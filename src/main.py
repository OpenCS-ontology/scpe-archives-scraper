from http import HTTPStatus
from queue import Empty

from api_caller import call_doi_api
from paper_scraper import get_paper_queue
from turtle_decoder import decode_turtle


def main():
    paper_q = get_paper_queue()
    try:
        while True:
            scraped_paper = paper_q.get(block=True, timeout=10)

            # For timeout to make sense, sometimes a dummy element is thrown in the queue.
            if scraped_paper.doi == "":
                continue

            api_response = call_doi_api(scraped_paper.doi)
            if api_response.status_code != HTTPStatus.OK:
                raise ConnectionError(f'Response from API not OK: {api_response.status_code}')

            decode_turtle(api_response.content)

    except Empty:
        pass

    print("Process finished")


if __name__ == '__main__':
    main()
