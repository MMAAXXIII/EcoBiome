"""Scientific rules related to hardware and data acquisition."""

from ecobiome.reasoning.rules.hardware.frozen_sensor import (
    FrozenSensorRule,
)
from ecobiome.reasoning.rules.hardware.stale_observation import (
    StaleObservationRule,
)

__all__ = [
    "FrozenSensorRule",
    "StaleObservationRule",
]
