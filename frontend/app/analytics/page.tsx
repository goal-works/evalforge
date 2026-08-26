import { Metric, PageHeader } from "@/components/ui";
import { api, duration, percent } from "@/lib/api";
import type { Run } from "@/lib/types";

export default async function AnalyticsPage() {
  const runs = await api<Run[]>("/runs");
  const completed = runs.filter(run => run.status === "Completed");
  const max = Math.max(...completed.map(run => run.pass_at_k), 1);
  const failures = completed.reduce((sum, run) => sum + run.failed_tasks, 0);
  const executions = completed.reduce((sum, run) => sum + run.completed_tasks, 0);
  const latency = completed.reduce((sum, run) => sum + run.duration_ms, 0) / Math.max(executions, 1);
  return <div className="page"><PageHeader eyebrow="Performance intelligence" title="Analytics" description="Understand benchmark reliability, failure volume, and execution efficiency across completed runs."/><section className="metric-grid"><Metric label="Completed runs" value={completed.length}/><Metric label="Failure rate" value={percent(failures / Math.max(executions,1))}/><Metric label="Mean task latency" value={duration(Math.round(latency))}/><Metric label="Total tokens" value={completed.reduce((sum, run) => sum + run.total_tokens, 0).toLocaleString()}/></section><section className="panel"><div className="panel-title"><div><span className="eyebrow">Run comparison</span><h2>Pass@k by evaluation</h2></div></div><div className="bar-chart">{completed.map(run => <div className="bar-row" key={run.id}><div><strong>{run.benchmark_name}</strong><small>{run.agent_name}</small></div><div className="bar-track"><i style={{width: `${(run.pass_at_k/max)*100}%`}}/></div><span>{percent(run.pass_at_k)}</span></div>)}</div></section><section className="insight-grid"><article className="insight"><span className="eyebrow">Failure analysis</span><h2>{failures} failed executions</h2><p>Open a run to inspect evaluator reasons and assign a failure category to each unsuccessful attempt.</p></article><article className="insight accent"><span className="eyebrow">Cost</span><h2>$0.00 in demo mode</h2><p>The mock adapter records tokens and latency while keeping provider cost at zero.</p></article></section></div>;
}
