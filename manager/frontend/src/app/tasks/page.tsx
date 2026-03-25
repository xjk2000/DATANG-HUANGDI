"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Sidebar } from "@/components/sidebar";
import { getTasks, getTaskSummary, STATE_LABELS, STATE_COLORS, type Task } from "@/lib/api";

function StateBadge({ state }: { state: string }) {
  const color = STATE_COLORS[state] || "bg-gray-100 text-gray-800";
  const label = STATE_LABELS[state] || state;
  return (
    <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${color}`}>
      {label}
    </span>
  );
}

function TaskRow({ task }: { task: Task }) {
  return (
    <div className="flex items-center gap-4 border-b border-slate-100 px-4 py-3 transition hover:bg-slate-50">
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium text-slate-900">{task.title}</p>
        <p className="text-xs text-slate-500">
          {task.id} · {task.official_name || task.official} · {task.org}
        </p>
      </div>
      <StateBadge state={task.state} />
      <span className="w-20 text-right text-xs text-slate-400">
        {new Date(task.updated_at).toLocaleDateString("zh-CN")}
      </span>
    </div>
  );
}

export default function TasksPage() {
  const [stateFilter, setStateFilter] = useState<string>("");

  const { data: tasks, isLoading } = useQuery({
    queryKey: ["tasks", stateFilter],
    queryFn: () => getTasks({ state: stateFilter || undefined, limit: 200 }),
    refetchInterval: 15_000,
  });

  const { data: summary } = useQuery({
    queryKey: ["task-summary"],
    queryFn: getTaskSummary,
    refetchInterval: 15_000,
  });

  const states = Object.keys(STATE_LABELS);

  return (
    <div className="flex h-screen">
      <Sidebar />
      <main className="flex-1 overflow-y-auto bg-slate-50 p-6">
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-slate-900">敕令看板</h2>
          <p className="text-sm text-slate-500">
            共 {summary?.total ?? 0} 条敕令 · {summary?.active ?? 0} 执行中 · {summary?.done ?? 0} 已完成
          </p>
        </div>

        {/* 状态过滤 */}
        <div className="mb-4 flex flex-wrap gap-2">
          <button
            onClick={() => setStateFilter("")}
            className={`rounded-full px-3 py-1 text-xs font-medium transition ${
              stateFilter === ""
                ? "bg-slate-900 text-white"
                : "bg-white text-slate-600 hover:bg-slate-100"
            }`}
          >
            全部
          </button>
          {states.map((state) => {
            const count = summary?.stateCounts[state] ?? 0;
            if (count === 0 && stateFilter !== state) return null;
            return (
              <button
                key={state}
                onClick={() => setStateFilter(stateFilter === state ? "" : state)}
                className={`rounded-full px-3 py-1 text-xs font-medium transition ${
                  stateFilter === state
                    ? "bg-slate-900 text-white"
                    : "bg-white text-slate-600 hover:bg-slate-100"
                }`}
              >
                {STATE_LABELS[state]} ({count})
              </button>
            );
          })}
        </div>

        {/* 任务列表 */}
        <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-200 px-4 py-3">
            <div className="flex items-center gap-4 text-xs font-medium text-slate-500">
              <span className="flex-1">敕令</span>
              <span className="w-20">状态</span>
              <span className="w-20 text-right">更新时间</span>
            </div>
          </div>

          {isLoading ? (
            <div className="py-12 text-center text-slate-400">加载中...</div>
          ) : tasks && tasks.length > 0 ? (
            tasks.map((task) => <TaskRow key={task.id} task={task} />)
          ) : (
            <div className="py-12 text-center text-slate-400">
              {stateFilter ? `没有「${STATE_LABELS[stateFilter]}」状态的敕令` : "暂无敕令"}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
