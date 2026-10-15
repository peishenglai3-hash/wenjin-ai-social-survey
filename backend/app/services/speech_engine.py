"""
Unified Speech Processing Engine — FunASR primary + cloud fallback.

Architecture:
  Primary:   FunASR (local/self-hosted) — MIT license, 170x realtime
  Fallback:  Qwen Paraformer / Qwen3-ASR-Flash (cloud)
  Legacy:    Xunfei RT-ASR (cloud)

Provides a single interface for:
  - Voice Activity Detection (VAD)
  - Speech-to-Text (ASR) — streaming + batch
  - Speaker Diarization (cam++)
  - Emotion Detection (emotion2vec+)
  - Punctuation restoration
  - Language identification
"""

from __future__ import annotations

import asyncio
import logging
import os
import subprocess
import time
from dataclasses import dataclass, field
from typing import AsyncGenerator

from app.config import settings

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────
PCM_RATE = 16000
PCM_CHANNELS = 1
PCM_WIDTH = 2  # 16-bit
PCM_CHUNK_MS = 200
PCM_CHUNK_BYTES = PCM_RATE * PCM_WIDTH * PCM_CHUNK_MS // 1000  # 6400


# ── Data Models ────────────────────────────────────────────────────────

@dataclass
class SpeechSegment:
    """A single utterance segment with speaker ID, emotion, and timestamps."""
    start_ms: int
    end_ms: int
    speaker_id: int = -1
    speaker_label: str = ""  # "interviewer" | "respondent" | "SPEAKER_00"
    text: str = ""
    emotion: str = "neutral"  # angry | happy | neutral | sad
    emotion_confidence: float = 0.0
    language: str = "zh"
    words: list[dict] = field(default_factory=list)


@dataclass
class TranscriptionResult:
    """Full transcription result from SpeechEngine."""
    text: str = ""
    segments: list[SpeechSegment] = field(default_factory=list)
    duration_ms: int = 0
    language: str = "zh"
    engine_used: str = ""
    speaker_count: int = 0
    emotion_summary: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)


@dataclass
class StreamingResult:
    """Incremental result from streaming ASR."""
    text: str = ""
    is_final: bool = False
    speaker_id: int = -1
    emotion: str = "neutral"
    start_ms: int = 0
    end_ms: int = 0


# ── FunASR Engine (Primary) ────────────────────────────────────────────

class FunASREngine:
    """Local FunASR-based speech processing engine.

    Uses FunASR toolkit from Alibaba DAMO Academy:
    - SenseVoiceSmall: ASR (234M params, zh/en/ja/ko/yue)
    - fsmn-vad: Voice Activity Detection
    - cam++: Speaker diarization (7.2M params)
    - emotion2vec+large: Emotion recognition (300M params, 4-class: angry/happy/neutral/sad)

    One pipeline call: VAD → ASR → punctuation → speaker ID → emotion.
    """

    def __init__(self):
        self._asr_model = None
        self._emotion_model = None
        self._available = None  # Tri-state: None=unchecked

    @property
    def available(self) -> bool:
        if self._available is None:
            try:
                import funasr  # noqa: F401
                self._available = True
            except ImportError:
                logger.info("FunASR not installed — cloud fallback will be used")
                self._available = False
        return self._available

    def _get_asr_model(self):
        if self._asr_model is None and self.available:
            from funasr import AutoModel
            self._asr_model = AutoModel(
                model=settings.funasr_asr_model,
                vad_model=settings.funasr_vad_model,
                spk_model=settings.funasr_spk_model,
                device=settings.funasr_device,
                disable_pbar=True,
            )
        return self._asr_model

    def _get_emotion_model(self):
        if self._emotion_model is None and self.available:
            from funasr import AutoModel
            self._emotion_model = AutoModel(
                model=settings.funasr_emotion_model,
                device=settings.funasr_device,
                disable_pbar=True,
            )
        return self._emotion_model

    def process_file(self, filepath: str) -> TranscriptionResult:
        """Process audio: VAD → ASR → speaker ID → emotion (single pass)."""
        if not self.available:
            raise RuntimeError("FunASR not available")

        model = self._get_asr_model()
        if model is None:
            raise RuntimeError("FunASR model failed to load")

        raw = model.generate(input=filepath, batch_size_s=settings.funasr_batch_size_s)
        result = self._parse_result(raw, filepath)

        # Run emotion on each segment
        try:
            emo_model = self._get_emotion_model()
            if emo_model is not None and result.segments:
                for seg in result.segments:
                    try:
                        emo_raw = emo_model.generate(
                            input=filepath,
                            granularity="utterance",
                            start_ms=seg.start_ms,
                            end_ms=seg.end_ms,
                        )
                        if emo_raw and len(emo_raw) > 0:
                            self._apply_emotion(seg, emo_raw[0])
                    except Exception:
                        logger.debug("Per-segment emotion detection failed (non-fatal)", exc_info=True)
        except Exception as e:
            logger.warning(f"Emotion model load failed (non-fatal): {e}")

        result.emotion_summary = self._emotion_summary(result.segments)
        return result

    def _parse_result(self, raw: list, filepath: str) -> TranscriptionResult:
        segments = []
        full_text: list[str] = []

        if not raw:
            return TranscriptionResult(
                duration_ms=self._audio_duration_ms(filepath),
                engine_used="funasr",
            )

        data = raw[0] if isinstance(raw, list) else raw
        sentence_info = data.get("sentence_info") or data.get("sentences") or []

        for item in sentence_info:
            seg = SpeechSegment(
                start_ms=item.get("start", item.get("begin_time", 0)),
                end_ms=item.get("end", item.get("end_time", 0)),
                speaker_id=item.get("spk", -1),
                speaker_label=f"SPEAKER_{item.get('spk', 0):02d}",
                text=(item.get("text") or item.get("sentence", "")).strip(),
                emotion=item.get("emotion", "neutral"),
            )
            segments.append(seg)
            if seg.text:
                full_text.append(seg.text)

        speaker_ids = {s.speaker_id for s in segments if s.speaker_id >= 0}
        duration_ms = segments[-1].end_ms if segments else self._audio_duration_ms(filepath)

        return TranscriptionResult(
            text="".join(full_text) if full_text else data.get("text", ""),
            segments=segments,
            duration_ms=duration_ms,
            engine_used="funasr",
            speaker_count=len(speaker_ids),
        )

    @staticmethod
    def _apply_emotion(seg: SpeechSegment, data: dict) -> None:
        labels = data.get("labels", [])
        scores = data.get("scores", [])
        if labels and scores:
            idx = scores.index(max(scores))
            seg.emotion = labels[idx]
            seg.emotion_confidence = scores[idx]

    @staticmethod
    def _emotion_summary(segments: list[SpeechSegment]) -> dict:
        if not segments:
            return {}
        total_ms = sum((s.end_ms - s.start_ms) for s in segments)
        if total_ms <= 0:
            return {}
        summary: dict[str, int] = {}
        for s in segments:
            dur = s.end_ms - s.start_ms
            emo = s.emotion or "neutral"
            summary[emo] = summary.get(emo, 0) + dur
        return {k: round(v / total_ms * 100, 1) for k, v in summary.items()}

    @staticmethod
    def _audio_duration_ms(filepath: str) -> int:
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries",
                 "format=duration", "-of", "default=noprint_wrappers=1:nokey=1",
                 filepath],
                capture_output=True, text=True, timeout=10,
            )
            return int(float(result.stdout.strip()) * 1000)
        except Exception:
            logger.debug("Failed to probe audio duration via ffprobe", exc_info=True)
            return 0


funasr_engine = FunASREngine()


# ── Unified Speech Engine ──────────────────────────────────────────────

class SpeechEngine:
    """Unified speech processing with automatic engine selection.

    Priority (adjusted for cloud-VM deployment without GPU):
      Qwen FileTrans (cloud, speaker diarization) → FunASR (local, needs GPU) → Qwen Paraformer → Xunfei

    Note: FunASR requires GPU for production use (170x realtime).
    On CPU-only servers it's ~10x slower and memory-hungry (models need 3+ GB).
    For the current 2vCPU/3.4GB server, cloud APIs are the recommended primary.
    """

    def __init__(self):
        self._funasr = funasr_engine

    async def process_file(
        self, filepath: str, language: str = "zh",
        with_emotion: bool = True, with_speaker: bool = True,
    ) -> TranscriptionResult:
        """Transcribe an audio file through the best available engine."""
        start = time.time()

        # 1) Qwen FileTrans (cloud, speaker diarization built-in — best for this server)
        if settings.qwen_api_key:
            try:
                from app.services.asr_qwen import qwen_filetrans

                file_url = f"{settings.public_base_url.rstrip('/')}/uploads/{os.path.basename(filepath)}"
                task_id = await qwen_filetrans.submit(file_url, language)
                cloud = await qwen_filetrans.poll(task_id)
                result = self._from_qwen_filetrans(cloud, filepath)
                logger.info(f"Qwen FileTrans done: {len(result.text)} chars, {result.speaker_count} speakers")
                return result
            except Exception as e:
                logger.warning(f"Qwen FileTrans failed ({e}) → falling back")

        # 2) FunASR (local, most capable but needs GPU for production speed)
        if self._funasr.available:
            try:
                logger.info(f"SpeechEngine: FunASR → {filepath}")
                result = await asyncio.to_thread(
                    self._funasr.process_file, filepath
                )
                result.engine_used = "funasr"
                logger.info(
                    f"FunASR done in {time.time() - start:.1f}s: "
                    f"{len(result.text)} chars, {len(result.segments)} segs, "
                    f"{result.speaker_count} speakers"
                )
                return result
            except Exception as e:
                logger.warning(f"FunASR failed ({e}) → falling back to cloud")

        # 3) Qwen Paraformer WebSocket (no speaker diarization — last resort cloud)
        if settings.qwen_api_key:
            try:
                from app.services.asr_qwen import QwenRealtimeASR
                text = await QwenRealtimeASR().transcribe_file(filepath)
                if text.strip():
                    return TranscriptionResult(
                        text=text,
                        duration_ms=FunASREngine._audio_duration_ms(filepath),
                        engine_used="qwen_paraformer",
                    )
            except Exception as e:
                logger.warning(f"Qwen Paraformer failed ({e})")

        raise RuntimeError(
            "No speech engine available. Set QWEN_API_KEY or install `pip install funasr` on a GPU server."
        )

    @staticmethod
    def _from_qwen_filetrans(raw: dict, filepath: str) -> TranscriptionResult:
        segments = []
        for s in raw.get("sentences", []):
            segments.append(SpeechSegment(
                start_ms=s.get("begin_time", 0),
                end_ms=s.get("end_time", 0),
                speaker_id=s.get("speaker_id", -1),
                speaker_label=f"SPEAKER_{s.get('speaker_id', 0):02d}",
                text=s.get("text", "").strip(),
            ))
        speaker_ids = {s.get("speaker_id", -1) for s in raw.get("sentences", [])}
        return TranscriptionResult(
            text=raw.get("transcription", ""),
            segments=segments,
            duration_ms=FunASREngine._audio_duration_ms(filepath),
            engine_used="qwen_filetrans",
            speaker_count=len(speaker_ids),
        )


speech_engine = SpeechEngine()
