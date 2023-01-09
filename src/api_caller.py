import requests

DOI_PREFIX = "https://doi.org/"
ORCID_SEARCH_TEMPLATE = "https://pub.orcid.org/v3.0/expanded-search/?q=%s&start=0&rows=10"


def call_doi_api(doi: str) -> requests.Response:
    url_call = DOI_PREFIX + doi
    r_rdf = requests.get(url_call, headers={"Accept": "text/turtle"})
    return r_rdf