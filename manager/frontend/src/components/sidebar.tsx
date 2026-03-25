"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/", label: "总览", icon: "📊" },
  { href: "/agents", label: "官员总览", icon: "🏛️" },
  { href: "/tasks", label: "敕令看板", icon: "📋" },
  { href: "/sessions", label: "会话记录", icon: "💬" },
  { href: "/audit", label: "审计日志", icon: "📖" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex h-screen w-60 flex-col border-r border-slate-200 bg-white">
      <div className="border-b border-slate-200 px-5 py-4">
        <h1 className="text-lg font-bold text-slate-900">⚔️ 帝王系统</h1>
        <p className="text-xs text-slate-500">三省六部五监 · 管理后台</p>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-4">
        {NAV_ITEMS.map((item) => {
          const isActive =
            item.href === "/"
              ? pathname === "/"
              : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition ${
                isActive
                  ? "bg-slate-100 text-slate-900"
                  : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
              }`}
            >
              <span className="text-base">{item.icon}</span>
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-slate-200 px-5 py-3">
        <p className="text-[11px] text-slate-400">大唐皇帝 v1.0</p>
      </div>
    </aside>
  );
}
