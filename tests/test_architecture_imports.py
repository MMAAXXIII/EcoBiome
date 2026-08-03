"""Architecture smoke tests for package import independence."""

import subprocess
import sys


def run_import_check(statement: str) -> None:
    """Run one import in a clean Python interpreter."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            statement,
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, (
        f"Import failed.\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )


def test_observation_package_imports_independently() -> None:
    run_import_check(
        "from ecobiome.core.observation import "
        "ObservationQualityEngine"
    )


def test_diagnostic_pipeline_imports_independently() -> None:
    run_import_check(
        "from ecobiome.reasoning.diagnostic_pipeline import "
        "DiagnosticInvestigationPipeline"
    )


def test_quality_contract_does_not_load_reasoning_package() -> None:
    run_import_check(
        "import sys; "
        "from ecobiome.contracts.quality_rule import QualityRule; "
        "assert 'ecobiome.reasoning' not in sys.modules; "
        "assert QualityRule is not None"
    )
