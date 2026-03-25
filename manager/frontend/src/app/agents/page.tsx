"use client";

import { useQuery } from "@tanstack/react-query";
import { Sidebar } from "@/components/sidebar";
import { getAgents, STATUS_COLORS, STATUS_LABELS, type Agent } from "@/lib/api";

const GROUP_ORDER = ["中书省", "门下省", "尚书省", "六部", "五监"];

function AgentCard({ agent }: { agent: Agent }) {
  const statusColor = STATUS_COLORS[agent.status] || STATUS_COLORS.unknown;
  const statusLabel = STATUS_LABELS[agent.status] || "未知";
  const lastActive = agent.last_activity_at
    ? new Date(agent.last_activity_at).toLocaleString("zh-CN")
    : "无记录";

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm transition hover:shadow-md">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className={`h-2.5 w-2.5 rounded-full ${statusColor}`} />
          <div>
            <h4 className="text-sm font-semibold text-slate-900">{agent.name}</h4>
            <p className="text-xs text-slate-500">{agent.id}</p>
          </div>
        </div>
        <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-600">
          {statusLabel}
        </span>
      </div>
      <p className="mt-2 text-xs text-slate-600">{agent.role}</p>
      <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
        <div>
          <span className="text-slate-400">会话</span>
          <p className="font-medium text-slate-700">{agent.session_count}</p>
        </div>
        <div>
          <span className="text-slate-400">模型</span>
          <p className="font-medium text-slate-700 truncate">{agent.model || "默认"}</p>
        </div>
      </div>
      <p className="mt-2 text-[11px] text-slate-400">最后活跃: {lastActive}</p>
    </div>
  );
}

export default function AgentsPage() {
  const { data: agents, isLoading } = useQuery({
    queryKey: ["agents"],
    queryFn: getAgents,
    refetchInterval: 15_000,
  });

  const grouped = agents
    ? GROUP_ORDER.map((group) => ({
        group,
        agents: agents.filter((a) => a.group === group),
      })).filter((g) => g.agents.length > 0)
    : [];

  const online = agents?.filter((a) => a.status === "alive").length ?? 0;
  const total = agents?.length ?? 0;

  return (
    <div className="flex h-screen">
      <Sidebar />
      <main className="flex-1 overflow-y-auto bg-slate-50 p-6">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-slate-900">官员总览</h2>
            <p className="text-sm text-slate-500">三省六部五监 · {total} 位官员</p>
          </div>
          <div className="flex items-center gap-2 rounded-full bg-white px-4 py-2 text-sm shadow-sm">
            <span className="h-2 w-2 rounded-full bg-emerald-500" />
            <span className="text-slate-700">{online} 在线</span>
            <span className="text-slate-300">|</span>
            <span className="text-slate-500">{total} 总计</span>
          </div>
        </div>

        {isLoading ? (
          <div className="py-20 text-center text-slate-400">加载中...</div>
        ) : (
          <div className="space-y-8">
            {grouped.map(({ group, agents: groupAgents }) => (
              <section key={group}>
                <h3 className="mb-3 text-lg font-semibold text-slate-800">{group}</h3>
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                  {groupAgents.map((agent) => (
                    <AgentCard key={agent.id} agent={agent} />
                  ))}
                </div>
              </section>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
