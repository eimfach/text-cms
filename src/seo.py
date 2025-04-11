from nltk import FreqDist, word_tokenize, pos_tag


def extract_nouns(s):
    ft = ["NN", "NNP"]
    t = word_tokenize(s)
    tags = pos_tag(t)
    tags = [t for t in tags if t[0].isalpha()]
    return [word for word, pos in tags if pos in ft]


def most_common_words_histogram(s):
    tokens = word_tokenize(s)
    return FreqDist(tokens).most_common(5)
