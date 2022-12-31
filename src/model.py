from dataclasses import dataclass
from typing import List


@dataclass
class PaperModel:
    doi: str
    abstract_text: str
    keywords: List[str]
    pdf_url: str

    volume_number: int
    page_start: int
    page_end: int

    def serialize(self):
        raise NotImplementedError


@dataclass
class AuthorModel:
    given_name: str
    family_name: str
    orcid: str


class DataModel:
    def __init__(self):
        self._papers: List[PaperModel] = []
        self._authors: List[AuthorModel] = []

    def add_paper(self, paper: PaperModel):
        self._papers.append(paper)

    def add_author(self, author: AuthorModel):
        self._authors.append(author)

    def serialize(self):
        raise NotImplementedError
