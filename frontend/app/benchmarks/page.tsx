import Link from "next/link";
import { BenchmarkForm } from "@/components/benchmark-form";
import { PageHeader, Status } from "@/components/ui";
import { api, percent } from "@/lib/api";
import type { Benchmark } from "@/lib/types";

export default async function BenchmarksPage(){const benchmarks=await api<Benchmark[]>("/benchmarks");return <div className="page"><PageHeader eyebrow="Library" title="Benchmarks" description="Versioned task suites with explicit evaluator contracts and repeatable inputs." action={<BenchmarkForm/>}/><section className="card-grid">{benchmarks.map(item=><Link className="benchmark-card" href={`/benchmarks/${item.id}`} key={item.id}><div className="card-top"><div className="icon-tile">{item.name.slice(0,2).toUpperCase()}</div><Status value={item.status}/></div><div><span className="eyebrow">v{item.version} · {item.difficulty}</span><h2>{item.name}</h2><p>{item.description}</p></div><div className="tag-row">{item.tags.map(tag=><span key={tag}>{tag}</span>)}</div><dl className="card-stats"><div><dt>Tasks</dt><dd>{item.task_count}</dd></div><div><dt>Runs</dt><dd>{item.run_count}</dd></div><div><dt>Latest pass@k</dt><dd>{item.latest_pass_rate===null?"—":percent(item.latest_pass_rate)}</dd></div></dl></Link>)}</section></div>}
