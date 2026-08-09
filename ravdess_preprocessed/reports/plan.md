# Wav2Vec2-XLS-R-300M — RAVDESS SER Model Implementation Prompt

I am building a Speech Emotion Recognition (SER) research project using the preprocessed **RAVDESS** dataset.

The dataset preprocessing has already been completed separately.

Now implement **ONLY the first deep-learning model:**

```text
facebook/wav2vec2-xls-r-300m
```

from Hugging Face.

The objective is to fine-tune Wav2Vec2-XLS-R-300M for **8-class Speech Emotion Recognition**.

Do not modify the preprocessing pipeline or create another dataset preprocessing pipeline unless absolutely required to load the existing processed data.

---

## 1. Model

Use exactly:

```text
facebook/wav2vec2-xls-r-300m
```

from Hugging Face Transformers.

Do NOT substitute:

- wav2vec2-base
- wav2vec2-large
- wav2vec2-large-xlsr-53
- HuBERT
- WavLM
- Whisper
- emotion2vec
- BEATs

This experiment is specifically for:

```text
Wav2Vec2-XLS-R-300M
```

---

## 2. Existing Dataset

Use the already-preprocessed RAVDESS dataset.

Expected structure:

```text
ravdess_preprocessed/
│
├── audio/
│   ├── Actor_01/
│   ├── Actor_02/
│   ├── ...
│   └── Actor_24/
│
├── metadata/
│   ├── ravdess_metadata.csv
│   ├── train.csv
│   ├── validation.csv
│   └── test.csv
│
├── reports/
└── logs/
```

Use:

```text
metadata/train.csv
metadata/validation.csv
metadata/test.csv
```

Do not create a new random train/validation/test split.

The existing actor-independent split must be preserved.

---

## 3. Dataset Split

The preprocessing pipeline created an actor-independent split.

Use it exactly:

```text
Train:
Actors 01–16

Validation:
Actors 17–20

Test:
Actors 21–24
```

Never move actors between splits.

Before training, verify:

```text
Train actors ∩ Validation actors = empty
Train actors ∩ Test actors = empty
Validation actors ∩ Test actors = empty
```

If leakage is detected, stop execution and report the problem.

---

## 4. Emotion Classes

There are exactly 8 classes.

Use this mapping:

```python
EMOTION_TO_ID = {
    "neutral": 0,
    "calm": 1,
    "happy": 2,
    "sad": 3,
    "angry": 4,
    "fearful": 5,
    "disgust": 6,
    "surprised": 7
}
```

And:

```python
ID_TO_EMOTION = {
    0: "neutral",
    1: "calm",
    2: "happy",
    3: "sad",
    4: "angry",
    5: "fearful",
    6: "disgust",
    7: "surprised"
}
```

The model must output:

```text
8 logits
```

---

## 5. Audio Input

The preprocessing pipeline already converted audio to:

```text
Mono
16,000 Hz
WAV
```

Use the audio files from the processed dataset.

Before passing audio to the model, verify:

```text
sampling_rate = 16000
channels = 1
```

Do not introduce additional model-specific audio transformations.

Do not use:

- MFCC
- Mel spectrogram
- handcrafted acoustic features
- pitch features
- energy features

The model must receive the raw waveform.

---

## 6. Hugging Face Processor

Use the appropriate Hugging Face processor/feature extractor for:

```text
facebook/wav2vec2-xls-r-300m
```

Prefer:

```python
AutoFeatureExtractor.from_pretrained(
    "facebook/wav2vec2-xls-r-300m"
)
```

or the appropriate current Hugging Face API if required by the installed Transformers version.

The processor must convert the waveform into model input.

Sampling rate:

```text
16000 Hz
```

---

## 7. Model Architecture

Implement the SER model using the pretrained XLS-R encoder plus a classification head.

Architecture:

```text
Raw Audio
    │
    ▼
16 kHz Waveform
    │
    ▼
Wav2Vec2 Feature Extractor
    │
    ▼
Wav2Vec2-XLS-R-300M
    │
    ▼
Last Hidden States
    │
    ▼
Masked Mean Pooling
    │
    ▼
Dropout
    │
    ▼
Linear Classification Head
    │
    ▼
8 Emotion Logits
```

Use:

```text
Wav2Vec2Model
```

for the encoder and add a custom classification head.

Do not use an ASR/CTC head.

This is an **emotion classification task**, not speech recognition.

---

## 8. Pooling

Use masked mean pooling over the temporal dimension.

Conceptually:

```python
hidden_states = outputs.last_hidden_state

pooled = masked_mean(
    hidden_states,
    attention_mask
)
```

The pooling must correctly account for padded audio.

Do not simply average padded values.

---

## 9. Classification Head

Use a simple classification head:

```text
Linear(hidden_size → 8)
```

with dropout before the classifier.

Recommended:

```python
dropout = 0.3
```

Keep the classification head simple because the purpose of this experiment is to evaluate the pretrained XLS-R representation.

---

## 10. Fine-Tuning Strategy

Implement two configurable modes:

### Mode A — Frozen Encoder

Freeze XLS-R parameters:

```python
for param in model.encoder.parameters():
    param.requires_grad = False
```

Train only the classification head.

### Mode B — Full Fine-Tuning

Unfreeze the complete XLS-R encoder and classification head.

The default experiment should be:

```text
Full fine-tuning
```

because this is the main SER experiment.

Make freezing configurable through the configuration file/command line.

For example:

```text
--freeze_encoder
```

should enable frozen-encoder training.

Without this argument:

```text
full fine-tuning
```

should be used.

---

## 11. Optimizer

Use:

```text
AdamW
```

Do not use deprecated imports such as:

```python
from transformers import AdamW
```

Use the current supported PyTorch/Transformers approach.

Use different learning rates if appropriate:

```text
Encoder learning rate:
1e-5

Classification head:
1e-4
```

Make these configurable.

Example:

```text
--encoder_lr
--classifier_lr
```

Do not hard-code them throughout the code.

---

## 12. Loss Function

Use:

```text
CrossEntropyLoss
```

as the default.

Initially do not use:

- focal loss
- label smoothing
- SMOTE
- oversampling
- undersampling

Keep the baseline experiment simple and reproducible.

Make class-weighted loss optional, but do not enable it by default.

---

## 13. Variable-Length Audio

RAVDESS clips may have different durations.

The DataLoader must support variable-length audio.

Implement a custom collator that:

1. Loads waveforms.
2. Sends them to the feature extractor.
3. Pads them dynamically within each batch.
4. Produces:
   - `input_values`
   - `attention_mask`
   - `labels`

Do not globally force every audio file to an arbitrary fixed duration unless required.

Prefer dynamic padding.

---

## 14. Dataset Class

Create a PyTorch Dataset such as:

```python
RAVDESSXLSRDataset
```

It should:

- Read the appropriate CSV
- Load audio
- Validate the audio path
- Return waveform + label
- Preserve filename and actor ID for evaluation/debugging

Do not parse RAVDESS filenames again if the metadata CSV already contains the labels.

---

## 15. Training Configuration

Create a central configuration.

Example:

```yaml
model_name: facebook/wav2vec2-xls-r-300m

num_classes: 8

sample_rate: 16000

batch_size: 4

num_epochs: 20

encoder_learning_rate: 1.0e-5

classifier_learning_rate: 1.0e-4

weight_decay: 0.01

dropout: 0.3

warmup_ratio: 0.1

gradient_accumulation_steps: 4

mixed_precision: true

early_stopping_patience: 5

seed: 42
```

Adjust batch size based on available GPU memory.

Do not change the dataset because of GPU limitations.

Use gradient accumulation when necessary.

---

## 16. GPU Support

Automatically detect:

```text
CUDA
```

and use GPU when available.

Example:

```python
device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)
```

Print:

```text
Device
GPU name
GPU memory
```

If CUDA is unavailable, allow CPU execution for debugging.

Do not require Apple MPS for the main experiment.

---

## 17. Mixed Precision

Support CUDA mixed precision.

Use:

```text
FP16 or BF16
```

depending on GPU support.

Make it configurable.

For example:

```text
--mixed_precision
```

The training code should use the current PyTorch AMP API.

---

## 18. Gradient Accumulation

Because XLS-R-300M is a large model, implement gradient accumulation.

Example:

```text
batch_size = 4
gradient_accumulation_steps = 4
```

Effective batch size:

```text
16
```

Make this configurable.

---

## 19. Gradient Clipping

Implement:

```text
max_grad_norm = 1.0
```

to prevent unstable gradients.

---

## 20. Learning Rate Scheduler

Use a standard scheduler with warmup.

Recommended:

```text
Linear warmup + linear decay
```

or a Hugging Face-compatible scheduler.

Use:

```text
warmup_ratio = 0.1
```

Make it configurable.

---

## 21. Early Stopping

Monitor:

```text
Validation Macro-F1
```

Use validation Macro-F1 as the primary model-selection metric.

Example:

```text
patience = 5
```

If validation Macro-F1 does not improve for 5 epochs:

```text
stop training
```

Save the best checkpoint based on:

```text
highest validation Macro-F1
```

Do NOT select the best model based only on training loss.

---

## 22. Checkpointing

Save:

```text
checkpoints/
└── best_model/
```

Include:

- model weights
- optimizer state
- scheduler state
- epoch
- best validation Macro-F1
- configuration
- label mapping

Also save the final model separately.

Example:

```text
outputs/wav2vec2_xlsr_300m/
│
├── checkpoints/
│   ├── best_model/
│   └── final_model/
│
├── logs/
├── metrics/
└── predictions/
```

---

## 23. Training Metrics

For every epoch calculate:

### Training

```text
Train Loss
Train Accuracy
Train Macro-F1
```

### Validation

```text
Validation Loss
Validation Accuracy
Validation Macro-F1
Validation Weighted-F1
Validation UAR
Validation WAR
```

Save them to:

```text
metrics/training_history.csv
```

Example:

```text
epoch,train_loss,train_accuracy,train_macro_f1,val_loss,val_accuracy,val_macro_f1,val_weighted_f1,val_uar,val_war
```

---

## 24. Test Evaluation

After training is complete:

IMPORTANT:

Use the **best validation Macro-F1 checkpoint**.

Evaluate it ONCE on:

```text
test.csv
```

Do not use the test set during training or model selection.

Calculate:

```text
Accuracy
Macro Precision
Macro Recall
Macro F1
Weighted Precision
Weighted Recall
Weighted F1
UAR
WAR
```

---

## 25. Definitions

Use:

### WAR

Weighted Average Recall / weighted accuracy according to the chosen SER evaluation implementation.

### UAR

Unweighted Average Recall:

```text
UAR = mean(recall for each emotion class)
```

For clarity, document the exact formulas used.

Macro-F1 must be calculated across the 8 emotion classes.

---

## 26. Confusion Matrix

Generate a confusion matrix for the test set.

Labels must appear in this order:

```text
Neutral
Calm
Happy
Sad
Angry
Fearful
Disgust
Surprised
```

Save:

```text
predictions/confusion_matrix.png
```

Also save the numeric confusion matrix:

```text
predictions/confusion_matrix.csv
```

---

## 27. Classification Report

Generate:

```text
predictions/classification_report.csv
```

containing:

```text
emotion
precision
recall
f1_score
support
```

for all 8 classes.

---

## 28. Test Predictions

Save every test prediction:

```text
predictions/test_predictions.csv
```

Columns:

```text
filepath
filename
actor_id
true_label
true_emotion
predicted_label
predicted_emotion
confidence
```

This is important for later error analysis.

---

## 29. Training Curves

Generate separate plots:

### Plot 1

```text
Training Loss vs Validation Loss
```

### Plot 2

```text
Training Macro-F1 vs Validation Macro-F1
```

### Plot 3

```text
Training Accuracy vs Validation Accuracy
```

Save:

```text
metrics/loss_curve.png
metrics/macro_f1_curve.png
metrics/accuracy_curve.png
```

Do not use subplots. Each figure should be separate.

---

## 30. Model Information

Before training, report:

```text
Model name
Number of parameters
Trainable parameters
Frozen parameters
Number of classes
Input sampling rate
Batch size
Effective batch size
Learning rate
GPU
```

Save this to:

```text
metrics/model_info.txt
```

Also calculate:

```text
Total parameters
Trainable parameters
```

---

## 31. Computational Metrics

Measure:

```text
Total training time
Average epoch time
Inference time
```

For inference time, report both:

```text
total test inference time
average inference time per audio file
```

Also report GPU memory usage if CUDA is available.

Save:

```text
metrics/computational_metrics.csv
```

---

## 32. Final Result File

Create:

```text
metrics/final_results.csv
```

with:

```text
model
accuracy
macro_precision
macro_recall
macro_f1
weighted_precision
weighted_recall
weighted_f1
uar
war
parameters
trainable_parameters
training_time
inference_time
```

The model field must be:

```text
Wav2Vec2-XLS-R-300M
```

This file will later be combined with results from:

```text
CNN + MFCC
CNN + BiLSTM
Wav2Vec2
HuBERT
WavLM
emotion2vec+
BEATs
```

for the final research comparison.

---

## 33. Reproducibility

Use:

```text
seed = 42
```

Set seeds for:

- Python
- NumPy
- PyTorch
- CUDA

Where practical, use deterministic settings.

Save the complete configuration used for the experiment:

```text
config.yaml
```

inside:

```text
outputs/wav2vec2_xlsr_300m/
```

---

## 34. Experiment Directory

Use exactly:

```text
outputs/
└── wav2vec2_xlsr_300m/
    │
    ├── config.yaml
    │
    ├── checkpoints/
    │   ├── best_model/
    │   └── final_model/
    │
    ├── metrics/
    │   ├── training_history.csv
    │   ├── final_results.csv
    │   ├── model_info.txt
    │   ├── computational_metrics.csv
    │   ├── loss_curve.png
    │   ├── macro_f1_curve.png
    │   └── accuracy_curve.png
    │
    ├── predictions/
    │   ├── test_predictions.csv
    │   ├── classification_report.csv
    │   ├── confusion_matrix.csv
    │   └── confusion_matrix.png
    │
    └── logs/
        └── training.log
```

---

## 35. Command-Line Interface

Create a main training script:

```bash
python train_xlsr.py \
    --data_dir /path/to/ravdess_preprocessed \
    --output_dir outputs/wav2vec2_xlsr_300m
```

Support:

```text
--batch_size
--epochs
--encoder_lr
--classifier_lr
--freeze_encoder
--gradient_accumulation_steps
--mixed_precision
--seed
```

Also create a separate evaluation script:

```bash
python evaluate_xlsr.py \
    --checkpoint outputs/wav2vec2_xlsr_300m/checkpoints/best_model \
    --test_csv /path/to/test.csv
```

---

## 36. Important Research Constraints

This is a research experiment.

Therefore:

1. Do not change the RAVDESS dataset split.
2. Do not train on the test set.
3. Do not tune hyperparameters using the test set.
4. Do not use test performance for early stopping.
5. Do not perform random file-level splitting.
6. Preserve actor independence.
7. Keep the emotion label mapping identical across all future models.
8. Keep the same evaluation metrics for all future models.
9. Record all hyperparameters.
10. Save reproducible results.

---

## 37. Do Not Modify Preprocessing

The preprocessing stage has already produced:

```text
16 kHz mono WAV
train.csv
validation.csv
test.csv
```

Do not:

- recreate the dataset
- change the actor split
- extract MFCC
- extract spectrograms
- perform augmentation
- normalize using statistics from the test set
- remove samples without reporting them

Only perform the minimum loading/padding required by XLS-R.

---

## 38. Expected Final Pipeline

```text
                 RAVDESS
                    │
                    ▼
        Existing Preprocessing
                    │
                    ▼
        Actor-independent split
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
      Train        Val         Test
        │           │
        └──────┬────┘
               ▼
      16 kHz Raw Waveform
               │
               ▼
   XLS-R Feature Extractor
               │
               ▼
  Wav2Vec2-XLS-R-300M Encoder
               │
               ▼
       Masked Mean Pooling
               │
               ▼
            Dropout
               │
               ▼
       Linear Classification
               │
               ▼
         8 Emotions
               │
               ▼
      Validation Macro-F1
               │
               ▼
       Best Checkpoint
               │
               ▼
         Final Test
               │
               ▼
   Research Metrics + Plots
```

---

## 39. Final Deliverable

At the end, provide:

1. Complete source code.
2. Configuration file.
3. Training script.
4. Evaluation script.
5. Dataset loader.
6. Dynamic padding collator.
7. XLS-R-300M model implementation.
8. Training logs.
9. Best checkpoint.
10. Final checkpoint.
11. Training curves.
12. Confusion matrix.
13. Classification report.
14. Test predictions.
15. Final metrics CSV.
16. Model parameter count.
17. Training/inference time.
18. A short README explaining exactly how to run the experiment.

Again, **do not implement the other SER models yet**. This task is exclusively for:

```text
facebook/wav2vec2-xls-r-300m
```

The implementation must be modular so that the same dataset and evaluation framework can later be reused for the other models in the research comparison.
