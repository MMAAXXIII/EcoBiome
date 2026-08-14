"""Automatic bridges into the EcoBiome scientific journal."""

from ecobiome.integrations.journal.diagnostic_bridge import (
    DiagnosticJournalBridge,
)
from ecobiome.integrations.journal.learning_bridge import (
    LearningJournalBridge,
)
from ecobiome.integrations.journal.media_bridge import (
    MediaJournalBridge,
)
from ecobiome.integrations.journal.service import (
    JournalIntegrationService,
)

__all__ = [
    "DiagnosticJournalBridge",
    "JournalIntegrationService",
    "LearningJournalBridge",
    "MediaJournalBridge",
]
