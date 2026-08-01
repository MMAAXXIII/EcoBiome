"""Main application for EcoBiome."""

import platform
from importlib.metadata import PackageNotFoundError, version


def run() -> None:
    """Start the EcoBiome application."""

    try:
        app_version = version("ecobiome")
    except PackageNotFoundError:
        app_version = "development"

    print("=" * 50)
    print("🌍 EcoBiome")
    print("Scientific Ecosystem Simulator")
    print(f"Version : {app_version}")
    print("=" * 50)
    print()
    print(f"Python : {platform.python_version()}")
    print("Projet chargé : aucun")
    print()
    print("EcoBiome est prêt.")