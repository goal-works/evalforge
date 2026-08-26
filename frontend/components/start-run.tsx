"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import type { Agent } from "@/lib/types";

export function StartRun({ benchmarkId, taskCount, agents }: { benchmarkId: string; taskCount: number; agents: Agent[] }) {
  const router = useRouter();
  const [agentId, setAgentId] = useState(agents[0]?.id ?? "");
  const [attempts, setAttempts] = useState(1);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  async function submit() {
    setPending(true); setError("");
    const response = await fetch("/api/v1/runs", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ benchmark_id: benchmarkId, agent_configuration_id: agentId, attempts }) });
    if (!response.ok) { setError("The evaluation could not be queued."); setPending(false); return; }
    const run = await response.json(); router.push(`/runs/${run.id}`); router.refresh();
  }
  return <div className="run-launcher"><label>Agent<select value={agentId} onChange={event => setAgentId(event.target.value)}>{agents.map(agent => <option value={agent.id} key={agent.id}>{agent.name} · {agent.model}</option>)}</select></label><label>Attempts<select value={attempts} onChange={event => setAttempts(Number(event.target.value))}>{[1,2,3,5].map(value => <option value={value} key={value}>{value}</option>)}</select></label><div className="execution-count"><span>Executions</span><strong>{taskCount * attempts}</strong></div><button className="primary-button" onClick={submit} disabled={pending || !agentId}>{pending ? "Queueing…" : "Start evaluation"}</button>{error && <p className="form-error">{error}</p>}</div>;
}
