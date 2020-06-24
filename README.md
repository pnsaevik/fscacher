# fscacher

Caching solution for functions that operate on the file system.

## Installation

`pip install <path to repository>`


## Command line usage

```
cacherun expensive_script arg1 arg2 ...
```

When `fscacher` is called, a list of subdirectories of the current directory is
obtained. If there is a subdirectory matching the function call, nothing
happens. Otherwise, the subdirectory is created and the script
`expensive_script` is executed within the newly created directory.


## Usage

Simple usage: 

```
from fscacher import Cache

cache = Cache(cache_path)
fn = cache.memoize(expensive_fn)

result = fn("arg1", "arg2")
```
When `fn` is called the first time, the function `expensive_fn` is evaluated
and its return value is serialized and stored at `cache_path`. Subsequent
calls to `fn` deserializes the stored result instead of re-evaluating
`expensive_fn`.

Optional arguments to `memoize` include:
-   `key`: Function with arguments `(func, args, kwargs)` and return value of
    type `str`, used to create the function call signature
-   `dump`: Function with arguments `(return_value, filename)` and no return
    value for serializing the result of `expensive_fn`
-   `load`: Function with arguments `(filename, )` for de-serializing the
    binary data on disk as a return value
-   `hash`: Function with arguments `(stream, )` and return value of type `str`
    for digesting function call signature as well as the contents of serialized
    files
-   `protocol`: Use predefined functions for `key`, `dump`, `load` and `hash`.
    A list of known protocol schemes are presented below. If both protocol and
    explicit functions are set, the explicit functions takes presedence.
    
If any of the arguments `key`, `dump`, `load` or `hash` are set to `"default"`,
the functions defined by the `cache.defaults` dict are used instead.

Default key function returns a string starting with the function name, followed
by an space-separated argument list. Arguments are converted to string by
the `str` function. Numpy arrays are converted to lists before conversion.
Keyword arguments are presented as `k=v` where `k` is the key and `v` is the
value. If the resulting string is too long (>200) or contain invalid characters
(`\/:*?"<>|`) or is non-parsable (spaces or `=` within arguments), it is utf-8
encoded and converted to a hash.  

Default dump and load functions are from the python pickle module.

Default hash function is based on sha256 from the hashlib module.

Implemented protocols include:
-   `filename/<suffix>`: Return value is interpreted as the name of a temporary
    file, which should have the suffix `<suffix>`, including any leading dot.
    `key` is default key, except that `<suffix>` is appended. `dump` moves the
    file to the index location. `load` returns the file name as a `pathlib`
    path.
-   `filehash/<suffix>`: Return value is interpreted as the name of a temporary
    file, which should have the suffix `<suffix>`, including any leading dot.
    `key` is default key with the suffix `.hash` appended. `dump` computes the
    hash of the temporary file and renames it to the hash value (unless already
    present). Thereafter, it copies the file (as a hardlink if possible) to the
    location specified by `key`, except that `.hash` is replaced by `<suffix>`.
    Finally, the hash is stored as a string (lowercase hex) at the location
    specified by `key` (the index location). `load` returns the contents of the
    file at the index location and interprets it as a `pathlib` path. In the
    end, this protocol works like `filename/<suffix>`, except that multiple
    function calls can be mapped to the same file if their return value has
    equal contents.
