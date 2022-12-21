import io
import lightrdf


def decode_turtle(data: bytes):
    parsed = lightrdf.RDFDocument(io.BytesIO(data), parser=lightrdf.turtle.PatternParser)
    triples = list(parsed.search_triples(None, None, None))
    print(triples)
