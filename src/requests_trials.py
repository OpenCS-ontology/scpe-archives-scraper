import requests


def get(url: str, times: int = 5, *args, **kwargs) -> requests.Response:
    try_count = 0
    while True:
        try:
            response = requests.get(url, *args, **kwargs)
            break
        except requests.exceptions.ConnectionError as e:
            try_count += 1
            if try_count >= times:
                raise e
    return response
