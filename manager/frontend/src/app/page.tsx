"use client";

import { useQuery } from "@tanstack/react-query";
import { Sidebar } from "@/components/sidebar";
import {
  getDashboardMetrics,
  STATE_LABELS,
  STATE_COLORS,
  STATUS_LABELS,
  type DashboardMetrics,
} from "@/lib/api";

function MetricCard({
  title,
  value,
  sub,
  icon,
  accent,
}: {
  title: string;
  value: string | number;
  sub?: string;
  icon: string;
  accent: string;
}) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            {title}
          </p>
          <p className="mt-2 text-3xl font-bold text-slate-900">{value}</p>
          {sub && <p className="mt-1 text-xs text-slate-500">{sub}</p>}
        </div>
        <div className={`rounded-lg p-2.5 ${accent}`}>
          <span className="text-lg">{icon}</span>
        </div>
      </div>
    </section>
  );
}

function StateDistribution({ stateCounts }: { stateCounts: Record<string, number> }) {
  const total = Object.values(stateCounts).reduce((a, b) => a + b, 0);
  if (total === 0) return null;

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <h3 className="mb-4 text-sm font-semibold text-slate-900">敕令状态分布</h3>
      <div className="space-y-2">
        {Object.entries(stateCounts)
          .sort(([, a], [, b]) => b - a)
          .map(([state, count]) => {
            const pct = Math.round((count / total) * 100);
            const label = STATE_LABELS[state] || state;
            const color = STATE_COLORS[state] || "bg-gray-100 text-gray-800";
            return (
              <div key={state} className="flex items-center gap-3">
                <span className={`inline-block rounded px-2 py-0.5 text-xs font-medium ${color}`}>
                  {label}
                </span>
                <div className="flex-1">
                  <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                    <div
                      className="h-full rounded-full bg-slate-400 transition-all"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
                <span className="w-10 text-right text-xs font-medium text-slate-600">
                  {count}
                </span>
              </div>
            );
          })}
      </div>
    </section>
  );
}

function OrgDistribution({ orgCounts }: { orgCounts: Record<string, number> }) {
  if (Object.keys(orgCounts).length === 0) return null;

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <h3 className="mb-4 text-sm font-semibold text-slate-900">部门任务分布</h3>
      <div className="space-y-2">
        {Object.entries(orgCounts)
          .sort(([, a], [, b]) => b - a)
          .map(([org, count]) => (
            <div key={org} className="flex items-center justify-between rounded-lg bg-slate-50 px-3 py-2">
              <span className="text-sm text-slate-700">{org || "未分配"}</span>
              <span className="text-sm font-semibold text-slate-900">{count}</span>
            </div>
          ))}
      </div>
    </section>
  );
}

export default function DashboardPage() {
  const { data: metrics, isLoading, error } = useQuery({
    queryKey: ["dashboard-metrics"],
    queryFn: getDashboardMetrics,
    refetchInterval: 15_000,
  });

  return (
    <div className="flex h-screen">
      <Sidebar />
      <main className="flex-1 overflow-y-auto bg-slate-50 p-6">
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-slate-900">总览</h2>
          <p className="text-sm text-slate-500">帝王系统运行状态一览</p>
        </div>

        {error && (
          <div className="mb-4 rounded-lg border border-rose-300 bg-rose-50 p-3 text-sm text-rose-700">
            加载失败: {(error as Error).message}
          </div>
        )}

        {isLoading && !metrics ? (
          <div className="text-center text-slate-400 py-20">加载中...</div>
        ) : metrics ? (
          <>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
              <MetricCard
                title="在线官员"
                value={metrics.agents.online}
                sub={`共 ${metrics.agents.total} 位官员`}
                icon="🏛️"
                accent="bg-blue-50"
              />
              <MetricCard
                title="执行中敕令"
                value={metrics.tasks.active}
                sub={`共 ${metrics.tasks.total} 条敕令`}
                icon="📋"
                accent="bg-orange-50"
              />
              <MetricCard
                title="完成率"
                value={`${metrics.tasks.completion_rate}%`}
                sub={`${metrics.tasks.done} 条已完成`}
                icon="✅"
                accent="bg-emerald-50"
              />
              <MetricCard
                title="会话总数"
                value={metrics.sessions.total}
                sub={`${metrics.sessions.total_messages} 条消息`}
                icon="💬"
                accent="bg-purple-50"
              />
            </div>

            <div className="mt-6 grid grid-cols-1 gap-4 xl:grid-cols-2">
              <StateDistribution stateCounts={metrics.tasks.state_counts} />
              <OrgDistribution orgCounts={metrics.tasks.org_counts} />
            </div>

            <div className="mt-6 grid grid-cols-1 gap-4 xl:grid-cols-3">
              <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
                <h3 className="mb-3 text-sm font-semibold text-slate-900">系统健康</h3>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-500">官员在线率</span>
                    <span className="font-medium text-slate-900">
                      {metrics.agents.total > 0
                        ? `${Math.round((metrics.agents.online / metrics.agents.total) * 100)}%`
                        : "0%"}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-500">阻塞敕令</span>
                    <span className={`font-medium ${metrics.tasks.blocked > 0 ? "text-rose-600" : "text-emerald-600"}`}>
                      {metrics.tasks.blocked}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-500">待审查</span>
                    <span className="font-medium text-slate-900">
                      {metrics.tasks.review}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-500">审计记录</span>
                    <span className="font-medium text-slate-900">
                      {metrics.audit.total}
                    </span>
                  </div>
                </div>
              </section>

              <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm xl:col-span-2">
                <h3 className="mb-3 text-sm font-semibold text-slate-900">三省六部五监</h3>
                <div className="grid grid-cols-3 gap-3">
                  {[
                    { name: "中书省", desc: "取旨起草", icon: "📜" },
                    { name: "门下省", desc: "审议封驳", icon: "🔍" },
                    { name: "尚书省", desc: "调度派发", icon: "📤" },
                    { name: "六部", desc: "管理执行", icon: "🏢" },
                    { name: "五监", desc: "生产制造", icon: "🏗️" },
                  ].map((dept) => (
                    <div key={dept.name} className="rounded-lg bg-slate-50 px-3 py-2.5 text-center">
                      <span className="text-xl">{dept.icon}</span>
                      <p className="mt-1 text-sm font-medium text-slate-900">{dept.name}</p>
                      <p className="text-[11px] text-slate-500">{dept.desc}</p>
                      <p className="mt-1 text-xs font-semibold text-slate-700">
                        {metrics.tasks.org_counts[dept.name] || 0} 敕令
                      </p>
                    </div>
                  ))}
                </div>
              </section>
            </div>
          </>
        ) : null}
      </main>
    </div>
  );
}
