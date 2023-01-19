import logging
from typing import List, Optional

import model
import doi_api_model as doi_api
import paper_scraper as scraper


def create_author_model(scraper_author: Optional[scraper.AuthorScraperResponse],
                        doi_api_author: Optional[doi_api.AuthorDoiResponse]
                        ) -> model.AuthorModel:
    """
    Factory method for model.AuthorModel, combining information from two
    author models: paper_scraper.AuthorScraperResponse and doi_api_model.AuthorDoiResponse.

    :param scraper_author: Author model got from scraping the SCPE Archives.
    :param doi_api_author: Author model got from scraping the DOI api.
    :return: The combined author model object.
    """

    if scraper_author is None and doi_api_author is None:
        raise RuntimeError("No data to create author from")

    result_affiliations = set()
    if scraper_author is not None and scraper_author.affiliation is not None:
        affiliation = model.AffiliationModel(
            name=scraper_author.affiliation,
            # Identifiers are left empty, because the data is not provided by SCPE website.
            identifiers=[]
        )
        result_affiliations.add(affiliation)

    result = model.AuthorModel(
        affiliations=result_affiliations,
        name=doi_api_author.name
        if doi_api_author is not None and doi_api_author.name is not None
        else (
            scraper_author.name
            if scraper_author is not None
            else None
        ),
        family_name=None if doi_api_author is None else doi_api_author.family_name,
        given_name=None if doi_api_author is None else doi_api_author.given_name,

        orcid=doi_api_author.orcid
        if doi_api_author is not None and doi_api_author.orcid is not None
        else (
            scraper_author.fallback_orcid
            if scraper_author is not None
            else None
        )
    )
    if result.name is None:
        logging.warning(f"!!!Author without a name!!! {result.get_id()}")
    return result


def create_paper_basic_model(scraper_paper: scraper.PaperScraperResponse) -> model.PaperModel:
    """
    Factory method for model.PaperModel,  based solely on information from paper_scraper.PaperScraperResponse.

    :param scraper_paper: Paper model got from scraping the SCPE Archives.
    :return: Basic paper model object.
    """

    result_authors: List[model.AuthorModel] = []
    for scraper_author in scraper_paper.authors:
        result_authors.append(create_author_model(scraper_author, None))

    result = model.PaperModel(
        abstract_text=scraper_paper.abstract_text,
        authors=set(result_authors),
        created=scraper_paper.fallback_created,
        doi=scraper_paper.doi,
        endingPage=scraper_paper.fallback_ending_page,
        keywords=None if scraper_paper.keywords is None else set(scraper_paper.keywords),
        pdf_url=scraper_paper.pdf_url,
        startingPage=scraper_paper.fallback_starting_page,
        title=scraper_paper.fallback_title,
        url=scraper_paper.url,
        volume=scraper_paper.fallback_volume
    )
    return result


def create_paper_model(scraper_paper: scraper.PaperScraperResponse,
                       doi_api_paper: Optional[doi_api.PaperDoiResponse]
                       ) -> model.PaperModel:
    """
    Factory method for model.PaperModel, combining information from two
    paper models: paper_scraper.PaperScraperResponse and doi_api_model.PaperDoiResponse.

    :param scraper_paper: Paper model got from scraping the SCPE Archives.
    :param doi_api_paper: Paper model got from scraping the DOI api.
    :return: The combined paper model object.
    """

    if doi_api_paper is None:
        return create_paper_basic_model(scraper_paper)

    # Sorting OrderedDicts by author's name.
    scraper_author_dict = {author.name: author for author in scraper_paper.authors}
    doi_author_dict = {author.name: author for author in doi_api_paper.authors}

    result_authors: List[model.AuthorModel] = []
    for author_name, doi_api_author in doi_author_dict.items():
        scraper_author = scraper_author_dict[author_name] if author_name in scraper_author_dict.keys() else None
        result_authors.append(create_author_model(scraper_author, doi_api_author))

    result = model.PaperModel(
        abstract_text=scraper_paper.abstract_text,
        authors=set(result_authors),
        created=doi_api_paper.date,
        doi=scraper_paper.doi,
        endingPage=doi_api_paper.ending_page,
        keywords=None if scraper_paper.keywords is None else set(scraper_paper.keywords),
        pdf_url=scraper_paper.pdf_url,
        startingPage=doi_api_paper.starting_page,
        title=scraper_paper.fallback_title.strip('"') if doi_api_paper.title is None else doi_api_paper.title.strip(
            '"'),
        url=scraper_paper.url,
        volume=doi_api_paper.volume
    )
    return result
