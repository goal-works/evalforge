"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

export function BenchmarkForm() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true); setError("");
    const data = new FormData(event.currentTarget);
    const response = await fetch("/api/v1/benchmarks", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: data.get("name"), slug: data.get("slug"), description: data.get("description"), version: data.get("version"), status: data.get("status"), difficulty: data.get("difficulty"), tags: String(data.get("tags") ?? "").split(",").map(value => value.trim()).filter(Boolean) }),
    });
    if (!response.ok) { const body = await response.json(); setError(body.detail?.[0]?.msg ?? body.detail ?? "Unable to create benchmark."); setPending(false); return; }
    const benchmark = await response.json(); router.push(`/benchmarks/${benchmark.id}`); router.refresh();
  }

  if (!open) return <button className="primary-button" onClick={() => setOpen(true)}>New benchmark</button>;
  return <div className="modal-backdrop" role="presentation"><section className="modal" role="dialog" aria-modal="true" aria-labelledby="benchmark-form-title"><div className="panel-title"><div><span className="eyebrow">New suite</span><h2 id="benchmark-form-title">Create benchmark</h2></div><button className="icon-button" aria-label="Close" onClick={() => setOpen(false)}>×</button></div><form className="form-stack" onSubmit={submit}><label>Name<input name="name" required minLength={2}/></label><label>Slug<input name="slug" required pattern="[a-z0-9]+(?:-[a-z0-9]+)*" placeholder="customer-support-v1"/></label><label>Description<textarea name="description" rows={3}/></label><div className="form-grid"><label>Version<input name="version" defaultValue="1.0.0" required/></label><label>Status<select name="status" defaultValue="Draft"><option>Draft</option><option>Active</option><option>Archived</option></select></label><label>Difficulty<select name="difficulty" defaultValue="Medium"><option>Easy</option><option>Medium</option><option>Hard</option><option>Expert</option></select></label><label>Tags<input name="tags" placeholder="reasoning, support"/></label></div>{error && <p className="form-error" role="alert">{error}</p>}<div className="form-actions"><button type="button" className="ghost-button" onClick={() => setOpen(false)}>Cancel</button><button className="primary-button" disabled={pending}>{pending ? "Creating…" : "Create benchmark"}</button></div></form></section></div>;
}
