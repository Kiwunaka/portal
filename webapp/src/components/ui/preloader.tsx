"use client";

import { motion, AnimatePresence } from "framer-motion";
import { useEffect, useState } from "react";

export function Preloader() {
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setLoading(false);
    }, 1800);
    return () => clearTimeout(timer);
  }, []);

  return (
    <AnimatePresence>
      {loading && (
        <motion.div
          initial={{ y: 0 }}
          exit={{ y: "-100%", transition: { duration: 0.8, ease: [0.32, 0.72, 0, 1] } }}
          className="fixed inset-0 z-[9999] flex flex-col items-center justify-center gap-8 bg-[#fbfaf7] dark:bg-[#0f1714]"
        >
          <motion.div
            initial={{ scale: 0.8, opacity: 0, rotate: -45 }}
            animate={{ scale: 1, opacity: 1, rotate: 0 }}
            transition={{ duration: 0.8, ease: "easeOut" }}
            className="flex h-16 w-16 items-center justify-center rounded-2xl bg-[color:var(--atlas-surface)] shadow-[0_24px_80px_-24px_rgba(20,103,79,0.3)] ring-1 ring-emerald-900/5 dark:bg-white/[0.04] dark:ring-white/10"
          >
            <div className="text-2xl text-[color:var(--atlas-status-success-text)] dark:text-emerald-400">P</div>
          </motion.div>

          <div className="flex flex-col items-center gap-3">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.3 }}
              className="font-mono text-xs font-semibold uppercase tracking-[0.3em] text-[color:var(--atlas-text-soft)]"
            >
              Инициализация кабинета
            </motion.div>

            <div className="h-1 w-48 overflow-hidden rounded-full bg-[color:var(--atlas-border)] dark:bg-white/5">
              <motion.div
                initial={{ width: "0%" }}
                animate={{ width: "100%" }}
                transition={{ duration: 1.4, ease: [0.32, 0.72, 0, 1] }}
                className="h-full rounded-full bg-emerald-700 dark:bg-emerald-400"
              />
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
