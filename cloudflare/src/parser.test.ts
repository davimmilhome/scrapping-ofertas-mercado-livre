import assert from "node:assert/strict";
import test from "node:test";
import { listingIdentity, parseCards, parseMoney, ParseError } from "./parser.ts";

test("normaliza preços brasileiros extraídos em partes", () => {
  assert.equal(parseMoney("1.299", "90"), "1299.90");
});

test("preserva a identidade MLB e remove rastreamento da URL", () => {
  const result = listingIdentity("/up/MLB-123456?foo=tracking", "https://www.mercadolivre.com.br/ofertas");
  assert.equal(result.id, "MLB123456");
  assert.match(result.url, /item_id=MLB123456$/);
});

test("rejeita cartão sem identidade confiável", () => {
  assert.throws(
    () => parseCards([{ href: "/produto", title: "Produto", currentFraction: "10" }], 1, "https://example.com"),
    ParseError,
  );
});

test("converte cartões válidos e conta rejeições", () => {
  const result = parseCards([
    {
      href: "/MLB-987654-produto",
      title: "Produto",
      currentFraction: "99",
      currentCents: "90",
      previousFraction: "120",
      seller: "vendido por Loja",
    },
    { href: "/sem-id", title: "Inválido", currentFraction: "5" },
  ], 1, "https://www.mercadolivre.com.br/ofertas");
  assert.equal(result.offers[0]?.listingId, "MLB987654");
  assert.equal(result.offers[0]?.previousPrice, "120.00");
  assert.equal(result.rejected, 1);
});
