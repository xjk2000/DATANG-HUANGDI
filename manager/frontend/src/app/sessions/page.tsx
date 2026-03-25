"use client";

import { useQuery } from "@tanstack/react-query";
import { Sidebar } from "@/components/sidebar";
import { getSessions, getSessionSummary, type SessionRecord } from "@/lib/api";

export default function SessionsPage() {
  const { data: sessions, isLoading } = useQuery({
    queryKey: ["sessions"],
    queryFn: () => getSessions(),
    refetchInterval: 15_000,
  });

  const { data: summary } = useQuery({
    queryKey: ["session-summary"],
    queryFn: getSessionSummary,
    refetchInterval: 15_000,
  });

  return (
    <div className="flex h-screen">
      <Sidebar />
      <main className="flex-1 overflow-y-auto bg-slate-50 p-6">
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-slate-900">会话记录</h2>
          <p className="text-sm text-slate-500">
            共 {summary?.total_sessions ?? 0} 个会话 · {summary?.total_messages ?? 0} 条消息
          </p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-200 px-4 py-3">
            <div className="flex items-center gap-4 text-xs font-medium text-slate-500">
              <span className="w-32">Agent</span>
              <span className="flex-1">标题</span>
              <span className="w-16 text-center">消息</span>
              <span className="w-28 text-right">时间</span>
            </div>
          </div>

          {isLoading ? (
            <div className="py-12 text-center text-slate-400">加载中...</div>
          ) : sessions && sessions.length > 0 ? (
            sessions.map((s: SessionRecord) => (
              <div
                key={s.id}
                className="flex items-center gap-4 border-b border-slate-100 px-4 py-3 transition hover:bg-slate-50"
              >
                <span className="w-32 truncate text-sm font-medium text-slate-700">
                  {s.agent_id}
                </span>
                <span className="min-w-0 flex-1 truncate text-sm text-slate-600">
                  {s.title || "未命名会话"}
                </span>
                <span className="w-16 text-center text-xs text-slate-500">
                  {s.message_count}
                </span>
                <span className="w-28 text-right text-xs text-slate-400">
                  {new Date(s.updated_at).toLocaleString("zh-CN")}
                </span>
              </div>
            ))
          ) : (
            <div className="py-12 text-center text-slate-400">暂无会话记录</div>
          )}
        </div>
      </main>
    </div>
  );
}
