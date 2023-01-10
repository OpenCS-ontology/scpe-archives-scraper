import io
from dataclasses import dataclass
import lightrdf
from typing import List

@dataclass
class AuthorDoiResponse:
    # starting page
    family_name: str
 
    given_name: str

    name: str

    orcid : str        
    
@dataclass
class PaperDoiResponse:
    # starting page
    starting_page: str
 
    ending_page: str

    volume: str

    date : str

    title : str

        
    authors: List[AuthorDoiResponse]



def doi_api_decoder(data: bytes)-> PaperDoiResponse:
    
    parsed = lightrdf.RDFDocument(io.BytesIO(data), parser=lightrdf.turtle.PatternParser)
    triples = list(parsed.search_triples(None, None, None))
    
    
    print(triples)
