import type { AnalysisReport, ModelInfo } from "@/types/analysis";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "http://127.0.0.1:8000";

export async function fetchModels(): Promise<ModelInfo[]> {
  const res = await fetch(`${API_BASE}/models`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error("Could not load models from the inference API.");
  }
  return res.json();
}

export async function analyzeAudio(
  modelKey: string,
  audio: Blob,
  filename: string,
): Promise<AnalysisReport> {
  const form = new FormData();
  form.append("model_key", modelKey);
  form.append("file", audio, filename);

  const res = await fetch(`${API_BASE}/predict`, {
    method: "POST",
    body: form,
  });

  if (!res.ok) {
    let detail = "Analysis failed.";
    try {
      const body = await res.json();
      if (body?.detail) {
        detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
      }
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }

  return res.json();
}

export async function checkApiHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/health`, { cache: "no-store" });
    return res.ok;
  } catch {
    return false;
  }
}

export { API_BASE };
