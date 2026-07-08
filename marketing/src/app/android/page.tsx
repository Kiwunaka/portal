import { SeoContentPage } from "../../components/seo/seo-content-page";
import { buildMarketingMetadata, MARKETING_CANONICAL_PATHS } from "../../lib/marketing-site";
import { getSeoPage } from "../../lib/seo-pages";

const seoPage = getSeoPage(MARKETING_CANONICAL_PATHS.android);

export const metadata = buildMarketingMetadata(seoPage.title, seoPage.description, {
  path: seoPage.path,
});

export default function AndroidSeoPage() {
  return <SeoContentPage page={seoPage} />;
}
