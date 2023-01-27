import logging
import re
from dataclasses import dataclass
from http import HTTPStatus
from queue import Queue
from threading import Thread
from typing import List, Optional, Tuple, Callable

from bs4 import BeautifulSoup
from requests.exceptions import ConnectionError

import requests_trials as requests


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

    # Cannot be acquired from meta
    fallback_orcid: Optional[str]


@dataclass
class PaperScraperResponse:
    """
    Model representing the scraped data about the paper.
    """

    # Page's url
    url: str

    # DC.Description
    abstract_text: Optional[str]

    # DC.Identifier.DOI
    doi: Optional[str]

    # DC.Subject
    keywords: List[str]

    # citation_pdf_url
    pdf_url: Optional[str]

    authors: List[AuthorScraperResponse]

    # DC.Date.created
    fallback_created: str

    # DC.Source.Volume
    fallback_volume: Optional[str]

    # citation_firstpage
    fallback_starting_page: Optional[str]

    # citation_lastpage
    fallback_ending_page: Optional[str]

    # DC.Title
    fallback_title: str


def get_paper_queue() -> Tuple[Queue[PaperScraperResponse], Callable[[], bool]]:
    """
    Get a queue into which papers will be scraped.
    Sometimes dummy papers can appear. Their DOI is an empty string, and they should be ignored.
    :return: Queue on which the scraped papers will appear periodically, and a function to check if there will be more items.
    """

    q = Queue()
    t = Thread(target=scrape_all_doi, args=[q])
    t.start()
    return q, lambda: t.is_alive()


def scrape_all_doi(q: Queue[PaperScraperResponse]) -> None:
    """
    Using HTTP requests get DOIs of all articles in the SCPE archives.
    :param q: Parallel listener into which to return found data.
    :return: List of all DOIs in SCPE Archive.
    """

    try:
        r_archives = requests.get(URL_ARCHIVES)
    except ConnectionError as e:
        logging.warning(f"SCPE archive {URL_ARCHIVES} scrape error: {str(e)}")
        return

    if r_archives.status_code != HTTPStatus.OK:
        raise Exception("Archives list read error")

    soup_archives = BeautifulSoup(r_archives.text, features=BEAUTIFUL_SOUP_FEATURES)
    links_issue = soup_archives.select("#main-content .title")

    urls_issue = map(lambda l: l.attrs['href'], links_issue)

    for url_issue in urls_issue:
        scrape_issue(q, 'https:' + url_issue)


def scrape_issue(q: Queue[PaperScraperResponse], url_issue: str) -> None:
    """
    Using HTTP requests get DOIs from a single issue in the SCPE archive.
    :param q: Parallel listener into which to return found data.
    :param url_issue: URL to the issue on scpe.org.
    :return: List of all DOIs present in this issue.
    """

    try:
        r_issue = requests.get(url_issue)
    except ConnectionError as e:
        logging.warning(f"SCPE issue {url_issue} scrape error: {str(e)}")
        return

    if r_issue.status_code != HTTPStatus.OK:
        raise Exception(f"Issue {{ {url_issue} }} read error")

    soup_issue = BeautifulSoup(r_issue.text, features=BEAUTIFUL_SOUP_FEATURES)
    links_paper = soup_issue.select(".article-summary .media-heading>a")

    urls_paper = map(lambda l: l.attrs['href'], links_paper)

    for url_paper in urls_paper:
        scrape_paper(q, 'https:' + url_paper)


def scrape_paper(q: Queue[PaperScraperResponse], url_paper: str) -> None:
    """
    Using HTTP requests get the DOI of paper present under a specific URL on scpe.org.
    :param q: Parallel listener into which to return found data.
    :param url_paper: URL of the paper from which DOI to scrape.
    :return: DOI of the paper related to the URL.
    """

    def find_doi(html: BeautifulSoup) -> str:
        meta_doi = html.find("meta", {"name": "DC.Identifier.DOI"})
        if meta_doi is None:
            meta_doi = html.find("meta", {"name": "citation_doi"})
        return meta_doi.attrs['content'] if meta_doi is not None else None

    def find_abstract(html: BeautifulSoup) -> Optional[str]:
        meta_abstract = html.find("meta", {"name": "DC.Description"})
        if meta_abstract is None:
            return None
        abstract = meta_abstract.attrs['content']
        return abstract

    def find_keywords(html: BeautifulSoup) -> List[str]:
        result = []
        for meta_keyword in html.findAll("meta", {"name": "DC.Subject"}):
            keywords = meta_keyword.attrs['content']
            for keyword in re.split(r"[,;]", keywords):
                result.append(keyword.strip(".").strip(" "))
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
                    logging.log(logging.WARNING,
                                f"Multiple institutions for one author: (author: {last_author}, inst1: {authors[last_author]}, inst2: {inst}")

                authors[last_author] = inst.strip("\"")

        authors_in_body_with_orcid = html.select("div.author div.orcid")
        name_to_orcid = {}
        for author in authors_in_body_with_orcid:
            orcid_a = author.find('a')
            orcid_url = orcid_a.attrs['href']
            orcid = orcid_url.split('/')[-1]

            strong_name = author.parent.find('strong')
            name_to_orcid[strong_name.contents[0]] = orcid

        result = []
        for author, institution in authors.items():
            # Try to find a fallback ORCID on the page.
            fallback_orcid = None
            if author in name_to_orcid.keys():
                fallback_orcid = name_to_orcid[author]
            result.append(AuthorScraperResponse(author, institution, fallback_orcid))
        return result

    def find_pdf_url(html: BeautifulSoup) -> Optional[str]:
        pdf_url_meta = html.find("meta", {"name": "citation_pdf_url"})

        if pdf_url_meta is None:
            pdf_url_a = html.select_one("div.download a")
            if pdf_url_a is None:
                return None
            pdf_url = pdf_url_a.attrs['href']
        else:
            pdf_url = pdf_url_meta.attrs['content']
        return 'https:' + pdf_url

    def find_created(html: BeautifulSoup) -> str:
        meta = html.find("meta", {"name": "DC.Date.created"})
        return meta.attrs['content']

    def find_volume(html: BeautifulSoup) -> Optional[str]:
        meta = html.find("meta", {"name": "DC.Source.Volume"})
        return meta.attrs['content'] if meta is not None else None

    def find_starting_page(html: BeautifulSoup) -> Optional[str]:
        meta = html.find("meta", {"name": "citation_firstpage"})
        return meta.attrs['content'] if meta is not None else None

    def find_ending_page(html: BeautifulSoup) -> Optional[str]:
        meta = html.find("meta", {"name": "citation_lastpage"})
        return meta.attrs['content'] if meta is not None else None

    def find_title(html: BeautifulSoup) -> str:
        meta = html.find("meta", {"name": "DC.Title"})
        return meta.attrs['content']

    try:
        r_paper = requests.get(url_paper)
    except ConnectionError as e:
        logging.warning(f"SCPE paper {url_paper} scrape error: {str(e)}")
        return

    if r_paper.status_code != HTTPStatus.OK:
        raise Exception(f"Paper {{ {url_paper} }} read error")

    soup_paper = BeautifulSoup(r_paper.text, features=BEAUTIFUL_SOUP_FEATURES)
    scraped = PaperScraperResponse(
        url=url_paper,
        abstract_text=find_abstract(soup_paper),
        doi=find_doi(soup_paper),
        keywords=find_keywords(soup_paper),
        pdf_url=find_pdf_url(soup_paper),
        authors=find_authors(soup_paper),
        fallback_title=find_title(soup_paper),
        fallback_created=find_created(soup_paper),
        fallback_volume=find_volume(soup_paper),
        fallback_ending_page=find_ending_page(soup_paper),
        fallback_starting_page=find_starting_page(soup_paper)
    )

    q.put(scraped)
