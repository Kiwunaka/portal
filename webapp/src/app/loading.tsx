"use client";

import { motion } from "framer-motion";

export default function Loading() {
  return (
    <div className="fixed inset-0 z-[200] flex items-center justify-center bg-white/55 backdrop-blur-md dark:bg-slate-950/55">
      <div className="glass-card px-8 py-7 text-center">
        <motion.div
          className="mx-auto mb-4 h-14 w-14 rounded-full border-4 border-emerald-200 border-t-emerald-600"
          animate={{ rotate: 360, scale: [1, 1.04, 1] }}
          transition={{ rotate: { duration: 1.2, repeat: Infinity, ease: "linear" }, scale: { duration: 1.4, repeat: Infinity } }}
        />
        <motion.p
          className="font-display text-sm uppercase tracking-[0.25em] text-emerald-700 dark:text-emerald-300"
          animate={{ opacity: [0.4, 1, 0.4] }}
          transition={{ duration: 1.3, repeat: Infinity }}
        >
          Подтягиваем ваш вход
        </motion.p>
        <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">POKROV VPN</p>
      </div>
    </div>
  );
}
