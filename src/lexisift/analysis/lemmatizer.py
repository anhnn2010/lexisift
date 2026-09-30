"""Conservative English word-family grouping backed by LemmInflect."""

from __future__ import annotations

from collections import Counter
from collections.abc import Collection, Mapping
from functools import lru_cache

from lexisift.analysis.stopwords import is_stopword

# Prefer correctness over recall. These irregulars are deliberately curated:
# LexiSift only groups an irregular surface when the relationship is safe without
# contextual POS tagging. Ambiguous homographs such as ``left``/``leave`` are
# intentionally absent and therefore remain separate vocabulary items.
_IRREGULAR_LEMMAS: dict[str, str] = {
    "best": "good",
    "better": "good",
    "children": "child",
    "feet": "foot",
    "gone": "go",
    "made": "make",
    "men": "man",
    "teeth": "tooth",
    "went": "go",
    "women": "woman",
    "worse": "bad",
    "worst": "bad",
}


@lru_cache(maxsize=32768)
def _dictionary_lemmas(word: str) -> Mapping[str, tuple[str, ...]]:
    """Return dictionary lemmas by universal POS without OOV guessing.

    LemmInflect ships its lexical resources with the package. ``getAllLemmas`` is
    deliberately used instead of its OOV rule system: LexiSift would rather leave
    an uncommon word ungrouped than manufacture a false lemma.
    """

    from lemminflect import getAllLemmas

    raw = getAllLemmas(word)
    return {
        pos: tuple(candidate.casefold() for candidate in candidates if candidate)
        for pos, candidates in raw.items()
    }


def _strip_lexical_possessive(word: str) -> str:
    """Strip lexical possessives while preserving stop-word contractions."""

    if word.endswith("'s") and len(word) > 2 and not is_stopword(word):
        return word[:-2]
    return word


def _candidate_set(word: str) -> frozenset[str]:
    """Return all dictionary lemmas for a surface form."""

    candidates: set[str] = set()
    for spellings in _dictionary_lemmas(word).values():
        candidates.update(spellings)
    return frozenset(candidates)


def _base_for_lookup(word: str) -> str:
    """Return the lexical token passed to the morphology dictionary."""

    # A contraction is a complete surface token for LexiSift. Mapping ``it's``
    # to ``its`` or ``don't`` to ``do`` damages vocabulary auditing, while these
    # tokens are already handled as stop words.
    if "'" in word and is_stopword(word):
        return word
    return _strip_lexical_possessive(word)


def _regular_inflections(lemma: str) -> frozenset[str]:
    """Return conservative regular English inflections for ``lemma``.

    This helper intentionally covers only productive, high-confidence spelling
    patterns. It is not a stemmer. Irregular forms are handled solely by the
    curated map above so homographs such as ``left`` never become ``leave`` just
    because a morphology dictionary exposes that verbal reading.
    """

    forms: set[str] = set()
    if not lemma or not lemma.isalpha():
        return frozenset()

    # Plural nouns / third-person singular verbs.
    forms.add(f"{lemma}s")
    forms.add(f"{lemma}es")
    if len(lemma) > 1 and lemma.endswith("y") and lemma[-2] not in "aeiou":
        forms.add(f"{lemma[:-1]}ies")

    # Regular past tense / past participle.
    if lemma.endswith("e"):
        forms.add(f"{lemma}d")
    elif len(lemma) > 1 and lemma.endswith("y") and lemma[-2] not in "aeiou":
        forms.add(f"{lemma[:-1]}ied")
    else:
        forms.add(f"{lemma}ed")

    # Present participle / gerund.
    if lemma.endswith("ie"):
        forms.add(f"{lemma[:-2]}ying")
    elif lemma.endswith("e") and not lemma.endswith(("ee", "ye", "oe")):
        forms.add(f"{lemma[:-1]}ing")
    else:
        forms.add(f"{lemma}ing")

    # Common final-consonant doubling (run -> running, stop -> stopped). We keep
    # this deliberately mechanical; dictionary candidates still gate the result.
    if (
        len(lemma) >= 3
        and lemma[-1].isalpha()
        and lemma[-1] not in "aeiouwxy"
        and lemma[-2] in "aeiou"
        and lemma[-3] not in "aeiou"
    ):
        forms.add(f"{lemma}{lemma[-1]}ed")
        forms.add(f"{lemma}{lemma[-1]}ing")

    return frozenset(forms)


def _is_regular_inflection(word: str, lemma: str) -> bool:
    """Return whether ``word`` is a conservative regular inflection of ``lemma``."""

    return word in _regular_inflections(lemma)


def _eligible_regular_candidates(word: str, candidates: frozenset[str]) -> frozenset[str]:
    """Return dictionary candidates supported by a regular spelling relation."""

    return frozenset(
        lemma
        for lemma in candidates
        if lemma != word and _is_regular_inflection(word, lemma)
    )


def _support_counts(
    bases: Mapping[str, str],
    candidates_by_word: Mapping[str, frozenset[str]],
) -> Counter[str]:
    """Count independent high-confidence evidence for lemma candidates.

    Only an unambiguous *regular* inflection or a curated safe irregular votes.
    Merely seeing a dictionary relation such as ``left -> leave`` contributes no
    evidence because that transformation is neither regular nor explicitly safe.
    """

    support: Counter[str] = Counter()
    for word, base in bases.items():
        if word in _IRREGULAR_LEMMAS:
            support[_IRREGULAR_LEMMAS[word]] += 1
            continue

        candidates = candidates_by_word[word]
        eligible = _eligible_regular_candidates(base, candidates)
        # A form that is itself a dictionary lemma is ambiguous and must not
        # vote for one of its own alternate readings (evening -> even).
        if base not in candidates and len(candidates) == 1 and len(eligible) == 1:
            support[next(iter(eligible))] += 1
    return support


def _select_lemma(
    word: str,
    base: str,
    candidates: frozenset[str],
    support: Counter[str],
) -> str:
    """Select a high-confidence dictionary lemma for one surface word."""

    if "'" in word and is_stopword(word):
        return word

    if word in _IRREGULAR_LEMMAS:
        return _IRREGULAR_LEMMAS[word]

    # Lexical possessives are safe independently of morphology/POS.
    if base != word:
        return _IRREGULAR_LEMMAS.get(base, base)

    if not candidates:
        return base

    eligible = _eligible_regular_candidates(base, candidates)
    if not eligible:
        return base

    # If the surface itself is also a dictionary lemma (e.g. evening), only map
    # it when another independent inflected form in this book supports exactly
    # one candidate. This favors false negatives over false family merges.
    if base in candidates:
        supported = [lemma for lemma in eligible if support[lemma] >= 1]
        if len(supported) != 1:
            return base
        lemma = supported[0]
    elif len(candidates) == 1 and len(eligible) == 1:
        lemma = next(iter(eligible))
    else:
        # If a non-lemma surface has multiple distinct dictionary analyses
        # (e.g. leaves -> leaf/leave, lives -> life/live), token-level POS is
        # required to choose safely. Keep the surface form instead of forcing
        # the whole book into one family.
        return base

    if not is_stopword(word) and is_stopword(lemma):
        return base
    return lemma


def lemmatize_word(word: str, vocabulary: Collection[str] | None = None) -> str:
    """Return a conservative dictionary lemma for one normalized token.

    When a complete book vocabulary is supplied, LexiSift can use independent
    word-family evidence to resolve some otherwise ambiguous regular forms.
    Without that context, ambiguous forms are deliberately left unchanged.
    """

    if vocabulary is not None:
        return build_lemma_map(vocabulary)[word]

    base = _base_for_lookup(word)
    if "'" in word and is_stopword(word):
        return word
    if word in _IRREGULAR_LEMMAS:
        return _IRREGULAR_LEMMAS[word]
    if base != word:
        return _IRREGULAR_LEMMAS.get(base, base)

    candidates = _candidate_set(base)
    eligible = _eligible_regular_candidates(base, candidates)
    if base not in candidates and len(candidates) == 1 and len(eligible) == 1:
        lemma = next(iter(eligible))
        if not is_stopword(word) and is_stopword(lemma):
            return base
        return lemma
    return base


def build_lemma_map(vocabulary: Collection[str]) -> dict[str, str]:
    """Return a conservative surface-form to lemma mapping for one book."""

    words = tuple(sorted(set(vocabulary)))
    bases = {word: _base_for_lookup(word) for word in words}
    candidates_by_word = {
        word: frozenset({bases[word]})
        if "'" in word and is_stopword(word)
        else _candidate_set(bases[word])
        for word in words
    }
    support = _support_counts(bases, candidates_by_word)

    return {
        word: _select_lemma(word, bases[word], candidates_by_word[word], support)
        for word in words
    }
