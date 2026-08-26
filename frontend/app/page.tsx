import Link from "next/link";
import { Metric, PageHeader, Status } from "@/components/ui";
import { api, percent } from "@/lib/api";
import type { Run } from "@/lib/types";

interface Dashboard { metrics: { total_runs: number; average_pass_rate: number; evaluated_tasks: number; active_benchmarks: number }; recent_runs: Run[] }

export default async function DashboardPage() {
  const data = await api<Dashboard>("/dashboard");
  return <div className="page"><PageHeader eyebrow="Overview" title="Evaluation command center" description="Track benchmark health, execution volume, and the runs that need inspection." action={<Link className="primary-button" href="/benchmarks">Start evaluation</Link>} />
    <section className="metric-grid"><Metric label="Total runs" value={data.metrics.total_runs} detail="Across all benchmarks"/><Metric label="Average pass@k" value={percent(data.metrics.average_pass_rate)} detail="Completed runs"/><Metric label="Evaluated executions" value={data.metrics.evaluated_tasks.toLocaleString()} detail="Tasks × attempts"/><Metric label="Active benchmarks" value={data.metrics.active_benchmarks} detail="Ready to run"/></section>
    <section className="panel"><div className="panel-title"><div><span className="eyebrow">Live history</span><h2>Recent runs</h2></div><Link href="/runs">View all</Link></div><div className="table-wrap"><table><thead><tr><th>Run</th><th>Status</th><th>Progress</th><th>Pass@k</th><th>Mean score</th></tr></thead><tbody>{data.recent_runs.map(run => <tr key={run.id}><td><Link className="run-id" href={`/runs/${run.id}`}>RUN-{run.id.slice(0, 7).toUpperCase()}</Link><small>{new Date(run.created_at).toLocaleString()}</small></td><td><Status value={run.status}/></td><td>{run.completed_tasks}/{run.total_tasks}</td><td>{percent(run.pass_at_k)}</td><td>{run.mean_score.toFixed(2)}</td></tr>)}</tbody></table></div></section>
    <section className="insight-grid"><article className="insight"><span className="eyebrow">Workflow</span><h2>Reproducible by design</h2><p>Benchmark versions, agent settings, attempts, execution events, and evaluator decisions stay connected to every run.</p></article><article className="insight accent"><span className="eyebrow">Demo mode</span><h2>No provider keys required</h2><p>Three deterministic mock profiles make failures and pass@k behavior inspectable on every machine.</p></article></section>
  </div>;
}
