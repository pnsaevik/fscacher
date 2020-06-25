from pathlib import Path
import hashlib
import shutil


class Cache:
    def __init__(self, path=None):
        self.path = Path(path)
        self.defaults = dict(
            key=_default_key,
            digest=_default_digest,
        )

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
            funcs['key'] = lambda f, a, kw: defkey(f, a, kw) + suffix
            funcs['dump'] = shutil.move
            funcs['load'] = lambda p: Path(p)

        return funcs['key'], funcs['dump'], funcs['load'], funcs['digest']


def _default_key(func, args, kwargs):
    def nstr(o):
        if hasattr(o, 'tolist'):
            return str(o.tolist())
        else:
            return str(o)

    # Build string components of key
    fn_name = func.__name__
    args_strs = [nstr(e) for e in args]
    kwargs_kv = [(nstr(k), nstr(v)) for k, v in kwargs.items()]
    kwargs_strs = [k + '=' + v for k, v in kwargs_kv]
    key = " ".join([fn_name] + args_strs + kwargs_strs)

    # Validate
    import re
    args_merge = "".join([fn_name] + args_strs + [k + v for k, v in kwargs_kv])
    valid = (len(key) < 200) and (not re.search(r'[\\/:*?"<>| =]', args_merge))
    if not valid:
        return _default_digest(key)
    else:
        return key


def _default_digest(s: str):
    hasher = hashlib.sha256()
    hasher.update(s.encode('utf-8'))
    return hasher.digest().hex()
