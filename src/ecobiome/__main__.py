"""Entry point for EcoBiome."""

import sys

from ecobiome.cli import main


def run_entry_point() -> int:
    """Dispatch CLI arguments before importing the graphical application."""
    if len(sys.argv) > 1:
        return main(sys.argv[1:])

    from ecobiome.app import run

    run()
    return 0


if __name__ == "__main__":
    raise SystemExit(run_entry_point())