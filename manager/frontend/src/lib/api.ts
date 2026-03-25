/**
 * 帝王系统 API 客户端
 */

const API_BASE = "/api/v1";

async function fetchAPI<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `API error: ${res.status}`);
  }
  return res.json();
}

// ─── Dashboard ───────────────────────────────────────────
export type DashboardMetrics = {
  agents: { total: number; online: number };
  tasks: {
    total: number;
    active: number;
    done: number;
    blocked: number;
    review: number;
    completion_rate: number;
    state_counts: Record<string, number>;
    org_counts: Record<string, number>;
  };
  sessions: { total: number; total_messages: number };
  audit: { total: number };
};

export const getDashboardMetrics = () =>
  fetchAPI<DashboardMetrics>("/dashboard/metrics");

// ─── Agents ──────────────────────────────────────────────
export type Agent = {
  id: string;
  name: string;
  group: string;
  role: string;
  status: string;
  session_count: number;
  model: string;
  workspace: string;
  last_activity_at: string | null;
  created_at: string;
  updated_at: string;
};

export const getAgents = () => fetchAPI<Agent[]>("/agents");
export const getAgent = (id: string) => fetchAPI<Agent>(`/agents/${id}`);

// ─── Tasks ───────────────────────────────────────────────
export type Task = {
  id: string;
  title: string;
  state: string;
  org: string;
  official: string;
  official_name: string;
  content: string;
  source: string;
  session_id: string | null;
  message_count: number;
  output: string;
  created_at: string;
  updated_at: string;
};

export type TaskSummary = {
  total: number;
  active: number;
  done: number;
  stateCounts: Record<string, number>;
  stateLabels: Record<string, string>;
  orgCounts: Record<string, number>;
};

export const getTasks = (params?: {
  state?: string;
  org?: string;
  limit?: number;
}) => {
  const qs = new URLSearchParams();
  if (params?.state) qs.set("state", params.state);
  if (params?.org) qs.set("org", params.org);
  if (params?.limit) qs.set("limit", String(params.limit));
  const q = qs.toString();
  return fetchAPI<Task[]>(`/tasks${q ? `?${q}` : ""}`);
};

export const getTaskSummary = () => fetchAPI<TaskSummary>("/tasks/summary");
export const getTask = (id: string) => fetchAPI<Task>(`/tasks/${id}`);
export const getTaskStates = () =>
  fetchAPI<{
    states: Record<string, string>;
    transitions: Record<string, string[]>;
  }>("/tasks/states");

export const createTask = (data: {
  id: string;
  title: string;
  state?: string;
  org?: string;
  official?: string;
  content?: string;
}) =>
  fetchAPI<Task>("/tasks", { method: "POST", body: JSON.stringify(data) });

export const changeTaskState = (taskId: string, state: string, detail = "") =>
  fetchAPI<Task>(`/tasks/${taskId}/state`, {
    method: "PUT",
    body: JSON.stringify({ state, detail }),
  });

// ─── Sessions ────────────────────────────────────────────
export type SessionRecord = {
  id: number;
  session_id: string;
  agent_id: string;
  title: string;
  message_count: number;
  created_at: string;
  updated_at: string;
};

export const getSessions = (agentId?: string) => {
  const q = agentId ? `?agent_id=${agentId}` : "";
  return fetchAPI<SessionRecord[]>(`/sessions${q}`);
};

export const getSessionSummary = () =>
  fetchAPI<{
    total_sessions: number;
    total_messages: number;
    agent_stats: Record<string, { session_count: number; message_count: number }>;
  }>("/sessions/summary");

// ─── Audit ───────────────────────────────────────────────
export type AuditLog = {
  id: number;
  action: string;
  task_id: string;
  agent_id: string;
  detail: string;
  old_state: string;
  new_state: string;
  created_at: string;
};

export const getAuditLogs = (params?: {
  task_id?: string;
  limit?: number;
}) => {
  const qs = new URLSearchParams();
  if (params?.task_id) qs.set("task_id", params.task_id);
  if (params?.limit) qs.set("limit", String(params.limit));
  const q = qs.toString();
  return fetchAPI<AuditLog[]>(`/audit${q ? `?${q}` : ""}`);
};

// ─── Sync ────────────────────────────────────────────────
export const triggerSync = () =>
  fetchAPI<{ status: string; result: unknown }>("/sync");

// ─── 常量 ────────────────────────────────────────────────
export const STATE_LABELS: Record<string, string> = {
  Imperial: "皇帝下旨",
  ZhongshuDraft: "中书起草",
  ZhongshuReview: "中书内审",
  MenxiaReview: "门下审议",
  Rejected: "门下封驳",
  Approved: "准奏通过",
  Dispatching: "尚书派发",
  Executing: "执行中",
  Review: "待审查",
  Done: "已完成",
  Cancelled: "已取消",
  Blocked: "阻塞",
};

export const STATE_COLORS: Record<string, string> = {
  Imperial: "bg-yellow-100 text-yellow-800",
  ZhongshuDraft: "bg-blue-100 text-blue-800",
  ZhongshuReview: "bg-blue-100 text-blue-800",
  MenxiaReview: "bg-purple-100 text-purple-800",
  Rejected: "bg-red-100 text-red-800",
  Approved: "bg-green-100 text-green-800",
  Dispatching: "bg-indigo-100 text-indigo-800",
  Executing: "bg-orange-100 text-orange-800",
  Review: "bg-purple-100 text-purple-800",
  Done: "bg-emerald-100 text-emerald-800",
  Cancelled: "bg-gray-100 text-gray-800",
  Blocked: "bg-rose-100 text-rose-800",
};

export const STATUS_COLORS: Record<string, string> = {
  alive: "bg-emerald-500",
  idle: "bg-yellow-500",
  inactive: "bg-gray-400",
  unknown: "bg-gray-300",
};

export const STATUS_LABELS: Record<string, string> = {
  alive: "活跃",
  idle: "空闲",
  inactive: "离线",
  unknown: "未知",
};
