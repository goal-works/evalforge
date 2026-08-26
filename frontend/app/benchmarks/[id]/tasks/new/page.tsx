import { TaskForm } from "@/components/task-form";
import { PageHeader } from "@/components/ui";

export default async function NewTaskPage({params}:{params:Promise<{id:string}>}){const {id}=await params;return <div className="page"><PageHeader eyebrow="Benchmark task" title="Create task" description="Define the instruction, input, evaluator contract, and deterministic demo output."/><TaskForm benchmarkId={id}/></div>}
