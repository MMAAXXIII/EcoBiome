"""Tests for the Project and Study domain models."""

import pytest

from ecobiome.core import Project, Study, StudyOrigin


def test_project_can_contain_an_existing_ecosystem_study() -> None:
    project = Project(name="Étude des mares locales")
    study = Study(
        name="Mare forestière",
        origin=StudyOrigin.EXISTING,
    )

    project.add_study(study)

    assert project.name == "Étude des mares locales"
    assert project.studies == [study]
    assert study.origin is StudyOrigin.EXISTING


def test_project_rejects_duplicate_study() -> None:
    project = Project(name="Mon jardin")
    study = Study(name="Bassin actuel", origin=StudyOrigin.EXISTING)

    project.add_study(study)

    with pytest.raises(ValueError, match="already part"):
        project.add_study(study)


def test_study_requires_a_name() -> None:
    with pytest.raises(ValueError, match="non-empty name"):
        Study(name="   ", origin=StudyOrigin.HYPOTHETICAL)