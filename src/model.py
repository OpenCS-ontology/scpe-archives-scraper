import os
from dataclasses import dataclass
from typing import List

from rdf_serializer import RDFSerializer


_SCRAPER_DEST_DIR = str(os.environ.get("SCRAPER_DEST_DIR"))


def format_strings(target: str) -> str:
    return target.replace(" ", "_")


@dataclass
class AuthorModel:
    given_name: str
    family_name: str
    orcid: str

    def get_id(self) -> str:
        return format_strings(self.given_name) +\
               "_" + format_strings(self.family_name) +\
               "_" + self.orcid


@dataclass
class PaperModel:
    doi: str
    abstract_text: str
    keywords: List[str]
    pdf_url: str
    title: str

    volume_number: int
    page_start: int
    page_end: int

    authors: List[AuthorModel]

    def get_id(self):
        return "SCPE_" + str(self.volume_number) +\
               "_" + format_strings(self.title)


class DataModel:
    def __init__(self, filename: str):
        self._id = filename
        self._papers: List[PaperModel] = []
        self._authors: List[AuthorModel] = []

    def add_paper(self, paper: PaperModel):
        self._papers.append(paper)

    def add_author(self, author: AuthorModel):
        self._authors.append(author)

    def serialize(self):
        serializer = RDFSerializer()
        for author in self._authors:
            serializer.accept_author(author)
        for paper in self._papers:
            serializer.accept_paper(paper)
        serializer.serialize(os.path.join(_SCRAPER_DEST_DIR, self._id))
