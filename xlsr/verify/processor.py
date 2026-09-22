"""HF processor verification runner."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List

from xlsr.core.constants import MODEL_NAME, SAMPLE_RATE
from xlsr.core.paths import DEFAULT_DATA_DIR, DEFAULT_OUTPUT_DIR
from xlsr.data.audio import load_raw_waveform
from xlsr.data.dataset import load_ravdess_splits
from xlsr.model.processor import (
    encode_audio_file,
    get_xlsr_processor,
    summarize_model_inputs,
    waveforms_to_model_inputs,
)
from xlsr.training.experiment import create_experiment_dirs

logger = logging.getLogger(__name__)


def run_processor_verification(
    data_dir: Path | str | None = None,
    output_dir: Path | str | None = None,
    *,
    num_samples: int = 4,
    stop_on_failure: bool = True,
) -> Dict[str, Any]:
    data_root = Path(data_dir) if data_dir is not None else DEFAULT_DATA_DIR
    out_root = Path(output_dir) if output_dir is not None else DEFAULT_OUTPUT_DIR
    exp = create_experiment_dirs(out_root)

    issues: List[str] = []
    details: List[str] = []

    try:
        processor = get_xlsr_processor()
        details.append(f"model_name: {processor.model_name}")
        details.append(f"sampling_rate: {processor.sampling_rate}")
        details.append(
            f"feature_extractor_class: {processor.feature_extractor.__class__.__name__}"
        )
    except Exception as exc:  # noqa: BLE001
        issues.append(f"Failed to load processor: {exc}")
        processor = None

    encoded_summary = None
    batch_summary = None
    if processor is not None:
        bundle = load_ravdess_splits(data_root)
        paths = [
            Path(p)
            for p in bundle.train["abs_filepath"].head(num_samples).tolist()
        ]
        try:
            single = encode_audio_file(processor, paths[0])
            encoded_summary = summarize_model_inputs(single)
            details.append(f"single_file: {paths[0].name}")
            details.append(f"single_inputs: {encoded_summary}")

            raws = [load_raw_waveform(p) for p in paths]
            batch = waveforms_to_model_inputs(processor, raws, padding=True)
            batch_summary = summarize_model_inputs(batch)
            details.append(f"batch_size: {len(raws)}")
            details.append(f"batch_inputs: {batch_summary}")

            if "input_values" not in single:
                issues.append("Processor output missing input_values")
            if "attention_mask" not in single:
                issues.append("Processor output missing attention_mask")
        except Exception as exc:  # noqa: BLE001
            issues.append(f"Failed to encode waveforms: {exc}")

    ok = len(issues) == 0
    lines = [
        "Hugging Face Processor Verification (Section 6)",
        "=" * 60,
        f"Status: {'PASSED' if ok else 'FAILED'}",
        f"Model: {MODEL_NAME}",
        f"Required sampling_rate: {SAMPLE_RATE}",
        "",
        "API:",
        '  AutoFeatureExtractor.from_pretrained("facebook/wav2vec2-xls-r-300m")',
        "",
        "Details:",
    ]
    for d in details:
        lines.append(f"  {d}")
    if issues:
        lines.append("")
        lines.append("Issues:")
        for i in issues:
            lines.append(f"  - {i}")
    else:
        lines.append("")
        lines.append("Processor converts raw waveforms to input_values (+ attention_mask).")

    report_path = exp["metrics"] / "processor_verification.txt"
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("Processor report written: %s", report_path)

    result = {
        "ok": ok,
        "issues": issues,
        "single": encoded_summary,
        "batch": batch_summary,
        "report_path": str(report_path),
    }
    if stop_on_failure and not ok:
        raise RuntimeError(
            "HF PROCESSOR VERIFICATION FAILED — stopping.\n"
            + "\n".join(f"  - {i}" for i in issues)
        )
    return result
