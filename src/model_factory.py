from typing import List

from urllib.parse import quote

import model
import doi_api_model as doi_api
import paper_scraper as scraper


def create_author_model(scraper_author: scraper.AuthorScraperResponse,
                        doi_api_author: doi_api.AuthorDoiResponse
                        ) -> model.AuthorModel:
    """
    Factory method for model.AuthorModel, combining information from two
    author models: paper_scraper.AuthorScraperResponse and doi_api_model.AuthorDoiResponse.

    :param scraper_author: Author model got from scraping the SCPE Archives.
    :param doi_api_author: Author model got from scraping the DOI api.
    :return: The combined author model object.
    """

    result_affiliations = set()
    if scraper_author.affiliation is not None:
        affiliation = model.AffiliationModel(
            name=quote(scraper_author.affiliation),
            # Identifiers are left empty, because the data is not provided by SCPE website.
            identifiers=[]
        )
        result_affiliations.add(affiliation)

    result = model.AuthorModel(
        affiliations=result_affiliations,
        family_name=quote(doi_api_author.family_name),
        given_name=quote(doi_api_author.given_name),
        orcid=doi_api_author.orcid
    )
    return result


def create_paper_model(scraper_paper: scraper.PaperScraperResponse,
                       doi_api_paper: doi_api.PaperDoiResponse
                       ) -> model.PaperModel:
    """
    Factory method for model.PaperModel, combining information from two
    paper models: paper_scraper.PaperScraperResponse and doi_api_model.PaperDoiResponse.

    :param scraper_paper: Paper model got from scraping the SCPE Archives.
    :param doi_api_paper: Paper model got from scraping the DOI api.
    :return: The combined paper model object.
    """

    # Sorting OrderedDicts by author's name.
    scraper_author_dict = {author.name: author for author in scraper_paper.authors}
    doi_author_dict = {author.name: author for author in doi_api_paper.authors}

    if sorted(scraper_author_dict.keys()) != sorted(doi_author_dict.keys()):
        # TODO: New method for authors, as mismatches happen. Just merge these dicts.
        raise RuntimeError(f"Authors' names mismatch.\nFrom SCPE scraper: {sorted(scraper_author_dict.keys())}\nFrom DOI api scraper: {sorted(doi_author_dict.keys())}")

    zipped_authors = [
        (author, doi_author_dict[author.name])
        for author in scraper_author_dict.values()
    ]

    result_authors: List[model.AuthorModel] = [
        create_author_model(scraper_author, doi_api_author)
        for (scraper_author, doi_api_author) in zipped_authors
    ]

    result = model.PaperModel(
        abstract_text=scraper_paper.abstract_text,
        authors=set(result_authors),
        created=doi_api_paper.date,
        doi=scraper_paper.doi,
        endingPage=int(doi_api_paper.ending_page),
        keywords=set(scraper_paper.keywords),
        pdf_url=scraper_paper.pdf_url,
        startingPage=int(doi_api_paper.starting_page),
        title=quote(doi_api_paper.title.strip('"')),
        url=scraper_paper.url,
        volume=int(doi_api_paper.volume)
    )
    return result
