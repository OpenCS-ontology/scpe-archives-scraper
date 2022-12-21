import requests

API_PREFIX = "https://doi.org/"


def call_api(doi: str) -> requests.Response:
    url_call = API_PREFIX + doi
    r_rdf = requests.get(url_call, headers={"Accept": "text/turtle"})
    return r_rdf
