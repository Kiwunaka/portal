export const SUPPORT_ATTACHMENT_ACCEPT =
  "image/png,image/jpeg,image/webp,application/pdf,text/plain,.png,.jpg,.jpeg,.webp,.pdf,.txt";
export const SUPPORT_ATTACHMENT_MAX_BYTES = 20 * 1024 * 1024;

const MIME_BY_EXTENSION = new Map([
  [".png", "image/png"],
  [".jpg", "image/jpeg"],
  [".jpeg", "image/jpeg"],
  [".webp", "image/webp"],
  [".pdf", "application/pdf"],
  [".txt", "text/plain"],
]);

const STORED_NAME_RE = /^\d{8}-[A-Za-z0-9]{8,64}\.(?:png|jpg|jpeg|webp|pdf|txt)$/;
const PRIVATE_PREFIX = "/api/tickets/attachments/";
const RETIRED_PREFIX = "/uploads/support/";

export function normalizePrivateSupportAttachmentPath(value: string): string | null {
  const raw = String(value || "").trim();
  const storedName = raw.startsWith(PRIVATE_PREFIX)
    ? raw.slice(PRIVATE_PREFIX.length)
    : raw.startsWith(RETIRED_PREFIX)
      ? raw.slice(RETIRED_PREFIX.length)
      : "";
  return STORED_NAME_RE.test(storedName) ? `${PRIVATE_PREFIX}${storedName}` : null;
}

export async function validateSupportAttachment(file: File): Promise<void> {
  if (file.size > SUPPORT_ATTACHMENT_MAX_BYTES) {
    throw new Error("Размер файла не должен превышать 20 МиБ.");
  }
  const name = String(file.name || "").toLowerCase();
  const extension = Array.from(MIME_BY_EXTENSION.keys()).find((candidate) => name.endsWith(candidate));
  const expectedMime = extension ? MIME_BY_EXTENSION.get(extension) : null;
  if (!extension || String(file.type || "").toLowerCase() !== expectedMime) {
    throw new Error("Можно приложить PNG, JPEG, WebP, PDF или TXT.");
  }
  if (extension === ".txt") {
    try {
      new TextDecoder("utf-8", { fatal: true }).decode(await file.arrayBuffer());
    } catch {
      throw new Error("TXT-файл должен быть сохранён в UTF-8.");
    }
  }
}
