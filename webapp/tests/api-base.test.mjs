import test from "node:test";
import assert from "node:assert/strict";

import {
  classifyApiPayload,
  resolveCandidateApiBases,
  resolvePrimaryApiBase,
} from "../src/lib/api-base.mjs";

test("resolvePrimaryApiBase prefers canonical env api base over app origin", () => {
  const base = resolvePrimaryApiBase({
    envBase: "https://api.pokrov.space/",
    origin: "https://app.pokrov.space",
    directApiBase: "https://api.pokrov.space",
  });

  assert.equal(base, "https://api.pokrov.space");
});

test("resolveCandidateApiBases keeps canonical api first when session is missing", () => {
  const bases = resolveCandidateApiBases({
    envBase: "",
    origin: "https://app.pokrov.space",
    directApiBase: "https://api.pokrov.space",
    hasSessionToken: false,
    enableLegacyPortFallback: false,
  });

  assert.deepEqual(bases, ["https://api.pokrov.space", "https://app.pokrov.space"]);
});

test("resolveCandidateApiBases keeps canonical api first when session exists", () => {
  const bases = resolveCandidateApiBases({
    envBase: "",
    origin: "https://app.pokrov.space",
    directApiBase: "https://api.pokrov.space",
    hasSessionToken: true,
    enableLegacyPortFallback: false,
  });

  assert.deepEqual(bases, ["https://api.pokrov.space", "https://app.pokrov.space"]);
});

test("classifyApiPayload rejects html masquerading as successful api response", () => {
  const kind = classifyApiPayload({
    bodyText: "<!DOCTYPE html><html><body>app shell</body></html>",
    contentType: "text/html; charset=utf-8",
  });

  assert.equal(kind, "html");
});

test("classifyApiPayload accepts json payloads", () => {
  const kind = classifyApiPayload({
    bodyText: '{"ok":true}',
    contentType: "application/json",
  });

  assert.equal(kind, "json");
});
