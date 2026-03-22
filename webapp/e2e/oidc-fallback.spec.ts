import { expect, test } from "@playwright/test";

test("falls back to the canonical API when app origin returns HTML for OIDC start", async ({ page }) => {
  await page.route("**/api/auth/telegram/oidc/start", async (route) => {
    const url = new URL(route.request().url());
    if (url.hostname === "api.pokrov.space") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          ok: true,
          mode: "oidc",
          auth_url: "https://example.com/auth?from=oidc-fallback",
          redirect_uri: "https://app.pokrov.space/",
        }),
      });
      return;
    }

    await route.fulfill({
      status: 200,
      contentType: "text/html",
      body: "<!doctype html><html><body>app html shell</body></html>",
    });
  });

  await page.goto("/", { waitUntil: "domcontentloaded" });
  await page.getByRole("button", { name: /продолжить через telegram/i }).click();
  await page.waitForURL("https://example.com/auth?from=oidc-fallback");
});
