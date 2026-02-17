"""Tests for CoreML provider type safety and runtime validation."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from hypnogen.core.tts_providers.coreml import (
    CoreMLProvider,
    DecoderModelSpec,
    DurationModelSpec,
)


def _make_mock_feature(name: str | None, shape: tuple[int, ...]) -> MagicMock:
    feature = MagicMock()
    feature.name = name
    feature.type.multiArrayType.shape = list(shape)
    return feature


def _make_mock_model(
    inputs: list[tuple[str | None, tuple[int, ...]]],
    outputs: list[tuple[str | None, tuple[int, ...]]],
) -> MagicMock:
    model = MagicMock()
    spec = model.get_spec.return_value.description
    spec.input = [_make_mock_feature(n, s) for n, s in inputs]
    spec.output = [_make_mock_feature(n, s) for n, s in outputs]
    return model


class TestDurationSpecNoneNames:
    """Verify _infer_duration_spec raises ValueError when spec names are None."""

    def test_missing_input_ids_name_raises(self) -> None:
        model = _make_mock_model(
            inputs=[
                ("unknown_input", (1, 128)),
                ("ref_s", (1, 256)),
                ("speed", (1,)),
                ("attention_mask", (1, 128)),
            ],
            outputs=[
                ("pred_dur", (1, 128)),
                ("d", (1, 640, 128)),
                ("t_en", (1, 512, 128)),
                ("s", (1, 256)),
            ],
        )
        provider = object.__new__(CoreMLProvider)
        with pytest.raises(RuntimeError, match="missing expected features"):
            provider._infer_duration_spec(model)

    def test_all_valid_names_succeeds(self) -> None:
        model = _make_mock_model(
            inputs=[
                ("input_ids", (1, 128)),
                ("ref_s", (1, 256)),
                ("speed", (1,)),
                ("attention_mask", (1, 128)),
            ],
            outputs=[
                ("pred_dur", (1, 128)),
                ("d", (1, 640, 128)),
                ("t_en", (1, 512, 128)),
                ("s", (1, 256)),
            ],
        )
        provider = object.__new__(CoreMLProvider)
        spec = provider._infer_duration_spec(model)
        assert isinstance(spec, DurationModelSpec)
        assert spec.input_ids_name == "input_ids"
        assert spec.t_en_name == "t_en"


class TestDecoderSpecNoneNames:
    """Verify _infer_decoder_spec raises ValueError when spec names are None."""

    def test_missing_asr_name_raises(self) -> None:
        model = _make_mock_model(
            inputs=[
                ("unknown_input", (1, 512, 240)),
                ("F0_pred", (1, 240)),
                ("N_pred", (1, 240)),
                ("ref_s", (1, 256)),
            ],
            outputs=[
                ("waveform", (1, 72000)),
            ],
        )
        provider = object.__new__(CoreMLProvider)
        with pytest.raises(RuntimeError, match="missing expected features"):
            provider._infer_decoder_spec(model, "3s")

    def test_all_valid_names_succeeds(self) -> None:
        model = _make_mock_model(
            inputs=[
                ("asr", (1, 512, 240)),
                ("F0_pred", (1, 240)),
                ("N_pred", (1, 240)),
                ("ref_s", (1, 256)),
            ],
            outputs=[
                ("waveform", (1, 72000)),
            ],
        )
        provider = object.__new__(CoreMLProvider)
        spec = provider._infer_decoder_spec(model, "3s")
        assert isinstance(spec, DecoderModelSpec)
        assert spec.asr_name == "asr"
        assert spec.seconds == 3


class TestSynthesizeBatchValidation:
    """Verify synthesize_batch rejects invalid inputs before inference."""

    def test_empty_text_raises_value_error(self) -> None:
        provider = object.__new__(CoreMLProvider)
        with pytest.raises(ValueError, match="non-empty string"):
            provider.synthesize_batch(["hello", ""])

    def test_whitespace_only_text_raises_value_error(self) -> None:
        provider = object.__new__(CoreMLProvider)
        with pytest.raises(ValueError, match="non-empty string"):
            provider.synthesize_batch(["  \t  "])

    def test_zero_speed_raises_value_error(self) -> None:
        provider = object.__new__(CoreMLProvider)
        with pytest.raises(ValueError, match="speed must be positive"):
            provider.synthesize_batch(["hello"], speed=0.0)

    def test_negative_speed_raises_value_error(self) -> None:
        provider = object.__new__(CoreMLProvider)
        with pytest.raises(ValueError, match="speed must be positive"):
            provider.synthesize_batch(["hello"], speed=-1.0)


class TestToNumpyDtype:
    """Verify _to_numpy accepts np.dtype(np.float32)."""

    def test_converts_list_to_float32(self) -> None:
        result = CoreMLProvider._to_numpy([1.0, 2.0, 3.0], dtype=np.dtype(np.float32))
        assert result.dtype == np.float32
        np.testing.assert_array_equal(result, [1.0, 2.0, 3.0])

    def test_converts_tensor_like_object(self) -> None:
        mock_tensor = MagicMock()
        mock_tensor.detach.return_value = mock_tensor
        mock_tensor.cpu.return_value = mock_tensor
        mock_tensor.numpy.return_value = np.array([0.5, -0.5])

        result = CoreMLProvider._to_numpy(mock_tensor, dtype=np.dtype(np.float32))
        assert result.dtype == np.float32
