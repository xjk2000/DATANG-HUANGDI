"use client";

import { useQuery } from "@tanstack/react-query";
import { Sidebar } from "@/components/sidebar";
import { getAuditLogs, STATE_LABELS, type AuditLog } from "@/lib/api";

const ACTION_LABELS: Record<string, string> = {
  create: "创建",
  state_change: "状态变更",
  flow: "流转",
  done: "完成",
  cancel: "取消",
};

const ACTION_COLORS: Record<string, string> = {
  create: "bg-blue-100 text-blue-800",
  state_change: "bg-amber-100 text-amber-800",
  flow: "bg-indigo-100 text-indigo-800",
  done: "bg-emerald-100 text-emerald-800",
  cancel: "bg-gray-100 text-gray-800",
};

export default function AuditPage() {
  const { data: logs, isLoading } = useQuery({
    queryKey: ["audit-logs"],
    queryFn: () => getAuditLogs({ limit: 100 }),
    refetchInterval: 15_000,
  });

  return (
    <div className="flex h-screen">
      <Sidebar />
      <main className="flex-1 overflow-y-auto bg-slate-50 p-6">
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-slate-900">审计日志</h2>
          <p className="text-sm text-slate-500">所有敕令状态变更的完整记录</p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-200 px-4 py-3">
            <div className="flex items-center gap-4 text-xs font-medium text-slate-500">
              <span className="w-24">时间</span>
              <span className="w-20">操作</span>
              <span className="w-32">敕令</span>
              <span className="w-40">状态变更</span>
              <span className="flex-1">详情</span>
            </div>
          </div>

          {isLoading ? (
            <div className="py-12 text-center text-slate-400">加载中...</div>
          ) : logs && logs.length > 0 ? (
            logs.map((log: AuditLog) => {
              const actionColor = ACTION_COLORS[log.action] || "bg-gray-100 text-gray-800";
              const actionLabel = ACTION_LABELS[log.action] || log.action;
              return (
                <div
                  key={log.id}
                  className="flex items-center gap-4 border-b border-slate-100 px-4 py-2.5 transition hover:bg-slate-50"
                >
                  <span className="w-24 text-xs text-slate-400">
                    {new Date(log.created_at).toLocaleString("zh-CN", {
                      month: "2-digit",
                      day: "2-digit",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </span>
                  <span className="w-20">
                    <span className={`inline-block rounded px-1.5 py-0.5 text-[11px] font-medium ${actionColor}`}>
                      {actionLabel}
                    </span>
                  </span>
                  <span className="w-32 truncate text-xs font-medium text-slate-700">
                    {log.task_id}
                  </span>
                  <span className="w-40 text-xs text-slate-600">
                    {log.old_state && log.new_state
                      ? `${STATE_LABELS[log.old_state] || log.old_state} → ${STATE_LABELS[log.new_state] || log.new_state}`
                      : log.new_state
                        ? STATE_LABELS[log.new_state] || log.new_state
                        : "—"}
                  </span>
                  <span className="min-w-0 flex-1 truncate text-xs text-slate-500">
                    {log.detail}
                  </span>
                </div>
              );
            })
          ) : (
            <div className="py-12 text-center text-slate-400">暂无审计日志</div>
          )}
        </div>
      </main>
    </div>
  );
}
