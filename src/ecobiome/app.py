"""Main application for EcoBiome."""

from ecobiome.ui.web_launcher import run_web_frontend


def run() -> None:
    """Start the canonical EcoBiome Bolt/React interface."""
    run_web_frontend()
