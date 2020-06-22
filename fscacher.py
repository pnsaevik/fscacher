import pathlib
import hashlib
import shutil


class Cache:
    def __init__(self, path=None):
        self.path = pathlib.Path(path)

    def memoize(self, func, suffix="", contents=False):
        def cached_func(*args, **kwargs):
            k = key(func, args, kwargs, suffix, contents)
            path = self.path.joinpath(k)
            if not path.exists():
                result = func(*args, **kwargs)
                shutil.move(result, path)
            return path

        return cached_func


def key(func, args, kwargs, suffix, c):
    fn_name = func.__name__
    args_strs = [digest(e, c) for e in args]
    kwargs_strs = [f"{digest(k)}={digest(v, c)}" for k, v in kwargs.items()]
    return "_".join([fn_name] + args_strs + kwargs_strs) + suffix


def digest(element, contents=False):
    if isinstance(element, pathlib.Path):
        hasher = hashlib.sha256()
        if contents:
            with open(str(element), 'br') as file:
                hasher.update(file.read())
            return '+' + hasher.digest().hex()[:16]
        else:
            hasher.update(element.name.encode('utf-8'))
            return '@' + hasher.digest().hex()[:16]
    else:
        return str(element)
