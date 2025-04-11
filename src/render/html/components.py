from calendar import month_abbr
from os import getcwd
from re import findall, search, split
import numpy


def pagehero(doc, introduction, topic, author, website, enable_subscriptions=False):
    with doc.tag("div", klass="heading-container"):
        with doc.tag("h1", klass="content-heading", id="pagetitle", style="margin-bottom: 5px"):
            with doc.tag("span", klass="icon-ink-pen-streamline colorful-font"):
                doc.text("")
            doc.text(" " + topic)

        with doc.tag("p", klass="center", id="journal-topic-author"):
            with doc.tag("small"):
                doc.text(" Journal Topic of ")
                with doc.tag("a", href=website, title=author):
                    doc.text(author)
                if enable_subscriptions:
                    doc.text(" 〜 ")
                    with doc.tag("a",
                                 href="javascript: window.robingruenkedotcom.subscribe();",
                                 style="display: none;", id="user-sub", klass="pending"):
                        doc.text("Subscribe")

        intro(doc, introduction)


def chapter(doc, html_id, chapter, features):
    with doc.tag("section", klass="project chapter", id=html_id):

        picture = chapter.picture
        gallery = chapter.gallery
        heading = chapter.topic
        author = chapter.author
        date = chapter.date
        quote = chapter.quote
        paragraphs = chapter.paragraphs
        appndx = chapter.appendix

        if picture:
            klass = "item project-text read-width-optimized"

            if gallery:
                klass = klass + " gallery-background no-padding"
            else:
                klass = klass + " no-border"

            with doc.tag("div", klass=klass):
                doc.stag("img", loading="lazy", klass="main-image",
                         src=picture.src,
                         style="display: block; max-height: " + picture.height)

                if gallery:
                    segmented_pictures = numpy.array(
                        gallery.items).reshape(-1, 3)

                    for gallery_segment in segmented_pictures:
                        with doc.tag("div", klass="gallery-container"):
                            for gallerypicture in gallery_segment:
                                doc.stag("img", loading="lazy",
                                         klass="gallery-picture",
                                         src=gallerypicture,
                                         style="max-height: " + gallery.height)

        with doc.tag("h2", klass="meta-block"):

            doc.text(heading)
            doc.stag("br")
            doc.line("small", create_better_date(date),
                     klass="meta", id=html_id + "-date")
            doc.line("small", " - " + author,
                     klass="meta", id=html_id + "-author")

        with doc.tag("div", klass="item project-text read-width-optimized"):

            if quote:
                with doc.tag("blockquote", klass="padding-top-20 padding-bottom-20 last clear"):
                    with doc.tag("span"):
                        doc.line("span", quote.content)
                    with doc.tag("a", href=quote.reference):
                        doc.text(quote.content)

            chapter_content(doc, paragraphs)

            if features["interactive-example"] and chapter.interactive_example:
                path = [
                    getcwd(),
                    "/../",
                    chapter.interactive_example,
                    "/index.html"
                ]
                html = open("".join(path)).read()

                with doc.tag("div", klass="interactive-example margin-top-40 margin-bottom-40"):
                    doc.asis(html)

            with doc.tag("div", klass="chapter-footer"):
                if appndx:
                    appendix(doc, appndx)

                if features["feedback"]:
                    if not appndx:
                        doc.attr(klass="chapter-footer feedback-only")

                    feedback_button(doc, idparent=html_id, topic=heading)

            if features["feedback"]:
                feedback_form(doc, idparent=html_id, topic=heading)

    doc.line("div", "", klass="pagebreak")


def chapter_content(doc, paragraphs):
    for paragraph in paragraphs:
        if paragraph.type == "text":
            content = paragraph.content

            with doc.tag("p"):
                if search(r"^Note:", content):
                    content = content.replace("Note:", "")
                    doc.line("span", "Note", klass="note")
                    doc.line("i", content)
                elif search(r"^- \[.*?\]", content):
                    checkboxcontent = findall(r"^- \[(.+?)\]", content)[0]

                    if search(r" ", checkboxcontent):
                        doc.stag("input", "", type="checkbox",
                                 disabled="true", klass="inline-checkbox")
                    elif search(r"x", checkboxcontent):
                        doc.stag("input", "", type="checkbox", checked="true",
                                 disabled="true", klass="inline-checkbox")

                    content = split(r"^- \[.*?\]", content)[1]
                    doc.text(content)
                else:
                    doc.text(content)

        if paragraph.type == "code":
            with doc.tag("div", klass="fancy-code"):
                with doc.tag("pre", klass="code"):
                    doc.text(paragraph.content)


def appendix(doc, apx):
    with doc.tag("div", klass="small-emphasis-container text-shorten"):
        with doc.tag("h4", klass="no-margin"):
            doc.line("i", "Appendix:")
        with doc.tag("small"):
            doc.line("span", "", klass="icon-link-streamline v-align font-regular")
            with doc.tag("a", href=apx.href, target="_blank"):
                with doc.tag("i"):
                    doc.text(apx.description)


def feedback_button(doc, idparent, topic):
    with doc.tag("div", id="feedback-container-" + idparent, klass="feedback-container", style="position: relative"):
        with doc.tag("div", klass="right text-shorten"):
            with doc.tag("span", id="feedback-toggle-" + idparent, klass="leave-feedback"):
                with doc.tag("span"):
                    doc.line("i", "Send Feedback  ", klass="font-thin")
                with doc.tag("span", klass="icon-bubble-comment-streamline-talk colorful-font font-regular"):
                    doc.text("")


def feedback_form(doc, idparent, topic):
    with doc.tag("div", id="feedback-form-container-" + idparent, klass="fancy-feedback margin-top-20", style="display: none"):
        with doc.tag("form", ("data-netlify", "true"), klass="feedback-form", name="feedback", method="POST"):
            doc.stag("input", type="hidden", name="topic", value=topic)
            doc.line("h5", "Feedback scope:", klass="no-margin")
            doc.line("h5", topic[:36] + "...", klass="no-margin")
            doc.line("hr", "", klass="margin-top-10 margin-bottom-10")
            doc.line("textarea", "", klass="no-border", name="content",
                     placeholder="Click here to write your feedback")
            doc.line("button", "Submit", klass="call-to-action no-border font-regular margin-top-20",
                     type="submit", style="display: block; width: 100%; cursor: pointer;")
            with doc.tag("div", klass="center"):
                with doc.tag("small", klass="max-char-hint"):
                    with doc.tag("span", klass="max-1000-characters"):
                        doc.text("0")
                    doc.text(" of max. 1500 characters")


def chapterindex(doc, chapters, ids):
    with doc.tag("blockquote", klass="chapter-index margin-bottom-10"):

        with doc.tag("div", id="chapter-index-toggle"):
            with doc.tag("h5", klass="no-margin font-regular"):
                with doc.tag("span", klass="icon-book-read-streamline v-align font-regular colorful-font"):
                    doc.text("")
                doc.line("span", " Chapter Index")

        with doc.tag("div"):
            with doc.tag("ul", id="chapter-index-list",
                         klass="margin-top-20 margin-bottom-20 colorful-font-soft",
                         style="display: none"):
                for chapter, _id in zip(chapters, ids):
                    with doc.tag("li"):
                        with doc.tag("a", href="#" + _id):
                            doc.text(chapter.topic)


def like(doc, topic):
    with doc.tag("div", klass="center auto read-width-optimized margin-bottom-20", id="feature-like-journal"):
        with doc.tag("form", ("data-netlify", "true"), name="Like +1 " + topic, method="POST", klass="like-form", id="like-form"):
            doc.stag("input", type="hidden",
                     name="content", value="Received +1")
            with doc.tag("p"):
                doc.line(
                    "i", "Please click the heart icon if you enjoyed this article ! ")
                doc.line(
                    "span", "", klass="icon-bubble-love-streamline-talk font-big submit heartbeat-animation")


def intro(doc, introduction):
    text = introduction.content
    appendix = introduction.appendix

    with doc.tag("blockquote", klass="margin-bottom-20", id="intro-text"):
        doc.text(text)
        doc.text(" ")
        if appendix is not None:
            doc.line("a", appendix.description,
                     href=appendix.href)

    with doc.tag("a", href="#", id="new-chapter-hint", style="display: none"):
        with doc.tag("blockquote", klass="highlight"):
            doc.text(
                "A new chapter was released since your last visit ! Click this box to jump right in !")


def create_better_date(d):
    sl = [
        month_abbr[d.month],
        " ",
        str(d.day),
        ", ",
        str(d.year)
    ]
    return "".join(sl).upper()
