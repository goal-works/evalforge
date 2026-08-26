const API_URL = process.env.API_URL ?? "http://localhost:8000";

export async function api<T>(path: string): Promise<T> {
  const response = await fetch(`${API_URL}/api/v1${path}`, { cache: "no-store" });
  if (!response.ok) throw new Error(`EvalForge API returned ${response.status}`);
  return response.json() as Promise<T>;
}

export function percent(value: number): string {
  return new Intl.NumberFormat("en", { style: "percent", maximumFractionDigits: 1 }).format(value);
}

export function duration(milliseconds: number): string {
  if (milliseconds < 1000) return `${milliseconds}ms`;
  return `${(milliseconds / 1000).toFixed(1)}s`;
}
