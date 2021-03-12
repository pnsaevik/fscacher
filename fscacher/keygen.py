import hashlib
import re


def key(func, args, kwargs):
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
    k = (fn_name + " " + all_args_str).rstrip()

    # Use alternative key if too long
    if len(k) > 200:
        k = fn_name + " " + sha256(all_args_str)

    return k


def key_content(func, stream):
    page_size = 65536
    hasher = hashlib.sha256()

    read_data = stream.read(page_size)
    while read_data:
        hasher.update(read_data)
        read_data = stream.read(page_size)

    return func.__name__ + " " + hasher.digest().hex()


def sha256(s: str, bits=256):
    hasher = hashlib.sha256()
    hasher.update(s.encode('utf-8'))
    return hasher.digest().hex()[:bits // 4]
