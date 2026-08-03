"""Demonstrate EcoBiome physical-unit handling."""

from ecobiome.core.units import Measurement


def main() -> None:
    """Display several safe physical conversions."""
    volume = Measurement(300, "liter")
    additional_volume = Measurement(2, "meter ** 3")
    total_volume = volume + additional_volume

    flow_rate = Measurement(20, "meter ** 3 / hour")
    temperature = Measurement(22, "degC")

    print("=" * 64)
    print("EcoBiome — Système d'unités physiques")
    print("=" * 64)
    print(
        f"300 L en m³       : "
        f"{volume.to('meter ** 3').value:.3f} m³"
    )
    print(
        f"30 L + 2 m³       : "
        f"{Measurement(30, 'liter') + additional_volume}"
    )
    print(
        f"Débit             : "
        f"{flow_rate.to('liter / hour').value:.0f} L/h"
    )
    print(
        f"Température SI    : "
        f"{temperature.to('kelvin').value:.2f} K"
    )
    print(f"Volume total      : {total_volume.value:.0f} L")


if __name__ == "__main__":
    main()
