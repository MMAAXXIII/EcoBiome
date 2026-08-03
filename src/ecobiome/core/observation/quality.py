"""Quality assessments and diagnostics for scientific observations."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID


class DataQuality(StrEnum):
    """Usability classification of an observed datum."""

    VALID = "valid"
    SUSPECT = "suspect"
    STALE = "stale"
    INVALID = "invalid"
    MISSING = "missing"


class DiagnosticCode(StrEnum):
    """Standard diagnostic codes explaining reduced data quality."""

    STALE_OBSERVATION = "observation.stale"
    FROZEN_SENSOR = "sensor.frozen"
    VALUE_OUT_OF_RANGE = "value.out_of_range"
    IMPOSSIBLE_VALUE = "value.impossible"
    MISSING_VALUE = "value.missing"
    COMMUNICATION_TIMEOUT = "device.communication_timeout"
    SENSOR_FAILURE = "device.sensor_failure"
    CAMERA_BLACK_FRAME = "camera.black_frame"
    CAMERA_FROZEN_FRAME = "camera.frozen_frame"
    CALIBRATION_EXPIRED = "device.calibration_expired"
    SOURCE_CONTRADICTION = "source.contradiction"
    UNKNOWN = "diagnostic.unknown"


@dataclass(frozen=True, slots=True, kw_only=True)
class QualityAssessment:
    """Describe the assessed reliability of one observation."""

    observation_id: UUID
    quality: DataQuality
    score: float
    diagnostics: tuple[DiagnosticCode, ...] = ()
    reasons: tuple[str, ...] = ()
    assessed_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    def __post_init__(self) -> None:
        """Validate and normalize the assessment."""
        if isinstance(self.score, bool) or not isinstance(
            self.score,
            int | float,
        ):
            raise TypeError(
                "Quality assessment score must be numeric."
            )

        score = float(self.score)

        if not 0.0 <= score <= 1.0:
            raise ValueError(
                "Quality assessment score must be between 0 and 1."
            )

        if self.assessed_at.tzinfo is None:
            raise ValueError(
                "Quality assessment timestamp must include a timezone."
            )

        diagnostics = tuple(dict.fromkeys(self.diagnostics))

        reasons = tuple(
            dict.fromkeys(
                reason.strip()
                for reason in self.reasons
                if reason.strip()
            )
        )

        if self.quality is DataQuality.VALID and diagnostics:
            raise ValueError(
                "A valid observation cannot contain diagnostics."
            )

        if self.quality is not DataQuality.VALID and not diagnostics:
            raise ValueError(
                "A non-valid observation requires a diagnostic."
            )

        if self.quality in {
            DataQuality.INVALID,
            DataQuality.MISSING,
        } and score > 0.0:
            raise ValueError(
                "Invalid or missing observations must have a zero score."
            )

        object.__setattr__(self, "score", score)
        object.__setattr__(self, "diagnostics", diagnostics)
        object.__setattr__(self, "reasons", reasons)

    @property
    def is_usable_for_reasoning(self) -> bool:
        """Return whether the observation may influence reasoning."""
        return self.quality in {
            DataQuality.VALID,
            DataQuality.SUSPECT,
        } and self.score > 0.0

    @property
    def requires_attention(self) -> bool:
        """Return whether human or automated attention is warranted."""
        return self.quality is not DataQuality.VALID

    @classmethod
    def valid(
        cls,
        observation_id: UUID,
        *,
        score: float = 1.0,
        assessed_at: datetime | None = None,
    ) -> QualityAssessment:
        """Create an assessment for a valid observation."""
        return cls(
            observation_id=observation_id,
            quality=DataQuality.VALID,
            score=score,
            assessed_at=assessed_at or datetime.now(UTC),
        )

    @classmethod
    def rejected(
        cls,
        observation_id: UUID,
        *,
        quality: DataQuality,
        diagnostic: DiagnosticCode,
        reason: str,
        assessed_at: datetime | None = None,
    ) -> QualityAssessment:
        """Create a zero-score assessment for unusable data."""
        if quality not in {
            DataQuality.INVALID,
            DataQuality.MISSING,
        }:
            raise ValueError(
                "Rejected assessments require INVALID or MISSING quality."
            )

        return cls(
            observation_id=observation_id,
            quality=quality,
            score=0.0,
            diagnostics=(diagnostic,),
            reasons=(reason,),
            assessed_at=assessed_at or datetime.now(UTC),
        )
