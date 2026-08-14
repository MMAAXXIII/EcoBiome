"""Exact Medaka fixture identity boundary; bundles injected by runtime gate."""
from __future__ import annotations

import hashlib
import json
import os
import zipfile
from pathlib import Path

import pytest

R3_SHA256="ade59888c854a1a68003158f7ff30de80c6cd28cdc92923355b25735708648fe"
GOLDEN_SHA256="1c79d1da92dabd741da0b8d33598e972f87afe72eb537ed1d23f35864d11d710"
RAW_SHA256="a5035cde0ed62495108a2c61fd667fc0740cc20879b79d18f73e49a4668de1ce"
def _sha(path:Path)->str: return hashlib.sha256(path.read_bytes()).hexdigest()
def _inputs()->tuple[Path,Path]:
    r3=os.environ.get("ECOBIOME_MEDAKA_R3_ZIP"); golden=os.environ.get("ECOBIOME_MEDAKA_GOLDEN_ZIP")
    if not r3 or not golden: pytest.skip("Exact Medaka bundles injected by dedicated off-repo runtime gate")
    return Path(r3),Path(golden)
def test_exact_medaka_external_fixture_identity()->None:
    r3,golden=_inputs(); assert _sha(r3)==R3_SHA256; assert _sha(golden)==GOLDEN_SHA256
    with zipfile.ZipFile(r3) as a:
        raw=a.read("RAW_ARTIFACT_PLOS_JATS.xml")
        segments=json.loads(a.read("DERIVED_JATS_TEXT_SEGMENTS.json").decode())
    with zipfile.ZipFile(golden) as a:
        claims=json.loads(a.read("MEDAKA_PROVIDER_BLIND_SOURCE_CLAIMS_GOLDEN_V1.json").decode())
        evidence=json.loads(a.read("MEDAKA_GOLDEN_EVIDENCE_SPANS_V1.json").decode())
    assert hashlib.sha256(raw).hexdigest()==RAW_SHA256
    assert segments["segment_count"]==172
    assert claims["claim_count"]==6
    assert evidence["evidence_count"]==6
    assert sum(x["golden_key"]!="G1_STUDY_PERIOD" for x in claims["claims"])==5

def test_medaka_v11_semantic_rewrite_boundary() -> None:
    expected = {
        "G1_STUDY_PERIOD": None,
        "G2_EGG_HANGING_TIMES": "event",
        "G3_APPEARANCE_GAMM": "temporal_pattern",
        "G4_SWIMMING_GAMM": "temporal_pattern",
        "G5_FOLLOWING_GAMM": "temporal_pattern",
        "G6_SCOPED_MIDNIGHT_CONCLUSION": "temporal_pattern",
    }
    assert sum(kind is not None for kind in expected.values()) == 5
    assert expected["G1_STUDY_PERIOD"] is None
    assert "interpretive_conclusion" not in {kind for kind in expected.values() if kind}
