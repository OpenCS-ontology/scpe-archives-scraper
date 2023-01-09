from rdflib.graph import Graph, URIRef, Literal, BNode
from rdflib.namespace import Namespace, XSD, DCTERMS, FOAF, RDF, ORG, SKOS, RDFS, OWL

import model


class RDFSerializer:
    def __init__(self):
        self._URI_BASE = URIRef("https://opencs.scpe.scraper.com/")
        self._URI_DT = URIRef("https://opencs.scpe.scraper.com/datatypes#")

        self._FABIO = Namespace("http://purl.org/spar/fabio/")
        self._DBO = Namespace("http://dbpedia.org/ontology/")
        self._PRISM = Namespace("http://prismstandard.org/namespaces/basic/2.0/")
        self._FRBR = Namespace("http://purl.org/spar/frbr")

        self._g = Graph()
        self._g.bind("", self._URI_BASE)
        self._g.bind("scrapdt", self._URI_DT)
        self._g.bind("xsd", XSD)
        self._g.bind("dcterms", DCTERMS)
        self._g.bind("foaf", FOAF)
        self._g.bind("rdf", RDF)
        self._g.bind("org", ORG)
        self._g.bind("skos", SKOS)
        self._g.bind("rdfs", RDFS)
        self._g.bind("owl", OWL)
        self._g.bind("fabio", self._FABIO)
        self._g.bind("dbo", self._DBO)
        self._g.bind("prism", self._PRISM)
        self._g.bind("frbr", self._FRBR)

    def _add_pdf_bnode(self, paper: model.PaperModel) -> BNode:
        bn = BNode()
        self._g.add((bn, RDF.type, self._FABIO.DigitalManifestation))
        self._g.add((bn, DCTERMS.format, Literal("application/pdf")))
        self._g.add((bn, self._FABIO.hasURL, URIRef(paper.pdf_url)))
        return bn

    def accept_paper(self, paper: model.PaperModel):
        # TODO: Run this code and fix, I probably missed something important
        #       and messed up the syntax. :|
        paper_id = paper.get_id()
        paper_uri = URIRef(f":{paper_id}")

        pdf_realization = self._add_pdf_bnode(paper)

        # Pair to be assigned to the specific paper.
        # In N3 (s p o) it's (p o), with the paper as the s.
        pairs = [
            (RDF.type, URIRef(f":Paper")),
            (self._PRISM.doi, Literal(paper.doi)),
            (DCTERMS.abstract, Literal(paper.abstract_text)),
            (DCTERMS.title, Literal(paper.title)),
            (self._PRISM.volume, Literal(paper.volume)),
            (self._PRISM.startingPage, Literal(paper.startingPage)),
            (self._PRISM.endingPage, Literal(paper.endingPage)),
            (self._FABIO.hasURL, Literal(paper.url)),
            (self._FRBR.realization, pdf_realization),
        ]

        for keyword in paper.keywords:
            keyword_list = keyword.split(",")
            for k in keyword_list:
                pairs.append((self._PRISM.keyword, Literal(k)))

        for author in paper.authors:
            pairs.append((DCTERMS.author, URIRef(f":{author.get_id()}")))

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

        for affiliation in author.affiliations:
            pairs.append((ORG.memberOf, URIRef(f":{affiliation.get_id()}")))

        for p, o in pairs:
            self._g.add((author_uri, p, o))

    def _format_identifier(self, identifier: model.IdentifierModel) -> Literal:
        # TODO: Create a proper namespace for scrapdt and replace this clunky URIRef.
        return Literal(identifier.value, datatype=URIRef(f"{self._URI_DT.lower()}:{identifier.type_val}"))

    def accept_affiliation(self, affiliation: model.AffiliationModel):
        affiliation_id = affiliation.get_id()
        affiliation_uri = URIRef(f":{affiliation_id}")

        pairs = [
            (RDF.type, URIRef(f":Affiliation")),
            (SKOS.prefLabel, Literal(affiliation.name)),
        ]

        for identifier in affiliation.identifiers:
            pairs.append((ORG.identifier, self._format_identifier(identifier)))

        for p, o in pairs:
            self._g.add((affiliation_uri, p, o))

    def serialize(self, destination: str):
        self._g.serialize(destination=destination, format="turtle")
