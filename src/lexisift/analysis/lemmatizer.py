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
# Surface forms whose dictionary analysis can vary across LemmInflect resource
# versions and whose meanings map to genuinely different lemmas. Without
# token-level POS/context, preserve them exactly rather than letting a regular
# spelling relation choose one sense.
_AMBIGUOUS_SURFACES: frozenset[str] = frozenset({
    "leaves",  # plural leaf / verb leave
    "lives",   # plural life / verb live
})


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
    """Return the preferred dictionary lemma for each POS reading.

    LemmInflect can return multiple ordered lemma candidates for one POS. For
    example, ``developed`` may produce ``("develop", "develope")`` for
    VERB. Treating every fallback spelling as an equally plausible lemma creates
    false ambiguity. LexiSift therefore keeps only the first (preferred) lemma
    per POS while still preserving genuine cross-POS ambiguity such as
    ``leaves`` -> NOUN ``leaf`` / VERB ``leave``.
    """

    candidates: set[str] = set()
    for spellings in _dictionary_lemmas(word).values():
        if spellings:
            candidates.add(spellings[0])
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


def _build_spelling_candidates(
    words: Collection[str],
    dictionary_candidates_by_word: Mapping[str, frozenset[str]],
) -> dict[str, frozenset[str]]:
    """Return regular-inflection candidates supported by book and dictionary data.

    The index is derived from vocabulary items already present in the book rather
    than from LemmInflect's analysis of the inflected surface. This makes regular
    family grouping stable across lexical-resource quirks. For example, even if
    a dictionary lists ``developed`` only as an adjective lemma, the simultaneous
    presence of ``develop`` and ``develops`` still provides spelling evidence for
    the ``develop`` family.
    """

    vocabulary = set(words)
    reverse: dict[str, set[str]] = {word: set() for word in vocabulary}

    # First derive relations from base-looking vocabulary items that actually
    # occur in the book. This path is intentionally independent of how a
    # particular LemmInflect resource classifies the inflected surface.
    for lemma in vocabulary:
        for form in _regular_inflections(lemma):
            if form in vocabulary and form != lemma:
                reverse[form].add(lemma)

    # Also accept dictionary lemmas that have a direct regular spelling relation
    # even when the base form itself is absent from the book (runs + running ->
    # run). Selection still requires corroboration for lexicalized/ambiguous
    # surfaces, so this does not reintroduce blind stemming.
    for word in vocabulary:
        for lemma in dictionary_candidates_by_word[word]:
            if lemma != word and _is_regular_inflection(word, lemma):
                reverse[word].add(lemma)

    return {word: frozenset(lemmas) for word, lemmas in reverse.items()}


def _dictionary_is_ambiguous(
    word: str,
    dictionary_candidates: frozenset[str],
    spelling_candidates: frozenset[str],
) -> bool:
    """Return whether dictionary evidence exposes competing non-self lemmas.

    A surface such as ``leaves`` can mean a form of either ``leaf`` or ``leave``.
    Even if only one of those base lemmas happens to occur elsewhere in the book,
    LexiSift must not force every occurrence into that family without token-level
    POS/context.
    """

    nonself = {lemma for lemma in dictionary_candidates if lemma != word}
    if len(nonself) > 1:
        return True
    if nonself and spelling_candidates and not nonself.issubset(spelling_candidates):
        return True
    return False


def _support_counts(
    words: Collection[str],
    spelling_candidates_by_word: Mapping[str, frozenset[str]],
    dictionary_candidates_by_word: Mapping[str, frozenset[str]],
) -> Counter[str]:
    """Count independent high-confidence spelling evidence for lemma families.

    Regular spelling relations are derived from base lemmas that actually occur
    in the book. A surface contributes one vote only when it points to exactly one
    base and the morphology dictionary does not expose a competing lemma. This
    lets ``developed`` + ``develops`` corroborate ``develop`` even when a specific
    LemmInflect build lexicalizes ``developed`` as an adjective, while ambiguous
    forms such as ``leaves`` do not vote for either ``leaf`` or ``leave``.
    """

    support: Counter[str] = Counter()
    for word in words:
        if word in _IRREGULAR_LEMMAS:
            support[_IRREGULAR_LEMMAS[word]] += 1
            continue

        spelling = spelling_candidates_by_word[word]
        dictionary = dictionary_candidates_by_word[word]
        if len(spelling) != 1 or _dictionary_is_ambiguous(word, dictionary, spelling):
            continue
        support[next(iter(spelling))] += 1
    return support


def _select_lemma(
    word: str,
    base: str,
    dictionary_candidates: frozenset[str],
    spelling_candidates: frozenset[str],
    support: Counter[str],
) -> str:
    """Select a high-confidence lemma for one surface word."""

    if "'" in word and is_stopword(word):
        return word

    if word in _IRREGULAR_LEMMAS:
        return _IRREGULAR_LEMMAS[word]

    if word in _AMBIGUOUS_SURFACES:
        return base

    # Lexical possessives are safe independently of morphology/POS.
    if base != word:
        return _IRREGULAR_LEMMAS.get(base, base)

    if not spelling_candidates:
        return base

    if _dictionary_is_ambiguous(word, dictionary_candidates, spelling_candidates):
        return base

    if len(spelling_candidates) != 1:
        return base
    lemma = next(iter(spelling_candidates))

    # If the surface is itself lexicalized as a dictionary lemma (for example
    # ``evening``), require another independent regular surface from this book to
    # corroborate the family. The current surface contributes one support vote,
    # so >=2 means at least one sibling exists. This rule is intentionally based
    # on spelling evidence, not on whether a particular LemmInflect build also
    # returns the base lemma for this exact surface.
    if base in dictionary_candidates and support[lemma] < 2:
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

    # Without book context there is no reverse vocabulary index, so keep regular
    # forms unchanged rather than guessing from a single surface token. Safe
    # irregulars and possessives above are still resolved.
    return base


def build_lemma_map(vocabulary: Collection[str]) -> dict[str, str]:
    """Return a conservative surface-form to lemma mapping for one book."""

    words = tuple(sorted(set(vocabulary)))
    bases = {word: _base_for_lookup(word) for word in words}
    dictionary_candidates_by_word = {
        word: frozenset({bases[word]})
        if "'" in word and is_stopword(word)
        else _candidate_set(bases[word])
        for word in words
    }
    spelling_candidates_by_word = _build_spelling_candidates(
        words, dictionary_candidates_by_word
    )
    support = _support_counts(
        words,
        spelling_candidates_by_word,
        dictionary_candidates_by_word,
    )

    return {
        word: _select_lemma(
            word,
            bases[word],
            dictionary_candidates_by_word[word],
            spelling_candidates_by_word[word],
            support,
        )
        for word in words
    }
