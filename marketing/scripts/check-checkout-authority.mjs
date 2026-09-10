import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const contract = JSON.parse(await readFile(new URL("../../shared/commercial-contract.json", import.meta.url), "utf8"));
const payButton = (page) => page.getByRole("button", { name: /^(Проверить заказ|Оплатить|Оплата (?:временно )?недоступна|Проверяем сумму)/ });

async function until(predicate, message, timeout = 10_000) {
  const deadline = Date.now() + timeout;
  while (Date.now() < deadline) {
    if (await predicate()) return;
    await new Promise((resolve) => setTimeout(resolve, 20));
  }
  throw new Error(message);
}

// Every API response is synthetic; no provider, account or production endpoint
// is contacted. Use the real catalog shape so projection guards remain active.
export async function checkCheckoutAuthority(browser, baseUrl, failures) {
  for (const scenario of ["invalid", "missing-token", "expiry", "input-race", "optional-acquisition", "read-timeout", "key-race", "mutation-retry", "quote-changed"]) {
    const context = await browser.newContext({ viewport: { width: 1180, height: 820 } });
    const page = await context.newPage();
    const held = new Map();
    const orders = [];
    const keyReads = [];
    let providerReads = 0;
    let quoteSequence = 0;
    let releaseProvider = false;
    const pageErrors = [];
    page.on("pageerror", (error) => pageErrors.push(error.message));
    const respond = (route, body) => route.fulfill({
      status: 200,
      contentType: "application/json",
      headers: { "X-Pokrov-Commercial-Revision": contract.commercial_revision },
      body: JSON.stringify(body),
    });
    const preview = (input, overrides = {}) => {
      const now = Date.now();
      const plan = contract.plans.find((item) => item.code === input.plan_code);
      return {
        ok: true, valid: true, reason_code: "ready", blocking_reasons: [],
        plan_code: input.plan_code, currency: "RUB", commercial_revision: contract.commercial_revision,
        base_price_rub: plan.amount_rub, final_price_rub: scenario === "expiry" ? Math.round(plan.amount_rub * 0.9) : plan.amount_rub,
        server_time: new Date(now).toISOString(),
        hold_expires_at: new Date(now + (scenario === "expiry" ? 3000 : 60_000)).toISOString(),
        offer_ends_at: new Date(now + 120_000).toISOString(),
        offer_token: scenario === "quote-changed" ? `synthetic-quote-${++quoteSequence}` : "synthetic-quote", terms_url: "/offer/", ...overrides,
      };
    };
    await page.route("**/api/**", async (route) => {
      const path = new URL(route.request().url()).pathname;
      if (path === "/api/public/catalog") {
        return respond(route, { ...contract, plans: contract.plans.map((plan) => ({ ...plan, days: plan.duration_days })) });
      }
      if (path === "/api/payments/providers") {
        providerReads += 1;
        if (scenario === "read-timeout" && !releaseProvider) {
          held.set("provider", route);
          return;
        }
        return respond(route, { ok: true, providers: [{ code: "lavatop", payment_methods: [
          { code: "sbp", label: "СБП", available: true }, { code: "card", label: "Карта", available: true },
        ] }] });
      }
      if (path.startsWith("/api/access-keys/status/")) {
        keyReads.push(path);
        if (path.endsWith("OLDKEY")) { held.set("key", route); return; }
        return route.fulfill({ status: 500, body: "SYNTHETIC_PRIVATE_PROVIDER_BODY" });
      }
      if (path === "/api/acquisition/handoffs") {
        if (scenario === "optional-acquisition") {
          held.set("acquisition", route);
          return;
        }
        return respond(route, { handle: "x".repeat(48), purpose: "checkout" });
      }
      if (path === "/api/payments/start-99-eligibility") return respond(route, { known: true, eligible: true });
      if (path === "/api/public/offers/preview") {
        const input = route.request().postDataJSON();
        if (scenario === "input-race" && ["OLD", "NEW"].includes(input.promo_code)) {
          held.set(input.promo_code, { route, input });
          return;
        }
        return respond(route, preview(input, scenario === "invalid"
          ? { valid: false, reason_code: "legal_blocked", final_price_rub: 0, offer_token: null }
          : scenario === "missing-token" ? { offer_token: null } : {}));
      }
      if (path === "/api/payments/orders/create-public") {
        orders.push(route.request().postDataJSON());
        if (scenario === "quote-changed" && orders.length === 1) return route.fulfill({ status: 409, contentType: "application/json", body: JSON.stringify({ detail: "checkout_quote_changed" }) });
        if (scenario === "mutation-retry" && orders.length === 1) return route.abort("connectionreset");
        return respond(route, { ok: true, order_id: "synthetic-order", status: "pending", payment_return_token: "synthetic-return" });
      }
      if (path === "/api/payments/orders/status") {
        return respond(route, { ok: true, state: "processing", reason_code: "payment_pending", surface: "marketing", provider: "lavatop", terminal: false, next_poll_seconds: 30 });
      }
      return respond(route, {});
    });

    try {
      const query = scenario === "optional-acquisition" ? "?checkout_ticket=synthetic&plan=1_month"
        : scenario === "expiry" ? "?plan=3_months&promo=EXPIRY" : "";
      await page.goto(`${baseUrl}/checkout/${query}`, { waitUntil: "domcontentloaded", timeout: 30_000 });
      assert.match(await page.title(), /POKROV/i);
      if (scenario !== "read-timeout") await payButton(page).waitFor({ timeout: scenario === "optional-acquisition" ? 1500 : 15_000 });
      if (["invalid", "missing-token"].includes(scenario)) {
        await page.getByRole("button", { name: "Проверить сумму", exact: true }).waitFor();
        assert.equal(await payButton(page).isEnabled(), false, "Invalid/tokenless preview enabled payment");
        assert.equal(await page.getByRole("button", { name: "Оплатить 1 ₽", exact: true }).count(), 0);
        assert.equal(orders.length, 0);
      } else if (scenario === "expiry") {
        await page.getByText("Есть промокод?", { exact: true }).click();
        await until(() => payButton(page).isEnabled(), "Fresh quote never enabled payment");
        await page.getByText("Промокод применён сервером.", { exact: true }).waitFor();
        await page.evaluate(() => {
          const originalNow = Date.now;
          Date.now = () => originalNow() - 86_400_000;
        });
        await until(async () => !(await payButton(page).isEnabled()), "Expired quote remained payable");
        await page.getByText("Срок подтверждённой суммы истёк. Проверьте условия ещё раз.", { exact: true }).waitFor();
        assert.equal(await page.getByText("Промокод применён сервером.", { exact: true }).count(), 0, "Expired quote still claims promo applied");
        assert.equal(await page.getByText(/^было .* ₽$/).count(), 0, "Expired quote still advertises a discount");
        assert.equal(orders.length, 0);
      } else if (scenario === "input-race") {
        await page.locator("#checkout-buyer-email").fill("synthetic@example.test");
        await until(() => payButton(page).isEnabled(), "Fresh quote never enabled payment");
        await page.getByText("Есть промокод?", { exact: true }).click();
        await page.locator("#checkout-promo-code").fill("OLD");
        assert.equal(await payButton(page).isEnabled(), false, "Debounce left a stale quote payable");
        await until(() => held.has("OLD"), "OLD preview was not requested");
        await page.locator("#checkout-promo-code").fill("NEW");
        assert.equal(await payButton(page).isEnabled(), false);
        await until(() => held.has("NEW"), "NEW preview was not requested");
        const fresh = held.get("NEW");
        await respond(fresh.route, preview(fresh.input, { final_price_rub: 79, offer_token: "synthetic-new" }));
        await until(() => payButton(page).isEnabled(), "Current response was not accepted");
        const stale = held.get("OLD");
        await respond(stale.route, preview(stale.input, { final_price_rub: 1, offer_token: "synthetic-old" })).catch(() => {});
        await payButton(page).evaluate((button) => { button.click(); button.click(); });
        await until(() => orders.length > 0, "Valid quote could not create an order");
        assert.equal(orders.length, 1, "Double click repeated order creation");
        assert.equal(orders[0].offer_token, "synthetic-new", "A stale response supplied order authority");
      } else if (scenario === "mutation-retry") {
        await page.locator("#checkout-buyer-email").fill("synthetic@example.test");
        await until(() => payButton(page).isEnabled(), "Fresh quote never enabled payment");
        await payButton(page).click();
        await page.getByText("Ответ не получен. Повторите попытку, чтобы проверить этот же заказ.", { exact: true }).waitFor();
        assert.equal(orders.length, 1, "Ambiguous POST was automatically repeated against another base");
        await payButton(page).click();
        await until(() => orders.length === 2, "Explicit retry did not send the same intent");
        assert.deepEqual(orders[1], orders[0], "Retry changed the accepted order intent");
        await page.getByText("Заказ уже создан. Проверяем его статус. Если деньги списались, не оплачивайте повторно.", { exact: true }).waitFor();
      } else if (scenario === "quote-changed") {
        await page.locator("#checkout-buyer-email").fill("synthetic@example.test");
        await until(() => payButton(page).isEnabled(), "Fresh quote never enabled payment");
        await payButton(page).click();
        await page.getByText("Расчёт изменился или истёк. Проверьте обновлённую сумму перед оплатой.", { exact: true }).waitFor();
        await until(() => payButton(page).isEnabled(), "Rejected quote was not refreshed");
        assert.equal(orders.length, 1, "Quote refresh automatically retried payment");
        await payButton(page).click();
        await until(() => orders.length === 2, "Fresh quote could not create an order");
        assert.notEqual(orders[1].offer_token, orders[0].offer_token, "Rejected intent retained the old quote");
      } else if (scenario === "read-timeout") {
        await until(() => held.has("provider"), "Provider read was not started");
        await page.waitForTimeout(8500);
        assert.equal(providerReads, 1, "Deadline restarted for another API base");
        assert.equal(await payButton(page).count(), 0);
        assert.equal(await page.locator('span[aria-disabled="true"]').filter({ hasText: "Оплата временно недоступна" }).count(), 1);
        releaseProvider = true;
        await page.getByRole("button", { name: "Проверить доступность оплаты", exact: true }).click();
        await until(() => payButton(page).isEnabled(), "Explicit read retry did not recover checkout");
      } else if (scenario === "key-race") {
        await page.locator("details").filter({ has: page.locator("#checkout-access-key") }).locator("summary").click();
        const key = page.locator("#checkout-access-key");
        await key.fill("OLDKEY");
        await until(() => held.has("key"), "Key read did not start");
        await key.fill("NEWKEY");
        await until(() => keyReads.some((path) => path.endsWith("NEWKEY")), "New key read did not start");
        await page.getByText("Не удалось проверить ключ. Попробуйте ещё раз.", { exact: true }).waitFor();
        await respond(held.get("key"), { key: "OLDKEY", valid: true, status: "active" }).catch(() => {});
        assert.equal(await key.inputValue(), "NEWKEY");
        assert.equal(await page.getByText("SYNTHETIC_PRIVATE_PROVIDER_BODY", { exact: false }).count(), 0);
      } else {
        assert.ok(held.has("acquisition"), "Acquisition request was not started");
        assert.equal(await page.getByText("Оплата временно недоступна", { exact: true }).count(), 0,
          "Optional acquisition delayed required catalog/provider state");
      }
      assert.deepEqual(pageErrors, [], "Checkout raised a page error");
    } catch (error) {
      failures.push(`checkout ${scenario}: ${error.message}`);
    } finally {
      await context.close();
    }
  }
}
