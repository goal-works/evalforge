import { RunComparison } from "@/components/run-comparison";
import { PageHeader } from "@/components/ui";
import { api } from "@/lib/api";
import type { Run } from "@/lib/types";

export default async function RunsPage(){const runs=await api<Run[]>("/runs");return <div className="page"><PageHeader eyebrow="Execution history" title="Evaluation runs" description="Compare agent behavior across benchmark versions, attempts, latency, and evaluator outcomes."/><RunComparison runs={runs}/></div>}
