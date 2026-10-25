export type RawCard = {
  href: string;
  title: string;
  currentFraction: string;
  currentCents?: string;
  previousFraction?: string;
  previousCents?: string;
  seller?: string;
};

export type ParsedOffer = {
  listingId: string;
  title: string;
  url: string;
  price: string;
  previousPrice: string | null;
  seller: string | null;
  page: number;
};

export class ParseError extends Error {}

export function parseMoney(fraction: string, cents?: string): string {
  const normalizedFraction = fraction.replace(/\D/g, "") || "0";
  const normalizedCents = (cents ?? "00").replace(/\D/g, "").padStart(2, "0").slice(0, 2);
  if (BigInt(normalizedFraction) === 0n && BigInt(normalizedCents) === 0n) {
    throw new ParseError("Preço inválido.");
  }
  return `${normalizedFraction}.${normalizedCents}`;
}

export function listingIdentity(rawUrl: string, baseUrl: string): { id: string; url: string } {
  const url = new URL(rawUrl, baseUrl);
  if (!/^https?:$/.test(url.protocol) || !url.hostname) {
    throw new ParseError("Link de anúncio inválido.");
  }
  const candidate = [
    url.searchParams.get("item_id"),
    url.searchParams.get("wid"),
    url.pathname,
    url.hash,
  ].filter(Boolean).join(" ");
  const match = candidate.match(/MLB-?(\d+)/i);
  if (!match) throw new ParseError("Link sem identificador MLB; não é seguro deduplicar.");
  const id = `MLB${match[1]}`;
  const canonical = new URL(url.origin + url.pathname.replace(/\/$/, ""));
  canonical.searchParams.set("item_id", id);
  return { id, url: canonical.toString() };
}

export function parseCards(cards: RawCard[], page: number, baseUrl: string): {
  offers: ParsedOffer[];
  rejected: number;
} {
  const offers: ParsedOffer[] = [];
  let rejected = 0;
  for (const card of cards) {
    try {
      if (!card.href || !card.title || !card.currentFraction) {
        throw new ParseError("Título, link ou preço ausente.");
      }
      const identity = listingIdentity(card.href, baseUrl);
      offers.push({
        listingId: identity.id,
        title: card.title.trim(),
        url: identity.url,
        price: parseMoney(card.currentFraction, card.currentCents),
        previousPrice: card.previousFraction
          ? parseMoney(card.previousFraction, card.previousCents)
          : null,
        seller: card.seller?.replace(/^(por|vendido por)\s+/i, "").trim() || null,
        page,
      });
    } catch {
      rejected += 1;
    }
  }
  if (offers.length === 0) throw new ParseError("Nenhum cartão reconhecido ou válido.");
  return { offers, rejected };
}
