from itertools import islice


def distribute(data: list, chunk_size: int = 2) -> list:
    it = iter(data)
    return [
        list(islice(it, chunk_size))
        for _ in range((len(data) + chunk_size - 1) // chunk_size)
    ]
