from http import HTTPStatus
from queue import Empty

from api_caller import call_doi_api  # , try_get_orcid
from paper_scraper import get_paper_queue
from doi_api_model import doi_api_decoder


def main():
    paper_q = get_paper_queue()
    try:
        while True:
            # Basic paper model
            scraped_paper = paper_q.get(block=True, timeout=10)

            # For timeout to make sense, sometimes a dummy element is thrown in the queue.
            if scraped_paper.doi == "":
                continue

            # DOI api model
            doi_api_response = call_doi_api(scraped_paper.doi)
            if doi_api_response.status_code != HTTPStatus.OK:
                raise ConnectionError(f'Response from API not OK: {doi_api_response.status_code}')
            #doi_response_model = doi_api_decoder(doi_api_response.content)

            # Supplement missing authors' ORCIDs
            # for author in scraped_paper.authors:
            #     # TODO: Change the try_get_orcid arguments after DOI scraping is implemented.
            #     names = author.name.split(sep=' ')
            #     first_name = names[0]
            #     last_name = names[-1]
            #     affiliation = author.affiliation
            #
            #     orcid = try_get_orcid(first_name, last_name, affiliation)
            #     print(orcid)

    except Empty:
        pass

    print("Process finished")


if __name__ == '__main__':
    main()
