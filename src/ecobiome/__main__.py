"""Entry point for EcoBiome."""

import sys

from ecobiome.app import run
from ecobiome.knowledge_acquisition.cli import main

if __name__ == "__main__":
    if len(sys.argv) > 1:
        raise SystemExit(main())

    run()
