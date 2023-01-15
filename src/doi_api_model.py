import io
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


def doi_api_decoder(data: bytes) -> PaperDoiResponse:
    parsed = lightrdf.RDFDocument(io.BytesIO(data), parser=lightrdf.turtle.PatternParser)

    def find_authors(turtle: lightrdf.RDFDocument) -> List[AuthorDoiResponse]:
        result = []

        author_uris = map(lambda l: l[0], turtle.search_triples(None, RDF.type, FOAF.Person))
        for author_uri in author_uris:
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
            name = strip_quotes(list(turtle.search_triples(author_uri, FOAF.name, None))[0][2])
            given_name = strip_quotes(list(turtle.search_triples(author_uri, FOAF.givenName, None))[0][2])
            family_name = strip_quotes(list(turtle.search_triples(author_uri, FOAF.familyName, None))[0][2])

            author = AuthorDoiResponse(
                orcid=orcid,
                given_name=given_name,
                family_name=family_name,
                name=name
            )
            result.append(author)
        return result

    authors = find_authors(parsed)

    paper_uri = list(parsed.search_triples(None, PRISM_2_1.doi, None))[0][0]

    ending_page = list(parsed.search_triples(paper_uri, PRISM_2_1.endingPage, None))[0][2]
    ending_page = strip_quotes(ending_page)
    starting_page = list(parsed.search_triples(paper_uri, PRISM_2_1.startingPage, None))[0][2]
    starting_page = strip_quotes(starting_page)
    volume = list(parsed.search_triples(paper_uri, PRISM_2_1.volume, None))[0][2]
    volume = strip_quotes(volume)
    date = list(parsed.search_triples(paper_uri, DCTERMS.date, None))[0][2]
    title = list(parsed.search_triples(paper_uri, DCTERMS.title, None))[0][2]

    return PaperDoiResponse(
        ending_page=ending_page,
        starting_page=starting_page,
        volume=volume,
        date=date,
        title=title,
        authors=authors
    )
