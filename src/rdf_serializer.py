from rdflib import XSD, DCTERMS, FOAF, RDF, ORG, SKOS, RDFS, OWL
from rdflib.graph import Graph
from rdflib.namespace import Namespace
from rdflib.term import URIRef, Literal, BNode

import model
from rdf_namespaces import DBO, FABIO, FRBR, PRISM


class RDFSerializer:
    def __init__(self):
        URI_BASE = URIRef("https://opencs.scpe.scraper.com/")
        self._BASE = Namespace(URI_BASE)

        URI_DT = URIRef("https://opencs.scpe.scraper.com/datatypes#")
        self._SCRAPDT = Namespace(URI_DT)

        self._g = Graph()
        self._g.bind("", self._BASE)
        self._g.bind("scrapdt", self._SCRAPDT)
        self._g.bind("xsd", XSD)
        self._g.bind("dcterms", DCTERMS)
        self._g.bind("foaf", FOAF)
        self._g.bind("rdf", RDF)
        self._g.bind("org", ORG)
        self._g.bind("skos", SKOS)
        self._g.bind("rdfs", RDFS)
        self._g.bind("owl", OWL)
        self._g.bind("fabio", FABIO)
        self._g.bind("dbo", DBO)
        self._g.bind("prism", PRISM)
        self._g.bind("frbr", FRBR)

    def _add_pdf_bnode(self, paper: model.PaperModel) -> BNode:
        bn = BNode()
        self._g.add((bn, RDF.type, FABIO.DigitalManifestation))
        self._g.add((bn, DCTERMS.format, Literal("application/pdf")))
        self._g.add((bn, FABIO.hasURL, URIRef(paper.pdf_url)))
        return bn

    def accept_paper(self, paper: model.PaperModel):
        # TODO: Run this code and fix, I probably missed something important
        #       and messed up the syntax. :|
        paper_id = paper.get_id()
        paper_node = self._BASE[paper_id]

        # Pair to be assigned to the specific paper.
        # In N3 (s p o) it's (p o), with the paper as the s.
        pairs = [
            (RDF.type, self._BASE["Paper"]),
            (PRISM.doi, Literal(paper.doi)),
            (DCTERMS.abstract, Literal(paper.abstract_text)),
            (DCTERMS.title, Literal(paper.title)),
            (PRISM.volume, Literal(paper.volume)),
            (PRISM.startingPage, Literal(paper.startingPage)),
            (PRISM.endingPage, Literal(paper.endingPage)),
            (FABIO.hasURL, Literal(paper.url)),
        ]

        if paper.pdf_url is not None:
            pdf_realization = self._add_pdf_bnode(paper)
            pairs.append((FRBR.realization, pdf_realization))

        for keyword in paper.keywords:
            keyword_list = keyword.split(",")
            for k in keyword_list:
                pairs.append((PRISM.keyword, Literal(k)))

        for author in paper.authors:
            pairs.append((DCTERMS.creator, self._BASE[author.get_id()]))

        for p, o in pairs:
            self._g.add((paper_node, p, o))

    def accept_author(self, author: model.AuthorModel):
        author_id = author.get_id()
        author_node = self._BASE[author_id]

        pairs = [
            (RDF.type, self._BASE["Author"]),
            (FOAF.givenName, Literal(author.given_name)),
            (FOAF.familyName, Literal(author.family_name)),
            (DBO.orcidId, Literal(author.orcid)),
        ]

        for affiliation in author.affiliations:
            pairs.append((ORG.memberOf, self._BASE[affiliation.get_id()]))

        for p, o in pairs:
            self._g.add((author_node, p, o))

    def _format_identifier(self, identifier: model.IdentifierModel) -> Literal:
        return Literal(identifier.value, datatype=self._SCRAPDT[identifier.type_val])

    def accept_affiliation(self, affiliation: model.AffiliationModel):
        affiliation_id = affiliation.get_id()
        affiliation_node = self._BASE[affiliation_id]

        pairs = [
            (RDF.type, self._BASE["Affiliation"]),
            (SKOS.prefLabel, Literal(affiliation.name)),
        ]

        for identifier in affiliation.identifiers:
            pairs.append((ORG.identifier, self._format_identifier(identifier)))

        for p, o in pairs:
            self._g.add((affiliation_node, p, o))

    def serialize(self, destination: str):
        self._g.serialize(destination=destination, format="turtle")
