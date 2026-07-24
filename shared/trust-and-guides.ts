import catalog from "./trust-and-guides.json";

export type ResponsibilityRow = (typeof catalog.responsibility_map.rows)[number];
export type PrivacyField = (typeof catalog.privacy_fields)[number];
export type RouteTaxonomyRow = (typeof catalog.route_taxonomy)[number];
export type FallbackClient = (typeof catalog.fallback_clients)[number];
export type UserGuide = (typeof catalog.guides)[number];
export type UserGuideControl = {
  label: string;
  does: string;
  use_when: string;
};
export type UserGuideDetail = {
  last_verified: string;
  steps: readonly string[];
  failure_steps: readonly string[];
  recommended_setup?: readonly string[];
  controls?: readonly UserGuideControl[];
  warnings?: readonly string[];
};

export const TRUST_CATALOG_VERSION = catalog.version;
export const TRUST_CATALOG_LAST_VERIFIED = catalog.last_verified;
export const RESPONSIBILITY_MAP = catalog.responsibility_map;
export const PRIVACY_FIELDS = catalog.privacy_fields;
export const ROUTE_TAXONOMY = catalog.route_taxonomy;
export const FALLBACK_CLIENTS = catalog.fallback_clients;
export const USER_GUIDES = catalog.guides;
export const USER_GUIDE_DETAILS = catalog.guide_details as Record<
  string,
  UserGuideDetail
>;
export const GUIDE_VIDEO_PROGRAM = catalog.guide_video_program;
