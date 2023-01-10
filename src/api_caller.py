from typing import Optional

import requests


DOI_PREFIX = "https://doi.org/"

ORCID_SEARCH_TEMPLATE = "https://pub.orcid.org/v3.0/expanded-search/?q=%s&start=0&rows=1"
ROR_SEARCH_TEMPLATE = "https://api.ror.org/organizations?page=1&query=%s"


def call_doi_api(doi: str) -> requests.Response:
    url_call = DOI_PREFIX + doi
    r_rdf = requests.get(url_call, headers={"Accept": "text/turtle"})
    return r_rdf


# def try_get_orcid(first_name: str, last_name: str, affiliation: Optional[str]) -> Optional[str]:
#     url_call = ORCID_SEARCH_TEMPLATE % author_name
#     r_json = requests.get(url_call)
#
#     return None


