import { OpsShell } from "@/components/shell";
import { OPS_SECTIONS, normalizeOpsSection } from "@/lib/sections";

export function generateStaticParams() {
  return OPS_SECTIONS.filter((item) => item.id !== "dashboard").map((item) => ({ section: item.id }));
}

export default async function SectionPage({ params }: { params: Promise<{ section: string }> }) {
  const { section } = await params;
  return <OpsShell section={normalizeOpsSection(section)} />;
}
