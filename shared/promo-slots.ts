import promoSlotsJson from "./promo-slots.json";

export type PromoSlotsCatalog = typeof promoSlotsJson;
export type PromoSlot = PromoSlotsCatalog["slots"][number];

export const promoSlotsCatalog: PromoSlotsCatalog = promoSlotsJson;

export function getPromoSlotsCatalog(): PromoSlotsCatalog {
  return promoSlotsCatalog;
}

export function getPromoSlotsForSurface(surface: string): PromoSlot[] {
  const normalized = String(surface || "").trim().toLowerCase();
  return promoSlotsCatalog.slots.filter((slot) => slot.surface === normalized);
}
