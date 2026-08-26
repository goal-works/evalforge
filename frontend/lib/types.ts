export type RunStatus = "Queued" | "Running" | "Completed" | "Failed" | "Cancelled";

export interface Run {
  id: string;
  benchmark_id: string;
  agent_configuration_id: string;
  benchmark_name?: string;
  agent_name?: string;
  status: RunStatus;
  attempts: number;
  total_tasks: number;
  completed_tasks: number;
  passed_tasks: number;
  failed_tasks: number;
  mean_score: number;
  pass_at_k: number;
  total_tokens: number;
  estimated_cost: number;
  duration_ms: number;
  created_at: string;
}

export interface Benchmark {
  id: string;
  name: string;
  slug: string;
  description: string;
  version: string;
  status: string;
  difficulty: string;
  tags: string[];
  task_count: number;
  run_count: number;
  latest_pass_rate: number | null;
  tasks?: Task[];
  runs?: Run[];
}

export interface Task {
  id: string;
  benchmark_id: string;
  name: string;
  slug: string;
  description: string;
  instruction: string;
  input: Record<string, unknown>;
  metadata: Record<string, unknown>;
  timeout_seconds: number;
  difficulty: string;
  evaluators: Array<{ id: string; name: string; type: string; weight: number; configuration: Record<string, unknown> }>;
}

export interface Agent {
  id: string;
  name: string;
  provider: string;
  model: string;
  temperature: number;
  max_tokens: number;
  system_prompt: string;
  configuration: { quality?: number };
}

export interface TaskRun {
  id: string;
  task_name: string;
  status: RunStatus;
  attempt_number: number;
  input: unknown;
  output: unknown;
  score: number;
  passed: boolean;
  failure_category: string | null;
  duration_ms: number;
  input_tokens: number;
  output_tokens: number;
  events: Array<{ id: string; type: string; sequence: number; payload: unknown; timestamp: string }>;
  results: Array<{ id: string; score: number; passed: boolean; reason: string; metadata: unknown }>;
}

export interface RunDetail extends Run {
  benchmark_name: string;
  agent_name: string;
  task_runs: TaskRun[];
}
