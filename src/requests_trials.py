import requests


def get(url: str, times: int = 5, *args, **kwargs) -> requests.Response:
    """
    Execute a requests.get call a number of times,
    to lessen the likelihood of failure.
    :return: Got response.
    :throws: Relevant expression that caused the last failure if the times count got exceeded.
    """
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
