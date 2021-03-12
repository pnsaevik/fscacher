from pathlib import Path
import hashlib
import shutil
import re


class Cache:
    def __init__(self, path=None, key=None):
        self.path = Path(path)
        self.defaults = dict(
            key=key or _default_key,
            digest=_default_digest,
        )

    def __contains__(self, item):
        return self.path.joinpath(str(item)).exists()

    def memoize(self, func, key='default', dump='default', load='default',
                digest='default', protocol=None):

        key, dump, load, digest = self._interpret_options(
            key, dump, load, digest, protocol)

        def cached_func(*args, **kwargs):
            k = key(func, args, kwargs)
            path = self.path.joinpath(k)
            if not path.exists():
                result = func(*args, **kwargs)
                dump(result, path)
            return load(path)

        cached_func.key = lambda *args, **kwargs: key(func, args, kwargs)
        return cached_func

    def _interpret_options(self, key, dump, load, digest, protocol):
        funcs = self.defaults.copy()
        if key != 'default':
            funcs['key'] = key
        if dump != 'default':
            funcs['dump'] = dump
        if load != 'default':
            funcs['load'] = load
        if digest != 'default':
            funcs['digest'] = digest

        defkey = funcs['key']

        if isinstance(protocol, str) and protocol.startswith('filename'):
            try:
                suffix = protocol[protocol.index('/') + 1:]
            except ValueError:
                suffix = ""
            funcs['key'] = lambda f, a, kw: (defkey(f, a, kw) + suffix).strip()
            funcs['dump'] = shutil.move
            funcs['load'] = lambda p: str(p)

        return funcs['key'], funcs['dump'], funcs['load'], funcs['digest']


def _default_key(func, args, kwargs):
    # Define string conversion
    def strconv(o):
        # Convert any numpy arguments to list
        if hasattr(o, 'tolist') and callable(o.tolist):
            o = o.tolist()

        ostr = str(o)

        # Hashconvert if too long or contains invalid chars
        if len(ostr) > 22 or re.search(r'[\\/:*?"<>| =]', ostr):
            ostr = sha256(ostr, 64)
        return ostr

    # Convert arguments to string
    args_strs = [strconv(e) for e in args]
    kwargs_strs = [f'{strconv(k)}={strconv(v)}' for k, v in kwargs.items()]

    # Build default key
    fn_name = func.__name__
    all_args_str = " ".join(args_strs + kwargs_strs)
    key = fn_name + " " + all_args_str

    # Use alternative key if too long
    if len(key) > 200:
        key = fn_name + " " + sha256(all_args_str)

    return key


def sha256(s: str, bits=256):
    hasher = hashlib.sha256()
    hasher.update(s.encode('utf-8'))
    return hasher.digest().hex()[:bits // 4]


def _default_digest(key: str):
    return sha256(key, 64)
