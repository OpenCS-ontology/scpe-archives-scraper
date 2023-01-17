from http import HTTPStatus
from queue import Empty

from api_caller import call_doi_api
from doi_api_model import doi_api_decoder
from model import DataModel
from model_factory import create_paper_model
from paper_scraper import get_paper_queue
from rdf_serializer import RDFSerializer


def main():
    paper_q, alive_checker = get_paper_queue()

    while alive_checker():
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
                doi_response_paper_model = doi_api_decoder(doi_api_response.content)

                # Here, ORCID could be supplemented for authors and ROR for affiliations (as well as GRID).
                # However, it won't be implemented right now, as incorrect results could arise.

                paper_model = create_paper_model(scraped_paper, doi_response_paper_model)
                data_model = DataModel(paper_model.get_id() + '.ttl')
                data_model.add_paper(paper_model)
                data_model.serialize(RDFSerializer())
        except Empty:
            pass

    print("Process finished")


if __name__ == '__main__':
    main()
