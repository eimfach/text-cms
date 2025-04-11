from functools import partial, reduce
from re import match
from typing import Dict, List, Tuple
from operator import getitem

from pydantic.error_wrappers import ValidationError
from model import Article, Chapter, Introduction, Meta
from model import type_chapter_with_gallery_url, type_chapter_with_picture_url
from model import type_with_appendix_filepath


class TokenizePropertyValues():
    def __init__(self):
        self.input_map = {
            "appendix": self._tokenize_appendix,
            "picture": self._tokenize_picture,
            "gallery": self._tokenize_gallery,
            "quote": self._tokenize_quote
        }

    def _tokenize_appendix(self, v: str):
        m = match(r"^\[(.*)\] (\S+)$", v)
        if m:
            v = {"description": m[1].strip(), "href": m[2]}
        else:
            err_msg = ("ensure this value has valid syntax: \""
                       "appendix\", like this: \"[description] "
                       "https://www.robingruenke.com\"")

            return None, err_msg

        return v, None

    def _tokenize_picture(self, v: str):
        m = match(r"^(\d+px) (\S+)$", v)
        if m:
            v = {"height": m[1], "src": m[2]}
        else:
            err_msg = ("ensure this value has valid syntax: \""
                       "picture\", like this: \"250px "
                       "/gallery/img.png\"")
            return None, err_msg

        return v, None

    def _tokenize_gallery(self, v: str):
        m = match(r"^(\d+px) (.+)$", v)
        if m:
            v = {"height": m[1], "items": m[2].split(" ")}
        else:
            err_msg = ("ensure this value has valid syntax: "
                       "\"gallery\", like this: \"45px "
                       "/gallery/img_1.png /gallery/img_2.png\"")
            return None, err_msg

        return v, None

    def _tokenize_quote(self, v: str):
        m = match(r"^\[(.*)\] \[(.+)\] (.+)$", v)
        if m:
            v = {
                "author": m[1],
                "content": m[2],
                "reference": m[3]
            }
        else:
            err_msg = ("ensure this value has proper formatting "
                       "\"quote\", like this \"[description] [content] \""
                       "https://wikipedia.com\"")
            return None, err_msg

        return v, None


class TokenizeComponent:

    def __init__(self):
        self.input_map = {
            "/meta": self.tokenize_component_meta,
            "/introduction": self.tokenize_component_introduction,
            "/chapter": self.tokenize_component_chapter
        }

    class Decorators:
        @classmethod
        def tokenize_properties(cls, *, has_content_body: bool):
            def wrapper(next_step):
                def tokenize(self, chunk: List):
                    err_comp = f"Error in {chunk[0].rstrip()} properties"
                    msg = partial(err_msg, err_comp)
                    props, tail = _tokenize_component_properties(chunk)

                    if len(tail) > 0:
                        invalid_msg = _invalid_tail(
                            has_content_body, props, tail)

                        if invalid_msg:
                            return None, msg(*invalid_msg)

                    return next_step(self, msg, props, tail)

                return tokenize
            return wrapper

        @classmethod
        def tokenize_property_values(cls, tpv: TokenizePropertyValues):
            def wrapper(next_step):
                def tokenize(self, msg, props, tail):
                    psc = props.copy()
                    input_map = tpv.input_map

                    for prop, val in props.items():
                        tokenize = input_map.get(prop)
                        if not tokenize:
                            continue

                        t, err = tokenize(val)
                        if err:
                            return None, msg(err)
                        else:
                            psc[prop] = t

                    return next_step(self, msg, psc, tail)

                return tokenize
            return wrapper

    @Decorators.tokenize_properties(has_content_body=True)
    @Decorators.tokenize_property_values(TokenizePropertyValues())
    def tokenize_component_chapter(self, msg, props, tail):
        paragraphs = []
        append = paragraphs.append
        previously_blank = False
        inside_code_block = False

        for line in tail:

            if blank(line) and not inside_code_block:
                previously_blank = True

            elif match(r"^\|code", line):
                append({"type": "code", "content": ""})
                inside_code_block = True

            elif match(r"^code\|", line):
                inside_code_block = False

            elif inside_code_block:
                paragraphs[-1]["content"] += line

            elif previously_blank:
                append({"type": "text", "content": [line.strip()]})
                previously_blank = False

            else:
                paragraphs[-1]["content"].append(line.strip())

        str_paragraphs(paragraphs)

        return ({**props, "paragraphs": paragraphs}, None)

    @Decorators.tokenize_properties(has_content_body=True)
    @Decorators.tokenize_property_values(TokenizePropertyValues())
    def tokenize_component_introduction(self, msg, props, tail):
        lines = [line.rstrip() for line in tail if not blank(line)]

        intro = " ".join(lines)
        return ({"content": intro.strip(), **props}, None)

    @Decorators.tokenize_properties(has_content_body=False)
    def tokenize_component_meta(self, msg, props, tail):
        return props, None


class ParseComponent:
    def __init__(self):
        self.input_map = {
            "/chapter": self.parse_component_chapter,
            "/introduction": self.parse_component_introduction,
            "/meta": self.parse_component_meta
        }

    def parse_component_chapter(self, tokens: Dict):
        try:
            Model = Chapter

            if "appendix" in tokens and not is_url(tokens["appendix"]["href"]):
                Model = type_with_appendix_filepath(Model)

            if "gallery" in tokens and is_url(tokens["gallery"]["items"][0]):
                Model = type_chapter_with_gallery_url(Model)

            if "picture" in tokens and is_url(tokens["picture"]["src"]):
                Model = type_chapter_with_picture_url(Model)

            chapter = Model(**tokens)

        except ValidationError as e:
            err_comp = "Error in /chapter"
            return None, default_err_msg(e, err_comp, tokens)

        return chapter, None

    def parse_component_introduction(self, tokens: Dict):
        try:
            Model = Introduction

            if "appendix" in tokens and not is_url(tokens["appendix"]["href"]):
                Model = type_with_appendix_filepath(Model)

            intro = Model(**tokens)

        except ValidationError as e:
            err_comp = "Error in /introduction"
            return None, default_err_msg(e, err_comp, tokens)

        return intro, None

    def parse_component_meta(self, tokens: Dict):
        err_comp = "Error in /meta properties"

        try:
            meta = Meta(**tokens)
            return meta, None

        except ValidationError as e:
            return None, default_err_msg(e, err_comp)


def _analyze_incorrect_property(line: str, props: List):
    err_msg_notation = "expected property notation but found"
    err_msg_space = "expected space after first colon"
    err_duplicate = "duplicate of field"

    if prop_missing_space(line):
        return err_msg_space

    elif _tokenize_property(line)[0] in props:
        return err_duplicate

    else:
        return err_msg_notation


def _chunk_until_next_component(file) -> List[str]:

    fi = SeekableFileIterator(file)
    first_line = next(fi, "---")

    if drafting(first_line):
        return []

    chunk = [first_line]
    append = chunk.append

    for line in fi:
        if component_identifier(line) or drafting(line):
            fi.rewind()
            break
        else:
            append(line)

    return chunk


def _component_iterator(file):
    return iter(partial(_chunk_until_next_component, file), [])


def _invalid_tail(has_content_body, props, tail):
    if not props_body_terminated(tail):
        msg = _analyze_incorrect_property(tail[0], props)
        return (msg, tail[0])

    elif not has_content_body:
        line = get_first_contentful(tail)
        if line is not "":
            msg = ("Properties were terminated by"
                   " blank line, overflowing content not allowed")

            return (msg, line)

    return None


def _tokenize_component_properties(chunk: List):
    properties = {}
    tail = []
    append_tail = tail.append
    chunk = chunk[1:]

    for n, line in enumerate(chunk):

        if blank(line):
            tail += chunk[n:]
            break

        lrs = line.rstrip()
        prop, value = _tokenize_property(lrs)

        if prop and prop not in properties:
            properties[prop] = value

        else:
            append_tail(line)

    return (properties, tail)


def _tokenize_property(line: str):
    m = match(r"^(.+?): (.+?)$", line)
    if m:
        prop, value = m.group(1, 2)
        return (prop.replace("-", "_"), value)
    else:
        return (None, None)


def parse(file,
          parse: ParseComponent = ParseComponent(),
          tokenize: TokenizeComponent = TokenizeComponent()):

    result = {"items": []}
    append_items = result["items"].append
    comp_count = 0

    for i, comp in enumerate(_component_iterator(file)):
        comp_count += 1
        comp_id = comp[0].strip()
        comp_is_meta = comp_id == "/meta"
        comp_is_intro = comp_id == "/introduction"

        if i == 0 and not comp_is_meta:
            yield None, ("Error: First component expected to be "
                         "/meta component")

        elif i == 1 and not comp_is_intro:
            yield None, ("Error: Second component expected to be "
                         "/introduction component")

        try:
            tokens, err = tokenize.input_map[comp_id](comp)

        except KeyError:
            err = f"Error: Tokenizer for \"{comp_id}\" not implemented"

        if err:
            yield None, err
            continue

        try:
            pcomp, err = parse.input_map[comp_id](tokens)

        except KeyError:
            err = f"Error: Parser for \"{comp_id}\" not implemented"

        if err:
            yield None, err
            continue

        if comp_is_meta or comp_is_intro:
            result[comp_id[1:]] = pcomp
        else:
            append_items(pcomp)

    items_positive = len(result["items"]) == comp_count - 2
    meta_positive = "meta" in result
    intro_positive = "introduction" in result

    if items_positive and meta_positive and intro_positive:
        yield Article(**result), None


###########################################
################# HELPERS #################
###########################################


class SeekableFileIterator:
    def __init__(self, file):
        self._file_pos = file.tell()
        self._file = file

    def __iter__(self):
        return self

    def __next__(self):
        self._file_pos = self._file.tell()
        line = self._file.readline()

        if self._end_of_file(line):
            raise StopIteration

        return line

    def _end_of_file(self, line):
        return line is ""

    def rewind(self):
        self._file.seek(self._file_pos)


def blank(line):
    return line.isspace()


def component_identifier(line):
    return line[0] is "/"


def component_type_is(name, chunk: List):
    line = chunk[0]
    return line.rstrip() == "/" + name


def default_err_msg(err, cmp, tokens=None):
    error = err.errors()[0]
    msg = error["msg"]
    keys = error["loc"]

    target = "->".join(replace(keys, "_", "-"))

    if tokens and keys[0] in tokens:
        v = get_value_from_nested_dict(tokens, keys)
        vt = truncate(v, 14)
        target = target + f": {vt} (len={len(v)})"

    return err_msg(cmp, msg, target)


def drafting(line):
    return line[:3] == "---"


def err_msg(component, msg, target=None):
    sl = [component, ": ", msg]

    if target:
        sl += [": ", "\"", target, "\""]

    return "".join(sl)


def get_first_contentful(tail):
    for l in tail:
        if not blank(l):
            return l

    return ""


def get_value_from_nested_dict(d: Dict, path: Tuple[str]):
    return reduce(getitem, path, d)


def is_url(s):
    return bool(match(r"^[a-z]+://", s))


def prop_missing_space(line: str):
    matches = line.rstrip().split(":", maxsplit=1)

    if len(matches) is 2 and matches[1][0] is not " ":
        return True
    else:
        return False


def props_body_terminated(tail):
    return blank(tail[0])


def replace(sl: List[str], c1, c2):
    return [str(s).replace(c1, c2) for s in sl]


def str_paragraphs(ps: List[Dict]):
    for p in ps:
        if p["type"] is "text":
            p["content"] = " ".join(p["content"])


def truncate(s, l):
    return (s[:l] + "...") if len(s) > l else s
