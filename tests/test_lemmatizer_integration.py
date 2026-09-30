"""Optional integration checks against the installed LemmInflect resources."""

import pytest

pytest.importorskip("lemminflect")

from lemminflect import getAllLemmas

from lexisift.analysis.lemmatizer import build_lemma_map


def test_real_lemminflect_avoids_observed_false_merges() -> None:
    vocabulary = {
        "even", "evening",
        "think", "thinks", "thinking",
        "develop", "develops", "developed",
        "play", "plays", "playing",
        "leave", "leaving", "leaves", "left",
        "see", "saw",
        "gone",
        "it's", "its",
    }
    mapping = build_lemma_map(vocabulary)

    assert mapping["evening"] == "evening"
    assert mapping["thinking"] == "think"
    assert mapping["developed"] == "develop", (
        "LemmInflect diagnostics: "
        f"develop={getAllLemmas('develop')!r}, "
        f"develops={getAllLemmas('develops')!r}, "
        f"developed={getAllLemmas('developed')!r}"
    )
    assert mapping["playing"] == "play"
    assert mapping["leaves"] == "leaves"
    assert mapping["left"] == "left"
    assert mapping["saw"] == "saw"
    assert mapping["gone"] == "go"
    assert mapping["it's"] == "it's"
