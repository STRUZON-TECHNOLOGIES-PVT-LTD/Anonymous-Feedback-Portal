"""Unit tests for the dependency-free name-extraction heuristic."""

from app.name_extraction import extract_names, normalize_name


class TestExtractNames:
    def test_single_name(self):
        assert extract_names("John never listens.") == ["John"]

    def test_leading_name(self):
        assert extract_names("Priya was great this month.") == ["Priya"]

    def test_sentence_initial_stopwords_filtered(self):
        assert extract_names("Please fix this. The team is great.") == []
        assert extract_names("However nobody showed up.") == []

    def test_short_names_skipped(self):
        assert extract_names("Al is great") == []

    def test_contractions_are_not_names(self):
        assert extract_names("I'm very happy with the team.") == []
        assert extract_names("We're on track for the deadline.") == []
        assert extract_names("It's been a good month.") == []
        assert extract_names("That's what I meant.") == []

    def test_possessive_kept_but_normalized(self):
        assert extract_names("John's team did great work.") == ["John's"]
        assert normalize_name("John's") == "john"
        assert normalize_name("John") == "john"

    def test_possessive_dedupes_with_plain(self):
        assert extract_names("John is great. John's work is solid.") == ["John"]

    def test_multi_name_run(self):
        assert extract_names("Maria and Pedro joined.") == ["Maria", "Pedro"]

    def test_punctuation_suffix_stripped(self):
        assert extract_names("Please contact John!") == ["John"]

    def test_apostrophe_name_kept(self):
        assert extract_names("O'Brien handled the incident.") == ["O'Brien"]

    def test_dedupe_case_insensitive(self):
        assert extract_names("Alice. Alice again.") == ["Alice"]

    def test_empty_and_whitespace(self):
        assert extract_names("") == []
        assert extract_names(None) == []
        assert extract_names("   ") == []

    def test_lowercase_mention_ignored(self):
        assert extract_names("john never listens.") == []


class TestNormalizeName:
    def test_possessive_stripped(self):
        assert normalize_name("James'") == "james'"
        assert normalize_name("James's") == "james"
        assert normalize_name("Chris") == "chris"

    def test_case_folded(self):
        assert normalize_name("McArthur") == "mcarthur"

    def test_plain_names_unchanged_beyond_case(self):
        assert normalize_name("Adam") == "adam"