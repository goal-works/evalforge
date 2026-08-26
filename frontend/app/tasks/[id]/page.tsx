import { notFound } from "next/navigation";
import { TaskForm } from "@/components/task-form";
import { PageHeader } from "@/components/ui";
import { api } from "@/lib/api";
import type { Task } from "@/lib/types";

export default async function EditTaskPage({params}:{params:Promise<{id:string}>}){const {id}=await params;let task:Task;try{task=await api<Task>(`/tasks/${id}`)}catch{notFound()}return <div className="page"><PageHeader eyebrow="Benchmark task" title={`Edit ${task.name}`} description="Update future evaluation behavior without rewriting historical run evidence."/><TaskForm benchmarkId={task.benchmark_id} task={task}/></div>}
