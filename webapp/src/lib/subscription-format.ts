export type CompatibleSubscriptionFormat = "smart" | "happ";

export function subscriptionUrlForFormat(rawUrl: string, format: CompatibleSubscriptionFormat): string {
  const url = new URL(String(rawUrl || "").trim());
  if (url.protocol !== "https:") {
    throw new Error("subscription_url_protocol_invalid");
  }
  url.searchParams.set("format", format);
  return url.toString();
}
