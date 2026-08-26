"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import type { FormEvent } from "react";
import type { Task } from "@/lib/types";

const defaults: Record<string, object> = {
  exact_match: { expected: "" }, contains: { value: "" },
  json_schema: { schema: { type: "object", required: [], properties: {} } },
  deterministic_judge: { criteria: ["required phrase"], threshold: 0.7 },
};

export function TaskForm({ benchmarkId, task }: { benchmarkId: string; task?: Task }) {
  const router = useRouter();
  const [evaluatorType, setEvaluatorType] = useState(task?.evaluators[0]?.type ?? "exact_match");
  const [configuration, setConfiguration] = useState(JSON.stringify(task?.evaluators[0]?.configuration ?? defaults.exact_match, null, 2));
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError("");
    const data = new FormData(event.currentTarget);
    let input: object; let metadata: object; let evaluatorConfiguration: object;
    try { input = JSON.parse(String(data.get("input"))); metadata = JSON.parse(String(data.get("metadata"))); evaluatorConfiguration = JSON.parse(configuration); }
    catch { setError("Input, metadata, and evaluator configuration must be valid JSON."); return; }
    setPending(true);
    const body = { name:data.get("name"),slug:data.get("slug"),description:data.get("description"),instruction:data.get("instruction"),input,metadata,timeout_seconds:Number(data.get("timeout_seconds")),difficulty:data.get("difficulty"),evaluators:[{type:evaluatorType,name:data.get("evaluator_name"),configuration:evaluatorConfiguration,weight:Number(data.get("weight"))}] };
    const path = task ? `/api/v1/tasks/${task.id}` : `/api/v1/benchmarks/${benchmarkId}/tasks`;
    const response = await fetch(path,{method:task?"PUT":"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
    if(!response.ok){const result=await response.json();setError(result.detail?.[0]?.msg??result.detail??"Unable to save task.");setPending(false);return}
    router.push(`/benchmarks/${benchmarkId}`);router.refresh();
  }

  function changeType(value:string){setEvaluatorType(value);setConfiguration(JSON.stringify(defaults[value],null,2))}
  return <form className="editor-layout" onSubmit={submit}><div className="editor-main"><section className="form-section"><span className="eyebrow">General</span><div className="form-grid"><label>Name<input name="name" defaultValue={task?.name} required/></label><label>Slug<input name="slug" defaultValue={task?.slug} pattern="[a-z0-9]+(?:-[a-z0-9]+)*" required/></label></div><label>Description<textarea name="description" rows={2} defaultValue={task?.description}/></label></section><section className="form-section"><span className="eyebrow">Instruction</span><label>Task instruction<textarea name="instruction" rows={7} defaultValue={task?.instruction} required/></label></section><section className="form-section"><span className="eyebrow">Input</span><label>JSON input<textarea className="code-input" name="input" rows={8} defaultValue={JSON.stringify(task?.input??{},null,2)} required/></label></section><section className="form-section"><span className="eyebrow">Evaluation builder</span><div className="form-grid"><label>Evaluator type<select value={evaluatorType} onChange={event=>changeType(event.target.value)}><option value="exact_match">Exact Match</option><option value="contains">Contains</option><option value="json_schema">JSON Schema</option><option value="deterministic_judge">Deterministic Judge</option></select></label><label>Evaluator name<input name="evaluator_name" defaultValue={task?.evaluators[0]?.name??"Primary evaluator"} required/></label><label>Weight<input name="weight" type="number" min="0.01" step="0.01" defaultValue={task?.evaluators[0]?.weight??1} required/></label></div><label>Configuration JSON<textarea className="code-input" rows={9} value={configuration} onChange={event=>setConfiguration(event.target.value)} required/></label></section><section className="form-section"><span className="eyebrow">Advanced</span><div className="form-grid"><label>Difficulty<select name="difficulty" defaultValue={task?.difficulty??"Medium"}><option>Easy</option><option>Medium</option><option>Hard</option><option>Expert</option></select></label><label>Timeout seconds<input name="timeout_seconds" type="number" min="1" max="3600" defaultValue={task?.timeout_seconds??30}/></label></div><label>Metadata JSON<textarea className="code-input" name="metadata" rows={7} defaultValue={JSON.stringify(task?.metadata??{mock_success_output:"",mock_failure_output:""},null,2)} required/></label></section></div><aside className="editor-actions"><span className="eyebrow">Task editor</span><h2>{task?"Update task":"Create task"}</h2><p>Changes affect future runs only. Existing run evidence remains persisted.</p>{error&&<p className="form-error" role="alert">{error}</p>}<button className="primary-button" disabled={pending}>{pending?"Saving…":"Save task"}</button><button className="ghost-button" type="button" onClick={()=>router.back()}>Cancel</button></aside></form>;
}
