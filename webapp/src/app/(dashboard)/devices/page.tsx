"use client";

import { AnimatePresence, motion } from "framer-motion";
import Link from "next/link";
import { useMemo, useState } from "react";

type DeviceRow = {
  id: string;
  name: string;
  icon: string;
  os: string;
  ip: string;
  status: "online" | "offline";
  lastSeen: string;
};

const INITIAL: DeviceRow[] = [
  { id: "d1", name: "iPhone 15 Pro", icon: "smartphone", os: "iOS 17", ip: "192.168.1.42", status: "online", lastSeen: "СЃРµР№С‡Р°СЃ" },
  { id: "d2", name: "MacBook Air M2", icon: "laptop_mac", os: "macOS Sonoma", ip: "192.168.1.15", status: "online", lastSeen: "СЃРµР№С‡Р°СЃ" },
  { id: "d3", name: "Windows Workstation", icon: "desktop_windows", os: "Windows 11", ip: "192.168.1.109", status: "offline", lastSeen: "2 С‡Р°СЃР° РЅР°Р·Р°Рґ" },
];

const DEVICE_POOL: DeviceRow[] = [
  { id: "d4", name: "iPad Air", icon: "tablet_mac", os: "iPadOS 17", ip: "192.168.1.33", status: "online", lastSeen: "СЃРµР№С‡Р°СЃ" },
  { id: "d5", name: "Android Pixel", icon: "smartphone", os: "Android 15", ip: "192.168.1.36", status: "online", lastSeen: "1 РјРёРЅ РЅР°Р·Р°Рґ" },
  { id: "d6", name: "Linux Laptop", icon: "terminal", os: "Ubuntu 24.04", ip: "192.168.1.130", status: "offline", lastSeen: "РІС‡РµСЂР°" },
];

export default function DevicesPage() {
  const [devices, setDevices] = useState<DeviceRow[]>(INITIAL);
  const [toast, setToast] = useState<string | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const freeSlots = useMemo(() => Math.max(0, 5 - devices.length), [devices.length]);

  const popToast = (text: string): void => {
    setToast(text);
    window.setTimeout(() => setToast(null), 1800);
  };

  const remove = (id: string): void => {
    const removed = devices.find((item) => item.id === id);
    setDevices((prev) => prev.filter((item) => item.id !== id));
    popToast(removed ? `${removed.name} РѕС‚РєР»СЋС‡РµРЅРѕ.` : "РЈСЃС‚СЂРѕР№СЃС‚РІРѕ РѕС‚РєР»СЋС‡РµРЅРѕ.");
  };

  const addFromPool = (): void => {
    if (devices.length >= 5) {
      popToast("Р›РёРјРёС‚ РґРѕСЃС‚РёРіРЅСѓС‚. РћСЃРІРѕР±РѕРґРёС‚Рµ СЃР»РѕС‚ РїРµСЂРµРґ РґРѕР±Р°РІР»РµРЅРёРµРј.");
      return;
    }
    const used = new Set(devices.map((item) => item.id));
    const next = DEVICE_POOL.find((item) => !used.has(item.id));
    if (!next) {
      popToast("РќРѕРІС‹С… СѓСЃС‚СЂРѕР№СЃС‚РІ РґР»СЏ РґРµРјРѕ Р±РѕР»СЊС€Рµ РЅРµС‚.");
      return;
    }
    setDevices((prev) => [...prev, next]);
    popToast(`${next.name} РїРѕРґРєР»СЋС‡РµРЅРѕ.`);
  };

  const onGetKey = (): void => {
    addFromPool();
    setShowAddModal(false);
    window.open("https://t.me/portal_privacy_bot", "_blank", "noopener,noreferrer");
  };

  return (
    <main className="space-y-6">
      <section className="glass-card p-7">
        <p className="font-mono text-xs uppercase tracking-[0.18em] text-slate-500">devices</p>
        <h1 className="mt-2 font-display text-4xl font-bold">РњРѕРё СѓСЃС‚СЂРѕР№СЃС‚РІР°</h1>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
          РџРѕРґРєР»СЋС‡Р°Р№С‚Рµ СѓСЃС‚СЂРѕР№СЃС‚РІР° Рё СѓРїСЂР°РІР»СЏР№С‚Рµ СЃР»РѕС‚Р°РјРё РІ РѕРґРёРЅ РєР»РёРє Р±РµР· РїРѕРІС‚РѕСЂРЅРѕР№ РЅР°СЃС‚СЂРѕР№РєРё.
        </p>
        <div className="mt-5 inline-flex rounded-xl bg-white/75 px-4 py-2 text-sm dark:bg-white/10">Р›РёРјРёС‚: {devices.length} РёР· 5</div>
      </section>

      <section className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
        <AnimatePresence>
          {devices.map((device, idx) => (
            <motion.article
              key={device.id}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ delay: idx * 0.04 }}
              className="glass-card p-6"
            >
              <div className="mb-4 flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <span className="material-symbols-rounded rounded-xl bg-violet-100 p-2.5 text-violet-600 dark:bg-violet-900/35 dark:text-violet-200">
                    {device.icon}
                  </span>
                  <div>
                    <h2 className="font-semibold">{device.name}</h2>
                    <p className="text-xs text-slate-500">{device.os}</p>
                  </div>
                </div>
                <span className={`rounded-full px-2.5 py-1 text-[11px] uppercase tracking-[0.14em] ${device.status === "online" ? "bg-emerald-500 text-white" : "bg-slate-300 text-slate-700 dark:bg-slate-700 dark:text-slate-200"}`}>
                  {device.status === "online" ? "online" : "offline"}
                </span>
              </div>

              <div className="space-y-2 text-sm text-slate-600 dark:text-slate-300">
                <p>IP: {device.ip}</p>
                <p>РџРѕСЃР»РµРґРЅСЏСЏ Р°РєС‚РёРІРЅРѕСЃС‚СЊ: {device.lastSeen}</p>
              </div>

              <button
                type="button"
                onClick={() => remove(device.id)}
                className="outline-btn mt-5 w-full rounded-xl py-2.5 text-sm font-semibold uppercase tracking-[0.12em] text-rose-600 dark:text-rose-300"
              >
                РћС‚РєР»СЋС‡РёС‚СЊ
              </button>
            </motion.article>
          ))}
        </AnimatePresence>

        {freeSlots > 0 ? (
          <article className="glass-card grid place-items-center p-6 text-center">
            <div>
              <span className="material-symbols-rounded rounded-full bg-violet-100 p-3 text-3xl text-violet-600 dark:bg-violet-900/35 dark:text-violet-200">add</span>
              <h3 className="mt-4 font-display text-2xl font-semibold">РЎРІРѕР±РѕРґРЅС‹Р№ СЃР»РѕС‚</h3>
              <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">РћСЃС‚Р°Р»РѕСЃСЊ {freeSlots} СЃРІРѕР±РѕРґРЅС‹С… СЃР»РѕС‚Р° РґР»СЏ РЅРѕРІРѕРіРѕ СѓСЃС‚СЂРѕР№СЃС‚РІР°.</p>
              <button
                type="button"
                onClick={() => setShowAddModal(true)}
                className="btn-primary mt-5 rounded-xl px-6 py-2.5 text-sm font-semibold uppercase tracking-[0.12em]"
              >
                Р”РѕР±Р°РІРёС‚СЊ СѓСЃС‚СЂРѕР№СЃС‚РІРѕ
              </button>
            </div>
          </article>
        ) : null}
      </section>

      <AnimatePresence>
        {showAddModal ? (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[230] grid place-items-center bg-slate-900/60 p-4"
            onClick={() => setShowAddModal(false)}
          >
            <motion.div
              initial={{ opacity: 0, y: 26, scale: 0.96 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 26, scale: 0.96 }}
              className="glass-card w-full max-w-md p-6"
              onClick={(event) => event.stopPropagation()}
            >
              <div className="mb-5 text-center">
                <h2 className="font-display text-3xl font-semibold">РџРѕРґРєР»СЋС‡РёС‚СЊ СѓСЃС‚СЂРѕР№СЃС‚РІРѕ</h2>
                <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
                  РЎРєР°С‡Р°Р№С‚Рµ РїСЂРёР»РѕР¶РµРЅРёРµ PORTAL, РїРѕР»СѓС‡РёС‚Рµ РєР»СЋС‡ РІ Telegram Рё РІРѕР№РґРёС‚Рµ РІ РѕРґРёРЅ СЃС†РµРЅР°СЂРёР№.
                </p>
              </div>

              <div className="space-y-3">
                <div className="rounded-xl bg-white/70 p-3 text-sm dark:bg-white/10">
                  <strong className="mr-2">1</strong>
                  РЎРєР°С‡Р°Р№С‚Рµ РїСЂРёР»РѕР¶РµРЅРёРµ РґР»СЏ РІР°С€РµР№ РћРЎ
                </div>
                <div className="rounded-xl bg-white/70 p-3 text-sm dark:bg-white/10">
                  <strong className="mr-2">2</strong>
                  РџРµСЂРµР№РґРёС‚Рµ РІ Р±РѕС‚Р° @portal_privacy_bot РІ Telegram
                </div>
                <div className="rounded-xl bg-white/70 p-3 text-sm dark:bg-white/10">
                  <strong className="mr-2">3</strong>
                  РџРѕР»СѓС‡РёС‚Рµ РєР»СЋС‡ Рё РІСЃС‚Р°РІСЊС‚Рµ РІ РїСЂРёР»РѕР¶РµРЅРёРµ
                </div>
              </div>

              <div className="mt-5 flex items-center justify-between gap-3">
                <Link href="/dashboard/downloads" className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold">
                  РЎРєР°С‡Р°С‚СЊ РєР»РёРµРЅС‚
                </Link>
                <div className="flex gap-2">
                  <button type="button" onClick={() => setShowAddModal(false)} className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold">
                    РћС‚РјРµРЅР°
                  </button>
                  <button type="button" onClick={onGetKey} className="btn-primary rounded-xl px-4 py-2 text-sm font-semibold">
                    РџРѕР»СѓС‡РёС‚СЊ РєР»СЋС‡
                  </button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        ) : null}
      </AnimatePresence>

      <AnimatePresence>
        {toast ? (
          <motion.div
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 14 }}
            className="fixed bottom-24 left-1/2 z-[210] -translate-x-1/2 rounded-full bg-slate-900 px-4 py-2 text-xs text-white shadow-xl"
          >
            {toast}
          </motion.div>
        ) : null}
      </AnimatePresence>
    </main>
  );
}

