"""Display an EcoBiome architecture diagnostic report."""

from ecobiome.reasoning.architecture_doctor import (
    EcoBiomeDoctor,
)
from ecobiome.reasoning.profiles import (
    build_camera_lux_registry,
)


def main() -> None:
    """Run and display the architecture diagnostic."""
    report = EcoBiomeDoctor(
        build_camera_lux_registry()
    ).inspect()

    print("EcoBiome Architecture Report")
    print("=" * 32)

    for diagnostic in report.diagnostics:
        symbol = "OK" if diagnostic.succeeded else "KO"

        print(
            f"[{symbol}] "
            f"{diagnostic.identifier}: "
            f"{diagnostic.message}"
        )

    summary = report.component_summary

    print()
    print("Registered components")
    print(f"- Quality rules: {summary.quality_rule_count}")
    print(
        f"- Consistency rules: "
        f"{summary.consistency_rule_count}"
    )
    print(
        f"- Hypothesis rules: "
        f"{summary.hypothesis_rule_count}"
    )
    print(
        f"- Experiment rules: "
        f"{summary.experiment_rule_count}"
    )
    print(f"- Total: {summary.total_count}")
    print()
    print(
        "Overall status: "
        f"{'HEALTHY' if report.succeeded else 'UNHEALTHY'}"
    )


if __name__ == "__main__":
    main()
