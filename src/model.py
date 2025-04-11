from datetime import date
from typing import Any, List, Optional
from pydantic import BaseModel, constr, stricturl, validator
from pydantic.main import Extra
from pydantic.types import DirectoryPath, FilePath
from re import match


class Meta(BaseModel):
    author: constr(min_length=2, max_length=48)
    website: stricturl(allowed_schemes=["https"])
    year: constr(min_length=4)
    title: constr(min_length=24, max_length=60)
    description: constr(min_length=50, max_length=160)
    keywords: str
    opt_out: Optional[str]

    class Config:
        validate_assignment = True
        allow_mutation = False
        extra = Extra.forbid

    @validator("keywords")
    def keywords_must_be_five_words(cls, v):
        if not valid_keywords(word_count=5, kws=v):
            msg = ("ensure this value has exactly 5 words with at least 3"
                   " characters and up to 16 for each word")
            raise ValueError(msg)

        return v

    @validator("keywords")
    def keywords_must_not_have_duplicates(cls, v):
        if duplicates(v.split(" ")):
            msg = "ensure this value has no duplicates in it"
            raise ValueError(msg)

        return v

    @validator("year")
    def year_must_be_valid_format(cls, v):
        if not valid_year(v):
            msg = ("ensure this value has these formats of"
                   " integers \"2020 - 2021\" or \"2020\"")
            raise ValueError(msg)

        return v


class WebRootPath(str):
    ext_validators = DirectoryPath

    @classmethod
    def __get_validators__(cls):
        yield cls.one_folder_up

        for validate in cls.ext_validators.__get_validators__():
            yield validate

        yield cls.set_absolute

    @classmethod
    def one_folder_up(cls, v):
        if v[0] != "/" and v[:3] != "../":
            v = "../" + v
        else:
            raise ValueError("dir navigation not allowed")

        return v

    @classmethod
    def set_absolute(cls, v):
        v = str(v)
        v = v[2:]
        return v


class WebRootFilePath(WebRootPath):
    ext_validators = FilePath


class Appendix(BaseModel):
    description: constr(min_length=3, max_length=48)
    href: stricturl(allowed_schemes=["https"])


class AppendixFilePath(Appendix):
    href: WebRootFilePath


class Introduction(BaseModel):
    content: constr(min_length=50, max_length=600)
    appendix: Optional[Appendix]

    class Config:
        validate_assignment = True
        allow_mutation = False
        extra = Extra.forbid


class Gallery(BaseModel):
    height: constr(min_length=3)
    items: List[WebRootFilePath]


class GalleryUrl(Gallery):
    items: List[stricturl(allowed_schemes=["https"])]


class Picture(BaseModel):
    src: WebRootFilePath
    height: constr(min_length=3)


class PictureUrl(Picture):
    src: stricturl(allowed_schemes=["https"])


class Quote(BaseModel):
    author: constr(min_length=2, max_length=48)
    content: constr(min_length=10)
    reference: stricturl(allowed_schemes=["https"])


class Paragraph(BaseModel):
    type: str
    content: str


class Chapter(BaseModel):
    author: constr(min_length=2, max_length=48)
    topic: constr(min_length=8, max_length=60)
    date: date
    website: Optional[stricturl(allowed_schemes=["https"])]
    appendix: Optional[Appendix]
    picture: Optional[Picture]
    interactive_example: Optional[WebRootPath]
    gallery: Optional[Gallery]
    quote: Optional[Quote]
    paragraphs: Optional[List[Paragraph]]

    class Config:
        validate_assignment = True
        allow_mutation = False
        extra = Extra.forbid


class Article(BaseModel):
    meta: Meta
    introduction: Introduction
    items: List[Any]


def duplicates(l: List):
    return len(l) is not len(set(l))


def in_between(n, mi, mx):
    return n >= mi and n <= mx


def type_chapter_with_appendix_filepath(Model: Chapter):
    class ChapterAppendixFilePath(Model):
        appendix: AppendixFilePath

    return ChapterAppendixFilePath


def type_chapter_with_picture_url(Model: Chapter):
    class ChapterPicUrl(Model):
        picture: PictureUrl

    return ChapterPicUrl


def type_chapter_with_gallery_url(Model: Chapter):
    class ChapterGalleryUrl(Model):
        gallery: GalleryUrl

    return ChapterGalleryUrl


def type_with_appendix_filepath(Model: BaseModel):
    class ModelAppendixFilePath(Model):
        appendix: AppendixFilePath

    return ModelAppendixFilePath


def valid_year(y: str):
    return bool(match(r"^([0-9]{4}|[0-9]{4} - [0-9]{4})$", y))


def valid_keywords(word_count: int, kws: str) -> bool:
    ws = words(kws)
    if len(ws) is not word_count:
        return False

    return all(words_in_between_length(min_l=3, max_l=16, ws=ws))


def words(ws: str):
    return ws.split(" ")


def words_in_between_length(min_l: int, max_l: int, ws: List[str]):
    return (in_between(len(w), min_l, max_l) for w in ws)
