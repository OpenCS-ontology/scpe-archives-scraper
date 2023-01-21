import logging
from typing import Optional

from requests import Response
from requests.exceptions import ConnectionError

import requests_trials as requests


DOI_PREFIX = "https://doi.org/"

# ORCID_SEARCH_TEMPLATE = "https://pub.orcid.org/v3.0/expanded-search/?q=%s&start=0&rows=1"
# ROR_SEARCH_TEMPLATE = "https://api.ror.org/organizations?page=1&query=%s"


def call_doi_api(doi: Optional[str]) -> Response:
    """
    Call the https://doi.org api and get a turtle file with the Response.

    :param doi: Optional string with the requested DOI. If None, returns I AM A TEAPOT response.
    """
    if doi is not None:
        url_call = DOI_PREFIX + doi

        try:
            r_rdf = requests.get(url_call, headers={"Accept": "text/turtle"})
            return r_rdf
        except ConnectionError as e:
            logging.warning(f"DOI api call failure: {str(e)}")

    r = Response()
    r.status_code = 418  # I AM A TEAPOT
    return r
