import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Set

from rdf_serializer import RDFSerializer


_SCRAPER_DEST_DIR = str(os.environ.get("SCRAPER_DEST_DIR"))


def format_strings(target: str) -> str:
    return target.replace(" ", "_")


class IdEquivalent(ABC):
    @abstractmethod
    def get_id(self) -> str:
        raise NotImplementedError

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.get_id() == other.get_id()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.get_id())


@dataclass(eq=True, order=True)
class IdentifierModel:
    """
    Auxiliary class not represented in the vocabulary.
    Describes a string typed with one of the scrapdt datatypes.
    """

    value: str
    type_val: str


@dataclass(eq=False)
class AffiliationModel:
    # skos:prefLabel -> xsd:string
    name: str

    # org:identifier -> xsd:simpleType
    # Type specific to the identifier being described, taken from scrapdt namespace.
    identifiers: List[IdentifierModel]

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        if len(self.identifiers) == 0 or len(other.identifiers) == 0:
            logging.log(logging.WARN, f"Comparison of affiliations without identifiers (self: {len(self.identifiers)}, other: {len(other.identifiers)})")
            return self.name == other.name

        for identifier in self.identifiers:
            if identifier in other.identifiers:
                return True
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        reprs_of_each_id = []
        for ident in self.identifiers:
            reprs_of_each_id.append(repr(ident))
        repr_ids = repr(sorted(reprs_of_each_id))
        return hash(repr_ids)

    def get_id(self):
        # TODO: Adjust this method to be less reliant on specific ids? somehow?.
        for ident in self.identifiers:
            if ident.type_val == "ROR":
                return ident.value
        if len(self.identifiers) > 0:
            return self.identifiers[0].value
        return self.name


@dataclass(eq=False)
class AuthorModel(IdEquivalent):
    # foaf:givenName -> xsd:string
    given_name: str

    # foaf:familyName -> xsd:string
    family_name: str

    # dbo:orcidId -> xsd:string
    orcid: str

    # org:memberOf -> :Affiliation
    affiliations: Set[AffiliationModel]

    def get_id(self) -> str:
        if self.orcid:
            return self.orcid
        else:
            return format_strings(self.given_name) +\
                   "_" + format_strings(self.family_name)


@dataclass(eq=False)
class PaperModel(IdEquivalent):
    # prism:doi -> xsd:string
    doi: str

    # dcterms:abstract -> xsd:string
    abstract_text: str

    # prism:keyword -> xsd:string
    keywords: Set[str]

    # URL to the SCPE page about this paper.
    # fabio:hasURL
    url: str

    # URL to a PDF file (realization)
    # frbr:realization -> fabio:DigitalManifestation ->
    #                     {
    #                          dcterms:format -> xsd:string (application/pdf)
    #                          fabio:hasURL -> xsd:string (THIS)
    #                     }
    pdf_url: str

    # dcterms:title
    title: str

    # prism:volume -> xsd:integer
    volume: int
    # prism:startingPage -> xsd:integer
    startingPage: int
    # prism:endingPage -> xsd:integer
    endingPage: int

    # dcterms:author -> :Author
    authors: Set[AuthorModel]

    def get_id(self):
        return "SCPE_" + str(self.volume) +\
               "_" + format_strings(self.title)


class DataModel:
    def __init__(self, filename: str):
        self._id = filename
        self._papers: Set[PaperModel] = set()
        self._authors: Set[AuthorModel] = set()
        self._affiliations: Set[AffiliationModel] = set()

    def add_paper(self, paper: PaperModel):
        self._papers.add(paper)

    def add_author(self, author: AuthorModel):
        self._authors.add(author)

    def add_affiliation(self, affiliation: AffiliationModel):
        self._affiliations.add(affiliation)

    def serialize(self):
        serializer = RDFSerializer()
        for affiliation in self._affiliations:
            serializer.accept_affiliation(affiliation)
        for author in self._authors:
            serializer.accept_author(author)
        for paper in self._papers:
            serializer.accept_paper(paper)
        serializer.serialize(os.path.join(_SCRAPER_DEST_DIR, self._id))
