"""Unified facade for automatic journal integrations."""

from ecobiome.integrations.journal.diagnostic_bridge import (
    DiagnosticJournalBridge,
)
from ecobiome.integrations.journal.learning_bridge import (
    LearningJournalBridge,
)
from ecobiome.integrations.journal.media_bridge import (
    MediaJournalBridge,
)
from ecobiome.journal import ScientificJournal


class JournalIntegrationService:
    """Expose all journal bridges through one integration service."""

    def __init__(
        self,
        journal: ScientificJournal,
    ) -> None:
        self.media = MediaJournalBridge(journal)
        self.diagnostics = DiagnosticJournalBridge(journal)
        self.learning = LearningJournalBridge(journal)
