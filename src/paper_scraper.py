from dataclasses import dataclass
from http import HTTPStatus
from queue import Queue
from threading import Thread

import requests
from bs4 import BeautifulSoup

URL_ARCHIVES = 'https://www.scpe.org/index.php/scpe/issue/archive'
BEAUTIFUL_SOUP_FEATURES = "html.parser"


def get_paper_queue() -> Queue[PaperScraperResponse]:
    q = Queue()
    t = Thread(target=scrape_all_doi, args=[q])
    t.start()
    return q


def scrape_all_doi(q: Queue[PaperScraperResponse]) -> None:
    """
    Using HTTP requests get DOIs of all articles in the SCPE archives.
    :return: List of all DOIs in SCPE Archive.
    """
    r_archives = requests.get(URL_ARCHIVES)

    if r_archives.status_code != HTTPStatus.OK:
        raise Exception("Archives list read error")

    soup_archives = BeautifulSoup(r_archives.text, features=BEAUTIFUL_SOUP_FEATURES)
    links_issue = soup_archives.select("#main-content .title")

    urls_issue = map(lambda l: l.attrs['href'], links_issue)

    for url_issue in urls_issue:
        scrape_issue(q, url_issue)


def scrape_issue(q: Queue[PaperScraperResponse], url_issue: str):
    """
    Using HTTP requests get DOIs from a single issue in the SCPE archive.
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
        scrape_paper(q, url_paper)


def scrape_paper(q: Queue[PaperScraperResponse], url_paper: str):
    """
    Using HTTP requests get the DOI of paper present under a specific URL on scpe.org.
    :param url_paper: URL of the paper from which DOI to scrape.
    :return: DOI of the paper related to the URL.
    """
    r_paper = requests.get(url_paper)

    if r_paper.status_code != HTTPStatus.OK:
        raise Exception(f"Paper {{ {url_paper} }} read error")

    soup_paper = BeautifulSoup(r_paper.text, features=BEAUTIFUL_SOUP_FEATURES)

    meta_doi = soup_paper.find("meta", {"name": "citation_doi"})
    doi = meta_doi.attrs['content'] if meta_doi is not None else ""

    q.put(PaperScraperResponse(doi, ""))
