import logging
from dataclasses import dataclass
from http import HTTPStatus
from queue import Queue
from threading import Thread
from typing import List, Optional

import requests
from bs4 import BeautifulSoup

URL_ARCHIVES = 'https://www.scpe.org/index.php/scpe/issue/archive'
BEAUTIFUL_SOUP_FEATURES = "html.parser"


@dataclass
class AuthorScraperResponse:
    """
    Model representing the scraped data about the author.
    Mainly used to get information about affiliation, which cannot be acquired from DOI api.
    """

    # citation_author
    name: str

    # citation_author_institution
    affiliation: Optional[str]


@dataclass
class PaperScraperResponse:
    """
    Model representing the scraped data about the paper.
    """

    # Page's url
    url: str

    # DC.Description
    abstract_text: str

    # DC.Identifier.DOI
    doi: str

    # DC.Subject
    keywords: List[str]

    # Cannot be acquired from meta
    pdf_url: Optional[str]

    authors: List[AuthorScraperResponse]


def get_paper_queue() -> Queue[PaperScraperResponse]:
    """
    Get a queue into which papers will be scraped.
    Sometimes dummy papers can appear. Their DOI is an empty string, and they should be ignored.
    :return: Queue on which the scraped papers will appear periodically.
    """

    q = Queue()
    t = Thread(target=scrape_all_doi, args=[q])
    t.start()
    return q


def scrape_all_doi(q: Queue[PaperScraperResponse]) -> None:
    """
    Using HTTP requests get DOIs of all articles in the SCPE archives.
    :param q: Parallel listener into which to return found data.
    :return: List of all DOIs in SCPE Archive.
    """

    r_archives = requests.get(URL_ARCHIVES)

    if r_archives.status_code != HTTPStatus.OK:
        raise Exception("Archives list read error")

    soup_archives = BeautifulSoup(r_archives.text, features=BEAUTIFUL_SOUP_FEATURES)
    links_issue = soup_archives.select("#main-content .title")

    urls_issue = map(lambda l: l.attrs['href'], links_issue)

    for url_issue in urls_issue:
        scrape_issue(q, 'https:' + url_issue)


def scrape_issue(q: Queue[PaperScraperResponse], url_issue: str):
    """
    Using HTTP requests get DOIs from a single issue in the SCPE archive.
    :param q: Parallel listener into which to return found data.
    :param url_issue: URL to the issue on scpe.org.
    :return: List of all DOIs present in this issue.
    """

    r_issue = requests.get(url_issue)

    if r_issue.status_code != HTTPStatus.OK:
        raise Exception(f"Issue {{ {url_issue} }} read error")

    soup_issue = BeautifulSoup(r_issue.text, features=BEAUTIFUL_SOUP_FEATURES)
    links_paper = soup_issue.select(".article-summary .media-heading>a")

    urls_paper = map(lambda l: l.attrs['href'], links_paper)

    for url_paper in urls_paper:
        scrape_paper(q, 'https:' + url_paper)


def scrape_paper(q: Queue[PaperScraperResponse], url_paper: str):
    """
    Using HTTP requests get the DOI of paper present under a specific URL on scpe.org.
    :param q: Parallel listener into which to return found data.
    :param url_paper: URL of the paper from which DOI to scrape.
    :return: DOI of the paper related to the URL.
    """

    def find_doi(html: BeautifulSoup) -> str:
        meta_doi = html.find("meta", {"name": "DC.Identifier.DOI"})
        doi = meta_doi.attrs['content']
        return doi

    def find_abstract(html: BeautifulSoup) -> str:
        meta_abstract = html.find("meta", {"name": "DC.Description"})
        abstract = meta_abstract.attrs['content']
        return abstract

    def find_keywords(html: BeautifulSoup) -> List[str]:
        result = []
        for meta_keyword in html.findAll("meta", {"name": "DC.Subject"}):
            keywords = meta_keyword.attrs['content']
            for keyword in keywords.split(","):
                result.append(keyword)
        return result

    def find_authors(html: BeautifulSoup) -> List[AuthorScraperResponse]:
        metadata = html.select("head meta[name^=\"citation_author\"]")
        # In the metadata there begins a list of entries of names "citation_author" and "citation_author_institution".
        # Each "citation_author_institution" entry refers to the author stated in the preceding entry.
        #
        # The approach below iterates over these entries and creates a dict, which is then mapped to authors list.

        authors = {}
        last_author = None
        for entry in metadata:
            if entry.attrs['name'] == 'citation_author':
                # New author entry. The following institution will relate to them.
                name = entry.attrs['content']
                authors[name] = None
                last_author = name

            elif entry.attrs['name'] == 'citation_author_institution':
                # Institution related to the last author
                inst = entry.attrs['content']

                assert last_author is not None
                if authors[last_author] is not None:
                    logging.log(logging.WARNING, f"Multiple institutions for one author: (author: {last_author}, inst1: {authors[last_author]}, inst2: {inst}")

                authors[last_author] = inst.strip("\"").replace(" ", "_")

        result = []
        for author, institution in authors.items():
            result.append(AuthorScraperResponse(author, institution))
        return result

    def find_pdf_url(html: BeautifulSoup) -> Optional[str]:
        pdf_url_a = html.select_one("div.download a")
        if pdf_url_a is None:
            return None

        pdf_url = pdf_url_a.attrs['href']
        return 'https:' + pdf_url

    r_paper = requests.get(url_paper)

    if r_paper.status_code != HTTPStatus.OK:
        raise Exception(f"Paper {{ {url_paper} }} read error")

    soup_paper = BeautifulSoup(r_paper.text, features=BEAUTIFUL_SOUP_FEATURES)
    scraped = PaperScraperResponse(
        url=url_paper,
        abstract_text=find_abstract(soup_paper),
        doi=find_doi(soup_paper),
        keywords=find_keywords(soup_paper),
        pdf_url=find_pdf_url(soup_paper),
        authors=find_authors(soup_paper)
    )

    q.put(scraped)
