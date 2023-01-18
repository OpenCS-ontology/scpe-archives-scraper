import io
import logging
from dataclasses import dataclass
from typing import List, Optional

import lightrdf
from rdflib import DCTERMS, FOAF, RDF, OWL

from rdf_namespaces import PRISM_2_1


@dataclass
class AuthorDoiResponse:
    family_name: str
    given_name: str
    name: str
    orcid: Optional[str]


@dataclass
class PaperDoiResponse:
    starting_page: str
    ending_page: str
    volume: str
    date: str
    title: str
    authors: List[AuthorDoiResponse]


def strip_quotes(target: str) -> str:
    return target.strip('"')


ORCID_STRING = 'orcid.org'


def retrieve_and_strip_quotes(rdf_model: lightrdf.RDFDocument, o, p):
    triples = list(rdf_model.search_triples(o, p, None))
    if triples:
        return strip_quotes(triples[0][2])
    else:
        return None


def doi_api_decoder(data: bytes) -> PaperDoiResponse:
    parsed = lightrdf.RDFDocument(io.BytesIO(data), parser=lightrdf.turtle.PatternParser)

    def find_authors(turtle: lightrdf.RDFDocument) -> List[AuthorDoiResponse]:
        result = []

        author_triples = turtle.search_triples(None, RDF.type, FOAF.Person)
        if author_triples is None:
            return result

        try:
            for author_triple in author_triples:
                author_uri = author_triple[0]

                # Try to find ORCID
                other_author_uri = list(turtle.search_triples(author_uri, OWL.sameAs, None))
                assert len(other_author_uri) <= 1
                orcid = None
                if len(other_author_uri) != 0:
                    other_uri = other_author_uri[0][2]
                    assert ORCID_STRING in other_uri
                    where_orcid = other_uri.find(ORCID_STRING)
                    orcid = other_uri[where_orcid + len(ORCID_STRING) + 1:len(other_uri) - 1]

                # Get the remaining info
                name = retrieve_and_strip_quotes(turtle, author_uri, FOAF.name)
                given_name = retrieve_and_strip_quotes(turtle, author_uri, FOAF.givenName)
                family_name = retrieve_and_strip_quotes(turtle, author_uri, FOAF.familyName)

                author = AuthorDoiResponse(
                    orcid=orcid,
                    given_name=given_name,
                    family_name=family_name,
                    name=name
                )
                result.append(author)
        except Exception:
            # lightrdf throws errors if some turtles returned from DOI api aren't really ok
            logging.warning(f"Lightrdf error in searching authors.\nTurtle file got from DOI api:\n{io.BytesIO(data)}\n")
        return result

    authors = find_authors(parsed)

    paper_uri = list(parsed.search_triples(None, PRISM_2_1.doi, None))[0][0]

    ending_page = retrieve_and_strip_quotes(parsed, paper_uri, PRISM_2_1.endingPage)
    starting_page = retrieve_and_strip_quotes(parsed, paper_uri, PRISM_2_1.startingPage)
    volume = retrieve_and_strip_quotes(parsed, paper_uri, PRISM_2_1.volume)
    date = retrieve_and_strip_quotes(parsed, paper_uri, DCTERMS.date)
    title = retrieve_and_strip_quotes(parsed, paper_uri, DCTERMS.title)

    return PaperDoiResponse(
        ending_page=ending_page,
        starting_page=starting_page,
        volume=volume,
        date=date,
        title=title,
        authors=authors
    )
