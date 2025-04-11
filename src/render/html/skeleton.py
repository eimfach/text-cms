from yattag import Doc, indent
import os
import datetime
import re
from render.html.components import pagehero, chapterindex, chapter, like


def htmldocument(document, verbose):
    filename = document.file_name
    features = document.features
    data = document.content
    related_topics = document.related_topics
    
    responsivecss = open(
        os.getcwd() + "/../stylesheets/inline/responsive.css").read()
    fontcss = open(os.getcwd() + "/../stylesheets/inline/font.css").read()
    iconfontcss = open(os.getcwd() + "/../fonts/styles.css").read()
    criticalpathcss = os.getcwd() + "/../stylesheets/inline/critical/" + \
        filename + ".css"

    try:
        criticalpathcss = open(criticalpathcss).read()

    except:
        if (verbose):
            print(f"[WARNING]: Critical CSS File not found: {filename}.css")

    printcss = open(os.getcwd() + "/../stylesheets/print.css").read()

    packedinlinecss = "\n" + fontcss + "\n\n" + iconfontcss + \
        "\n\n" + criticalpathcss + "\n\n" + responsivecss

    packedjspath = assetpipeline("journal.js",
                                 "js/modules/polyfills.js",
                                 "js/modules/startup.js",
                                 "js/modules/subscriptions.js",
                                 "js/modules/chapterindex.js",
                                 "js/modules/articleupdatehint.js",
                                 "js/modules/gallery.js",
                                 "js/modules/feedback.js",
                                 "js/modules/likesubmit.js")

    doc = Doc()
    tag, text, stag, line, asis = doc.tag, doc.text, doc.stag, doc.line, doc.asis

    asis("<!DOCTYPE html>")
    with tag("html", lang="en"):
        with tag("head"):

            stag("meta", charset="utf-8")
            stag("meta", ("http-equiv", "X-UA-Compatible"), content="chrome=1")
            stag("meta", name="viewport", content="width=device-width")
            stag("meta", name="description", content=data.meta.description)
            stag("meta", name="keywords", content=data.meta.keywords)
            stag("meta", name="author", content=data.meta.author)
            stag("link", rel="icon", type="image/svg+xml",
                 href="/img/favicon-5.svg")

            with tag("style"):
                asis(packedinlinecss)

            asis(
                "<!--[if lt IE 9]><script src=\"//html5shiv.googlecode.com/svn/trunk/html5.js\"></script><![endif]-->")

            line("title", data.meta.title)

        with tag("body"):

            if features["related-topics"] and len(related_topics) > 0:
                with tag("div", id="side-pane", klass="journal"):
                    line("h4", "Related Topics")

                    for t in related_topics:
                        with tag("div", klass="post-item"):
                            line("a", t["title"],
                                 href=t["href"])

            with tag("div", id="content"):
                pagehero(
                    doc,
                    introduction=data.introduction,
                    topic=data.meta.title,
                    author=data.meta.author,
                    website=data.meta.website,
                    enable_subscriptions=features["subscriptions"])

                with doc.tag("section", klass="projects"):
                    journalcontent(doc, data, features)

                with doc.tag("div", klass="center  margin-top-40"):
                    with doc.tag("a", href="/", title="robingruenke.com"):
                        with doc.tag("span", klass="icon-home-house-streamline colorful-font font-big"):
                            doc.text("")

                with doc.tag("div", klass="center"):
                    doc.line("small", copyright(data))

    stag("link", href="/stylesheets/styles.css", rel="stylesheet")
    stag("link", href="/stylesheets/print.css", rel="stylesheet", media="print")
    line("script", "", src=packedjspath)

    return doc


def journalcontent(doc, data, features):
    # render chapter index
    if features["chapter-index"] and len(data.items) > 2:
        ids = [getnormalizedtopic(chapter.topic)
               for chapter in data.items]
        chapterindex(doc, data.items, ids=ids)

    doc.line("div", "", klass="pagebreak")

    for i in data.items:
        html_id = getnormalizedtopic(i.topic)
        chapter(doc, html_id, i, features)

    if features["missing-chapters-hint"] and len(data.items) < 3:
        with doc.tag("blockquote", klass="last no-border margin-top-40", id="more-info"):
            doc.text(("Note: Wonder where the rest of the article is ? "
                      " In my Journal articles, I write and publish small chapters."
                      " Every now and then I add a new chapter. Just come back later !"))

    if features["journal-like"]:
        like(doc, data.meta.title)


def getnormalizedtopic(s):
    return "-".join(re.findall(r"\w+", s)).lower()


def copyright(data):
    sl = [
        "Copyright ",
        str(data.meta.year),
        "-",
        str(datetime.datetime.now().year),
        " Robin T. Gruenke"
    ]
    return "".join(sl)


def assetpipeline(prod_filename, *assets):
    prod_file_type = prod_filename.split(".")[1]

    assets_content = ""
    for asset in assets:
        assets_content = assets_content + \
            open(os.path.join(os.getcwd(), "..", asset)).read() + "\n\n"

    if prod_file_type == "js":
        prod_filepath = os.path.join("js", "dist", prod_filename)
        file = open(os.path.join(os.getcwd(), "..", prod_filepath), "w")
        prod_template = open(os.path.join(
            os.getcwd(), "..", "js", "prod_template.js"))

        prod_content = "// auto generated, don't modify \n\n"
        for line in prod_template:
            if re.search(r"^//{modules}", line):
                prod_content = prod_content + assets_content + "\n\n"
            else:
                prod_content = prod_content + line

        file.write(prod_content)
        file.close()

        return "/" + prod_filepath

    else:
        raise TypeError(
            "assetPipeline: Unsupported filetype: " + prod_file_type)
