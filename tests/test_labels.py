"""Unit tests for locked emotion label mapping."""

from __future__ import annotations

import pytest

from xlsr.data.labels import (
    CLASS_NAMES,
    EMOTION_TO_ID,
    ID_TO_EMOTION,
    NUM_CLASSES,
    emotion_to_id,
    id_to_emotion,
)


def test_num_classes_is_eight() -> None:
    assert NUM_CLASSES == 8
    assert len(CLASS_NAMES) == 8


def test_bidirectional_mapping() -> None:
    for emotion, label_id in EMOTION_TO_ID.items():
        assert ID_TO_EMOTION[label_id] == emotion
        assert emotion_to_id(emotion) == label_id
        assert id_to_emotion(label_id) == emotion


def test_label_ids_are_contiguous() -> None:
    assert sorted(ID_TO_EMOTION.keys()) == list(range(NUM_CLASSES))


def test_unknown_emotion_raises() -> None:
    with pytest.raises(Exception):
        emotion_to_id("joy")
