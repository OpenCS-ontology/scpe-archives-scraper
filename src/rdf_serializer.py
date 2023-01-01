from rdflib.graph import Graph, URIRef, Literal
from rdflib.namespace import Namespace, XSD, DCTERMS, FOAF, RDF

import model


class RDFSerializer:
    def __init__(self):
        self._URI_BASE = URIRef("https://opencs.scpe.scraper.com/")

        self._DATACITE = Namespace("http://purl.org/spar/datacite/")
        self._FABIO = Namespace("http://purl.org/spar/fabio/")
        self._SCHEMA = Namespace("https://schema.org/")
        self._DBO = Namespace("http://dbpedia.org/ontology/")

        self._g = Graph()
        self._g.bind("", self._URI_BASE)
        self._g.bind("xsd", XSD)
        self._g.bind("dcterms", DCTERMS)
        self._g.bind("foaf", FOAF)
        self._g.bind("rdf", RDF)
        self._g.bind("datacite", self._DATACITE)
        self._g.bind("fabio", self._FABIO)
        self._g.bind("schema", self._SCHEMA)
        self._g.bind("dbo", self._DBO)

    def accept_paper(self, paper: model.PaperModel):
        # TODO: Run this code and fix, I probably missed something important
        #       and messed up the syntax. :|
        paper_id = paper.get_id()
        paper_uri = URIRef(f":{paper_id}")

        # Pair to be assigned to the specific paper.
        # In N3 (s p o) it's (p o), with the paper as the s.
        pairs = [
            (RDF.type, URIRef(f":Paper")),
            (self._DATACITE.doi, Literal(paper.doi)),
            (DCTERMS.abstract, Literal(paper.abstract_text)),
            (DCTERMS.title, Literal(paper.title)),
            (self._SCHEMA.volumeNumber, Literal(paper.volume_number)),
            (self._SCHEMA.pageStart, Literal(paper.page_start)),
            (self._SCHEMA.pageEnd, Literal(paper.page_end)),
            (self._FABIO.hasURL, Literal(paper.pdf_url)),
        ]

        for keyword in paper.keywords:
            pairs.append((self._SCHEMA.keywords, Literal(keyword)))

        for author in paper.authors:
            pairs.append((self._SCHEMA.author, URIRef(f":{author.get_id()}")))

        for p, o in pairs:
            self._g.add((paper_uri, p, o))

    def accept_author(self, author: model.AuthorModel):
        author_id = author.get_id()
        author_uri = URIRef(f":{author_id}")

        pairs = [
            (RDF.type, URIRef(f":Author")),
            (FOAF.givenName, Literal(author.given_name)),
            (FOAF.familyName, Literal(author.family_name)),
            (self._DBO.orcidId, Literal(author.orcid)),
        ]

        for p, o in pairs:
            self._g.add((author_uri, p, o))

    def serialize(self, destination: str):
        self._g.serialize(destination=destination, format="turtle")
