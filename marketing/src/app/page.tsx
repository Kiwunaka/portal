import MarketingLanding, { buildMarketingMetadata } from "../components/marketing-landing";

export const metadata = buildMarketingMetadata(undefined, undefined, {
  path: "/",
  keywords: ["pokrov", "android", "windows", "managed premium", "activation key", "all except ru"],
});

export default function HomePage() {
  return <MarketingLanding pagePath="/" />;
}
