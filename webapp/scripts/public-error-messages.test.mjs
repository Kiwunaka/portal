import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import ts from "typescript";

const source = readFileSync(new URL("../src/lib/public-error-messages.ts", import.meta.url), "utf8");
const compiled = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
}).outputText;
const module = { exports: {} };
new Function("exports", "module", compiled)(module.exports, module);
const { userFacingErrorMessage } = module.exports;

test("keeps domain not-found and forbidden errors out of unrelated mappings", () => {
  assert.equal(
    userFacingErrorMessage(new Error("support_attachment_not_found"), "fallback"),
    "Вложение не найдено или уже удалено. Обновите обращение.",
  );
  assert.equal(
    userFacingErrorMessage(new Error("recovery_scope_forbidden"), "fallback"),
    "Это действие недоступно в режиме восстановления. Войдите в полный аккаунт.",
  );
});

test("does not echo FastAPI validation JSON even when input contains Cyrillic", () => {
  const raw = JSON.stringify({ detail: [{ type: "string_too_short", input: "СЕКРЕТНЫЙ-КОД" }] });
  const result = userFacingErrorMessage(new Error(raw), "Не удалось выполнить действие.");
  assert.equal(result, "Не удалось выполнить действие.");
  assert.doesNotMatch(result, /СЕКРЕТНЫЙ-КОД/);
});
