import asyncio

from cachetools import TTLCache

# from functools import lru_cache, wraps

# # wasteful
# from concurrent.futures import ThreadPoolExecutor
# def work_in_the_back():
#     def decorator(func):
#         @wraps(func)
#         def wrapper(*args, **kwargs):
#             with ThreadPoolExecutor() as executor:
#                 future = executor.submit(func, *args, **kwargs)
#                 res = future.result()
#             return res
#         return wrapper
#     return decorator


# def ttl_cache(ttl_seconds=300, maxsize=32):
#     def decorator(func):
#         @lru_cache(maxsize=maxsize)
#         def cached(*args, _ttl_hash, **kwargs):
#             return func(*args, **kwargs)

#         @wraps(func)
#         def wrapper(*args, **kwargs):
#             ttl_hash = int(time.time() // ttl_seconds)
#             return cached(*args, _ttl_hash=ttl_hash, **kwargs)

#         return wrapper

#     return decorator


_cache = TTLCache(maxsize=256, ttl=600)
_locks: dict[tuple, asyncio.Lock] = {}


def _lock_for(key: tuple) -> asyncio.Lock:
    # one lock per key to avoid stampedes
    lock = _locks.get(key)
    if lock is None:
        lock = _locks[key] = asyncio.Lock()
    return lock


async def cached_search(fetch_coro, *, category: str, keyword: str):
    key = (category, keyword)

    try:
        return _cache[key]
    except KeyError:
        pass

    async with _lock_for(key):
        # re-check after acquiring lock
        try:
            return _cache[key]
        except KeyError:
            value = await fetch_coro()
            _cache[key] = value
            return value
