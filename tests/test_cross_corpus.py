"""Unit tests for Cross-Corpus Canonical Emotion Mapping."""

import pytest
from scripts.evaluate_cross_corpus import CANONICAL_MAP, DATASET_LABEL_MAPPINGS, canonicalize


def test_canonical_emotion_mapping():
    assert canonicalize("anger") == "angry"
    assert canonicalize("angry") == "angry"
    assert canonicalize("happiness") == "happy"
    assert canonicalize("happy") == "happy"
    assert canonicalize("sadness") == "sad"
    assert canonicalize("sad") == "sad"
    assert canonicalize("fearful") == "fear"
    assert canonicalize("fear") == "fear"
    assert canonicalize("disgust") == "disgust"
    assert canonicalize("neutral") == "neutral"
    assert canonicalize("surprise") == "surprise"
    assert canonicalize("pleasant_surprise") == "surprise"
    assert canonicalize("surprised") == "surprise"
    assert canonicalize("calm") == "calm"


def test_shared_canonical_classes():
    # CREMA-D and RAVDESS should share 6 canonical emotions
    crema_canonical = {canonicalize(k) for k in DATASET_LABEL_MAPPINGS["cremad"].keys()}
    ravdess_canonical = {canonicalize(k) for k in DATASET_LABEL_MAPPINGS["ravdess"].keys()}
    shared = crema_canonical & ravdess_canonical
    assert len(shared) == 6
    assert shared == {"angry", "disgust", "fear", "happy", "neutral", "sad"}


def test_all_datasets_share_core_emotions():
    all_sets = [
        {canonicalize(k) for k in DATASET_LABEL_MAPPINGS[d].keys()}
        for d in ["cremad", "ravdess", "savee", "tess"]
    ]
    universal_intersection = set.intersection(*all_sets)
    assert len(universal_intersection) == 6
    assert universal_intersection == {"angry", "disgust", "fear", "happy", "neutral", "sad"}
