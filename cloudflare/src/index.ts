import puppeteer from "@cloudflare/puppeteer";
import { neon, type NeonQueryFunction } from "@neondatabase/serverless";
import type { RawCard } from "./parser";
import { parseCards } from "./parser";

const CARD_SELECTOR = ".promotion-item, .poly-card, .ui-search-result__wrapper";
const READY_SELECTOR =
  ".promotion-item .andes-money-amount__fraction, " +
  ".poly-card .poly-price__current .andes-money-amount__fraction, " +
  ".ui-search-result__wrapper .andes-money-amount__fraction";

type Env = {
  BROWSER: Fetcher;
  DATABASE_URL: string;
  MANUAL_TOKEN?: string;
  BASE_URL: string;
  PAGES?: string;
  PAGE_TIMEOUT_SECONDS?: string;
  MAX_RUNTIME_SECONDS?: string;
  REQUEST_DELAY_SECONDS?: string;
  RETRIES?: string;
  LOG_RETENTION_DAYS?: string;
  SCHEMA_BOOTSTRAP?: string;
};

type Summary = {
  runId: string;
  status: "succeeded" | "partial" | "failed" | "timed_out";
  pagesRequested: number;
  pagesOk: number;
  offersFound: number;
  rejectedCount: number;
  failuresCount: number;
  durationSeconds: number;
};

type Sql = NeonQueryFunction<false, false>;

function numberSetting(raw: string | undefined, fallback: number, min: number, max: number): number {
  const value = Number(raw ?? fallback);
  if (!Number.isFinite(value) || value < min || value > max) {
    throw new Error(`Configuração numérica fora do limite (${min}-${max}).`);
  }
  return value;
}

function config(env: Env) {
  return {
    pages: numberSetting(env.PAGES, 1, 1, 100),
    timeoutSeconds: numberSetting(env.PAGE_TIMEOUT_SECONDS, 20, 1, 300),
    maxRuntimeSeconds: numberSetting(env.MAX_RUNTIME_SECONDS, 300, 1, 300),
    delaySeconds: numberSetting(env.REQUEST_DELAY_SECONDS, 1, 0, 60),
    retries: numberSetting(env.RETRIES, 2, 0, 5),
    retentionDays: numberSetting(env.LOG_RETENTION_DAYS, 30, 1, 365),
  };
}

function safeError(error: unknown): string {
  const message = error instanceof Error ? error.message : String(error);
  return message.replace(/[\r\n]+/g, " ").slice(0, 1000);
}

function pageUrl(baseUrl: string, page: number): string {
  const url = new URL(baseUrl);
  if (page > 1) url.searchParams.set("page", String(page));
  return url.toString();
}

async function ensureSchema(sql: Sql): Promise<void> {
  await sql`CREATE TABLE IF NOT EXISTS offer_snapshots (
    id BIGSERIAL PRIMARY KEY,
    marketplace VARCHAR(64) NOT NULL,
    listing_id VARCHAR(64) NOT NULL,
    observed_on DATE NOT NULL,
    title VARCHAR(1024) NOT NULL,
    url VARCHAR(4096) NOT NULL,
    price NUMERIC(18, 2) NOT NULL,
    previous_price NUMERIC(18, 2),
    seller VARCHAR(1024),
    page INTEGER NOT NULL,
    collected_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT uq_offer_daily UNIQUE (marketplace, listing_id, observed_on)
  )`;
  await sql`CREATE TABLE IF NOT EXISTS collection_runs (
    run_id VARCHAR(32) PRIMARY KEY,
    status VARCHAR(16) NOT NULL,
    app_env VARCHAR(16) NOT NULL,
    runner VARCHAR(32) NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    finished_at TIMESTAMPTZ,
    duration_seconds NUMERIC(12, 3),
    max_duration_seconds NUMERIC(12, 3) NOT NULL,
    pages_requested INTEGER NOT NULL,
    pages_ok INTEGER NOT NULL DEFAULT 0,
    offers_found INTEGER NOT NULL DEFAULT 0,
    failures_count INTEGER NOT NULL DEFAULT 0,
    rejected_count INTEGER NOT NULL DEFAULT 0,
    error_summary VARCHAR(1000)
  )`;
}

async function pruneRuns(sql: Sql, retentionDays: number): Promise<void> {
  await sql`
    DELETE FROM collection_runs
    WHERE finished_at < NOW() - (${retentionDays} * INTERVAL '1 day')
       OR (finished_at IS NULL AND started_at < NOW() - (${retentionDays} * INTERVAL '1 day'))
  `;
  await sql`
    UPDATE collection_runs
    SET status = 'abandoned', finished_at = NOW()
    WHERE status = 'running' AND started_at < NOW() - INTERVAL '15 minutes'
  `;
}

async function saveOffers(
  sql: Sql,
  offers: ReturnType<typeof parseCards>["offers"],
  collectedAt: string,
): Promise<void> {
  const observedOn = collectedAt.slice(0, 10);
  for (const offer of offers) {
    await sql`
      INSERT INTO offer_snapshots
        (marketplace, listing_id, observed_on, title, url, price, previous_price,
         seller, page, collected_at)
      VALUES
        ('mercadolivre', ${offer.listingId}, ${observedOn}, ${offer.title}, ${offer.url},
         ${offer.price}, ${offer.previousPrice}, ${offer.seller}, ${offer.page}, ${collectedAt})
      ON CONFLICT (marketplace, listing_id, observed_on) DO UPDATE SET
        title = EXCLUDED.title,
        url = EXCLUDED.url,
        price = EXCLUDED.price,
        previous_price = EXCLUDED.previous_price,
        seller = EXCLUDED.seller,
        page = EXCLUDED.page,
        collected_at = EXCLUDED.collected_at
      WHERE EXCLUDED.collected_at >= offer_snapshots.collected_at
    `;
  }
}

type BrowserPage = Awaited<ReturnType<Awaited<ReturnType<typeof puppeteer.launch>>["newPage"]>>;

async function extractCards(page: BrowserPage): Promise<RawCard[]> {
  return page.$$eval(CARD_SELECTOR, (elements, selector) => {
    // The browser binding supplies the DOM objects at runtime, while the
    // Workers type package intentionally does not include the browser DOM lib.
    // Keep this boundary structural so the Worker build does not mix DOM and
    // Web Worker globals.
    type DomNode = {
      classList: { contains(className: string): boolean };
      closest(selectors: string): DomNode | null;
      href?: string;
      querySelector(selectors: string): DomNode | null;
      querySelectorAll(selectors: string): DomNode[];
      textContent?: string | null;
    };
    const nodes = elements as unknown as DomNode[];
    const cards = nodes.filter((element) => !element.querySelector(selector));
    type MoneyParts = { fraction?: string; cents?: string };
    const text = (root: DomNode, selectors: string): string | undefined =>
      root.querySelector(selectors)?.textContent?.replace(/\s+/g, " ").trim() || undefined;
    const money = (root: DomNode, selectors: string): MoneyParts => {
      const amount = root.querySelector(selectors);
      if (!amount) return {};
      return {
        fraction: text(amount, ".andes-money-amount__fraction"),
        cents: text(amount, ".andes-money-amount__cents"),
      };
    };
    return cards.map((card) => {
      const current = money(
        card,
        ".poly-price__current .andes-money-amount, " +
          ".andes-money-amount-combo__main-container .andes-money-amount",
      );
      const previous = money(card, "s.andes-money-amount, .andes-money-amount--previous");
      const link = card.querySelector(
        "a.poly-component__title, a.promotion-item__link-container, a.ui-search-link",
      );
      const title = text(
        card,
        ".poly-component__title, .promotion-item__title, .ui-search-item__title",
      );
      const fallbackCurrent =
        current.fraction
          ? undefined
          : Array.from(card.querySelectorAll(".andes-money-amount")).find(
              (amount) => !amount.closest("s") && !amount.classList.contains("andes-money-amount--previous"),
            );
      const fallback: MoneyParts = fallbackCurrent
        ? {
            fraction: text(fallbackCurrent, ".andes-money-amount__fraction"),
            cents: text(fallbackCurrent, ".andes-money-amount__cents"),
          }
        : {};
      return {
        href: link?.href ?? "",
        title: title ?? "",
        currentFraction: current.fraction ?? fallback.fraction ?? "",
        currentCents: current.cents ?? fallback.cents,
        previousFraction: previous.fraction,
        previousCents: previous.cents,
        seller: text(card, ".poly-component__seller, .promotion-item__seller"),
      } satisfies RawCard;
    });
  }, CARD_SELECTOR);
}

async function collectPage(
  browser: Awaited<ReturnType<typeof puppeteer.launch>>,
  url: string,
  timeoutSeconds: number,
): Promise<ReturnType<typeof parseCards>> {
  const page = await browser.newPage();
  try {
    await page.goto(url, { waitUntil: "domcontentloaded", timeout: timeoutSeconds * 1000 });
    await page.waitForSelector(READY_SELECTOR, { timeout: timeoutSeconds * 1000 });
    const cards = await extractCards(page);
    return parseCards(cards, Number(new URL(url).searchParams.get("page") ?? 1), url);
  } finally {
    await page.close();
  }
}

async function run(env: Env): Promise<Summary> {
  if (!env.DATABASE_URL || !env.BASE_URL) throw new Error("DATABASE_URL e BASE_URL são obrigatórios.");
  const baseUrl = new URL(env.BASE_URL);
  if (baseUrl.protocol !== "https:" || baseUrl.hostname !== "www.mercadolivre.com.br") {
    throw new Error("BASE_URL deve ser o endpoint HTTPS permitido do Mercado Livre.");
  }
  const settings = config(env);
  const startedAt = Date.now();
  const startedIso = new Date(startedAt).toISOString();
  const runId = crypto.randomUUID().replaceAll("-", "").slice(0, 32);
  const sql = neon(env.DATABASE_URL);
  if (env.SCHEMA_BOOTSTRAP === "true") await ensureSchema(sql);
  await pruneRuns(sql, settings.retentionDays);
  await sql`
    INSERT INTO collection_runs
      (run_id, status, app_env, runner, started_at, max_duration_seconds, pages_requested)
    VALUES
      (${runId}, 'running', 'production', 'cloudflare-browser', ${startedIso},
       ${settings.maxRuntimeSeconds}, ${settings.pages})
  `;

  let browser: Awaited<ReturnType<typeof puppeteer.launch>> | undefined;
  let pagesOk = 0;
  let offersFound = 0;
  let rejectedCount = 0;
  let failuresCount = 0;
  let timedOut = false;
  const errors: string[] = [];
  try {
    browser = await puppeteer.launch(env.BROWSER);
    for (let pageNumber = 1; pageNumber <= settings.pages; pageNumber += 1) {
      if (Date.now() - startedAt >= settings.maxRuntimeSeconds * 1000) {
        timedOut = true;
        break;
      }
      let parsed: ReturnType<typeof parseCards> | undefined;
      for (let attempt = 0; attempt <= settings.retries; attempt += 1) {
        try {
          parsed = await collectPage(browser, pageUrl(env.BASE_URL, pageNumber), settings.timeoutSeconds);
          break;
        } catch (error) {
          if (attempt === settings.retries) errors.push(`Página ${pageNumber}: ${safeError(error)}`);
        }
      }
      if (!parsed) {
        failuresCount += 1;
      } else {
        const collectedAt = new Date().toISOString();
        await saveOffers(sql, parsed.offers, collectedAt);
        pagesOk += 1;
        offersFound += parsed.offers.length;
        rejectedCount += parsed.rejected;
      }
      if (pageNumber < settings.pages && settings.delaySeconds > 0) {
        await new Promise((resolve) => setTimeout(resolve, settings.delaySeconds * 1000));
      }
    }
  } catch (error) {
    failuresCount += 1;
    errors.push(safeError(error));
  } finally {
    try {
      await browser?.close();
    } catch (error) {
      errors.push(`Encerramento do navegador: ${safeError(error)}`);
    }
  }

  const finishedAt = Date.now();
  const durationSeconds = (finishedAt - startedAt) / 1000;
  const status = timedOut ? "timed_out" : pagesOk === 0 ? "failed" : failuresCount ? "partial" : "succeeded";
  await sql`
    UPDATE collection_runs
    SET status = ${status}, finished_at = ${new Date(finishedAt).toISOString()},
        duration_seconds = ${durationSeconds}, pages_ok = ${pagesOk},
        offers_found = ${offersFound}, failures_count = ${failuresCount},
        rejected_count = ${rejectedCount}, error_summary = ${errors.join(" | ").slice(0, 1000) || null}
    WHERE run_id = ${runId}
  `;
  if (status === "failed") throw new Error(errors.join(" | ") || "Nenhuma página foi coletada.");
  return { runId, status, pagesRequested: settings.pages, pagesOk, offersFound, rejectedCount, failuresCount, durationSeconds };
}

export default {
  async scheduled(_controller: ScheduledController, env: Env): Promise<void> {
    try {
      const summary = await run(env);
      console.log(JSON.stringify({ event: "collection_finished", ...summary }));
    } catch (error) {
      console.error(JSON.stringify({ event: "collection_failed", error: safeError(error) }));
      throw new Error("collection_failed");
    }
  },

  async fetch(request: Request, env: Env): Promise<Response> {
    if (request.method !== "POST" || new URL(request.url).pathname !== "/run") {
      return new Response("Not found", { status: 404 });
    }
    const authorization = request.headers.get("authorization");
    if (!env.MANUAL_TOKEN || authorization !== `Bearer ${env.MANUAL_TOKEN}`) {
      return new Response("Unauthorized", { status: 401 });
    }
    try {
      return Response.json(await run(env));
    } catch (error) {
      console.error(JSON.stringify({ event: "collection_failed", error: safeError(error) }));
      return Response.json({ error: "collection_failed" }, { status: 502 });
    }
  },
} satisfies ExportedHandler<Env>;
