# fscacher

Caching solution for functions that operate on the file system.

## Installation

`pip install semantic-fscacher`


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
-   `digest`: Function with arguments `(stream, )` and return value of type `str`
    for digesting function call signature as well as the contents of serialized
    files
-   `protocol`: Use predefined functions for `key`, `dump`, `load` and `digest`.
    The only implemented protocol scheme is `filename`, which is presented below.
    If both protocol and explicit functions are set, the explicit functions takes
    presedence.
    
If any of the arguments `key`, `dump`, `load` or `digest` are set to
`"default"`, the functions defined by the `cache.defaults` dict are used
instead.

Default key function is constructed as follows:
1.  Arguments and keyword arguments (both keys and values) are converted to
    string by the `str` function. Numpy arrays are converted to lists before
    conversion.
2.  Any arguments which are too long (> 22 chars) or contain invalid characters
    (`= \/:*?"<>|`) are utf-8 encoded and converted to a 64-bit truncated
    sha256 hash.
3.  Keyword arguments are joined as key-value pairs of the form `k=v`.
4.  If short enough, the key is the function name followed by the
    space-separated argument list. If too long, the key is the function
    name followed by the full sha256 hash of the space-separated argument
    list.

Default dump and load functions are from the python pickle module.

Default digest function is sha256.

Except from the default functions, the only implemented protocol of pre-defined
functions is `filename`. In this protocol, the return value is interpreted as
the name of a temporary file, which means that serialization is not necessary.
`dump` simply moves the file to the index location, and `load` returns the file
name as a string. `digest` and `key` are defined as the default functions.
Optionally, one may use `filename/<suffix>` in place of `filename`, in which
the `key` function is modified to append `<suffix>` to the index file name.
