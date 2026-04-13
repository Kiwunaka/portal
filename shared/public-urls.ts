import publicUrlsJson from "./public-urls.json";

export type PublicUrls = typeof publicUrlsJson;

export const publicUrls: PublicUrls = publicUrlsJson;

export function getPublicUrls(): PublicUrls {
  return publicUrls;
}
