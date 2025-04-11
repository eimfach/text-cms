from seo import extract_nouns, most_common_words_histogram


def test_extract_nouns():
    s = ("A python is going to speak to other pythons at Liverpool"
         " while other pythons are swimming in the river [ ].")
    expected = ["python", "Liverpool", "river"]
    r = extract_nouns(s)
    assert r == expected


def test_word_histogram():
    s = ("some some some python python river")
    r = most_common_words_histogram(s)
    expected = [("some", 3), ("python", 2), ("river", 1)]
    assert r == expected
