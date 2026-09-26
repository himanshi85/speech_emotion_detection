export type EmotionScore = {
  emotion: string;
  label_id: number;
  probability: number;
};

export type AnalysisReport = {
  model_key: string;
  display_name: string;
  predicted_emotion: string;
  predicted_label_id: number;
  confidence: number;
  probabilities: EmotionScore[];
  inference_time_sec: number;
  audio_duration_sec: number;
  sample_rate: number;
  summary: string;
};

export type ModelInfo = {
  key: string;
  display_name: string;
  input_type: string;
  architecture: string;
  checkpoint_available: boolean;
};

export type InputMode = "record" | "upload";
