/** Russian pluralization for the cabinet's user-facing counters. */
export function ruPlural(value: number, one: string, few: string, many: string): string {
  const mod10 = Math.abs(value) % 10;
  const mod100 = Math.abs(value) % 100;
  if (mod10 === 1 && mod100 !== 11) return one;
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) return few;
  return many;
}

export function formatDays(value: number): string {
  return `${value} ${ruPlural(value, "день", "дня", "дней")}`;
}

export function formatDevicesLimit(value: number): string {
  if (value === 1) return "1 устройство";
  return `до ${value} ${ruPlural(value, "устройства", "устройств", "устройств")}`;
}
