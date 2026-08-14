export type ReleasePlatform = "android" | "windows";

export const RELEASE_ASSET_NAMES: Record<ReleasePlatform, string> = {
  android: "pokrov-android-arm64-v8a.apk",
  windows: "pokrov-windows-setup-x64.exe",
};

export function approvedReleaseAsset(value: string, filename: string): string {
  try {
    const url = new URL(value);
    const parts = url.pathname.split("/");
    if (
      url.protocol !== "https:" ||
      url.hostname !== "github.com" ||
      url.username ||
      url.password ||
      url.port ||
      url.search ||
      url.hash ||
      parts.length !== 7 ||
      parts.slice(1, 5).join("/") !== "Kiwunaka/pokrov/releases/download" ||
      !/^v[0-9A-Za-z][0-9A-Za-z._-]{0,63}$/.test(parts[5] || "") ||
      parts[6] !== filename
    ) {
      return "";
    }
    return url.toString();
  } catch {
    return "";
  }
}
