import os
from argparse import ArgumentParser
from cProfile import runctx
from glob import glob
from sys import exit
from typing import List

from yattag import indent

from journalparser import parse
from model import Article
from render.html.skeleton import htmldocument
from seo import extract_nouns, most_common_words_histogram


def main(args):
    features = {"feedback": True, "journal-like": True,
                "interactive-example": True, "related-topics": True,
                "missing-chapters-hint": True, "chapter-index": True,
                "subscriptions": False
                }

    documents, parser_err = parse_documents(
        files(args), features, args.verbose)

    if parser_err:
        exit(1)

    set_recommended_keywords(documents, args)

    print_keywords_intel(args.verbose)

    set_related_topics(documents, args.verbose)

    render(documents, args.verbose)

    print(CliFormat.dim("Done."))


def files(args):
    if args.file:
        return [args.file]
    else:
        return glob("../journal/**/*.journal", recursive=True)


def parse_documents(files, features, verbose):
    docs = []
    append_doc = docs.append
    parser_err = False

    for path in files:
        content = None
        with open(path) as f:
            for content, err in parse(f):
                if err:
                    print(r"    - " + err)

                    if not verbose:
                        break

        if not content:
            print_parser_fail(path)
            parser_err = True
            continue

        append_doc(Document(path, features, content))

    return docs, parser_err


def render(documents, verbose):
    for document in documents:
        htmlfile = document.file_path
        with open(htmlfile, "w") as f:
            html = htmldocument(document, verbose)
            f.write(indent(html.getvalue()))


def set_recommended_keywords(documents, args):
    for document in documents:
        n = extract_nouns(document.content_text())
        h = most_common_words_histogram(" ".join(n))
        document.recommended_keywords = h

        print_found_common_keywords(
            document.file_name, h, verbose=args.verbose)
        print_more_keyword_info(document, verbose=args.verbose)


def set_related_topics(documents, verbose):
    for document in documents_valid_as_related(documents):
        rts = document.related_topics
        append_topic = rts.append
        sort_topics = rts.sort

        for other_doc in documents_valid_as_related(documents):
            if other_doc is document:
                continue

            mi = document.keywords_match_index(other_doc)
            if mi <= 8:
                append_topic(dict(
                    match_index=mi,
                    title=other_doc.content.meta.title,
                    href=other_doc.href))

        sort_topics(key=lambda t: t["match_index"])

        print_related_topics(document, verbose)


class CliFormat:
    @ classmethod
    def bold(cls, s):
        return cls._end_format("\033[4m", s)

    @ classmethod
    def green(cls, s):
        return cls._end_format("\033[92m", s)

    @ classmethod
    def dim(cls, s):
        return cls._end_format("\033[90m", s)

    @ classmethod
    def red(cls, s):
        return cls._end_format("\033[91m", s)

    @ classmethod
    def _end_format(cls, f, s):
        return "".join([f, s, "\033[0m"])


class Document():
    def __init__(self, path, features, content: Article):
        file_dir, file_name = os.path.split(path)

        doc_features = features.copy()
        if content.meta.opt_out:
            for feature in content.meta.opt_out.split(" "):
                doc_features[feature] = False

        self.prod_dir = file_dir.split("..")[1]
        self.file_dir = file_dir
        self.file_name = file_name.split(".")[0]
        self.content = content
        self.features = doc_features
        self.recommended_keywords = []
        self.related_topics = []
        self._content_keywords = content.meta.keywords.split(" ")

    def content_keywords_match_recommended(self):
        return self._content_keywords == self.r_keywords_flat()

    def content_text(self):
        sl = [self.content.meta.title]
        append = sl.append

        for item in self.content.items:
            append(item.topic)
            sl += [p.content for p in item.paragraphs if p.type == "text"]

        return " ".join(sl)

    @ property
    def file_path(self) -> str:
        return os.path.join(self.file_dir, self.file_name + ".html")

    @ property
    def href(self) -> str:
        return os.path.join(self.prod_dir, self.file_name + ".html")

    def is_valid_as_related_topic(self):
        return self.content_keywords_match_recommended() \
            and len(self.r_keywords_uncommon()) == 0

    def keywords_match_index(self, document):
        keywords = self._content_keywords
        other_keywords = document._content_keywords
        return len(set(keywords + other_keywords))

    def r_keywords_flat(self) -> List[str]:
        return [k for k, v in self.recommended_keywords]

    def r_keywords_uncommon(self) -> List[str]:
        return [k for k, v in self.recommended_keywords if v < 5]


###########################################
################# HELPERS #################
###########################################


def cli_arguments():
    ap = ArgumentParser()
    ap.add_argument("-v", "--verbose", action="store_true", default=False,
                    help="Show all errors")
    ap.add_argument("-p", "--performance", action="store_true", default=False,
                    help="Show performance analysis")
    ap.add_argument("-f", "--file", help="Parse this file only")
    return ap.parse_args()


def documents_valid_as_related(documents: List[Document]):
    return [d for d in documents if d.is_valid_as_related_topic()]


def print_parser_fail(file_name):
    print("Parsing failed: " + file_name)


def print_found_common_keywords(entity, kws, verbose):
    if not verbose:
        return

    print()
    print(CliFormat.bold(entity + ":"))
    print(CliFormat.dim("  > Found these common keywords:"))
    print("    " + CliFormat.dim(str(kws)))


def print_keywords_intel(verbose):
    if not verbose:
        return

    print()
    a = CliFormat.dim("(1)(2)")
    i = f"[i] Keywords: Use five nouns{a}"
    ii = ("at least five times each which are cohesive"
          " with the documents topic.")

    print(CliFormat.green(i), CliFormat.green(ii))
    print(CliFormat.dim("(1) common, singular or mass (2) proper, singular"))
    print()


def print_keywords_not_matching(s):
    print(
        CliFormat.red("  X"),
        "Recommended keywords not matching set document keywords:",
        CliFormat.dim(s))


def print_more_keyword_info(doc: Document, verbose):
    if not verbose:
        return

    urkws = doc.r_keywords_uncommon()

    if len(urkws) > 1:
        k = ", ".join(urkws)
        print_uncommon_keywords(k)

    if not doc.content_keywords_match_recommended():
        print_keywords_not_matching(doc.content.meta.keywords)


def print_related_topics(doc: Document, verbose):
    if not verbose or len(doc.related_topics) == 0:
        return

    print()
    print(CliFormat.bold(doc.file_name))
    print(CliFormat.dim("  > Found these related topics:"))
    for topic in doc.related_topics:
        print(CliFormat.dim("    " + str(topic)))


def print_uncommon_keywords(k):
    print(
        CliFormat.red("  X"),
        f"Recommended keywords \"{k}\" are not common enough (use 5 times each).")


if __name__ == "__main__":
    args = cli_arguments()
    if args.performance:
        runctx("main(args)", globals(), locals())
    else:
        main(args)
