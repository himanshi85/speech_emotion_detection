export type EmotionScore = {
  emotion: string;
  label_id: number;
  probability: number;
};

export type BehavioralMetrics = {
  speaking_speed: {
    category: string;
    syllables_per_second: number;
    words_per_minute: number;
  };
  pause_frequency: {
    category: string;
    pauses_per_minute: number;
    silence_ratio: number;
  };
  vocal_energy: {
    category: string;
    rms_db: number;
  };
  pitch_variation: {
    category: string;
    mean_hz: number;
    std_hz: number;
  };
  overall_behaviour: string;
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
  behavior?: BehavioralMetrics;
};

export type ModelInfo = {
  key: string;
  display_name: string;
  input_type: string;
  architecture: string;
  checkpoint_available: boolean;
};

export type InputMode = "record" | "upload";
