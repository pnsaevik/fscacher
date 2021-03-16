# fscacher

Caching solution for functions that operate on the file system, with
human-readable naming scheme for cached files.

## Installation

`pip install semantic-fscacher`


## Features

* Execute a series of python commands which returns serialized results
* Rename results according to the command name and arguments
* Re-use precomputed results
* Define variables in makefile
* Specify suffix to be appended to file names
* (not implemented) Auto-serialization for commands that returns objects
* (not implemented) Deserialization of command arguments
* (not implemented) Rename results according to contents of results (eager evaluation)
* (not implemented) Convert commands to job arrays

## Command line usage

Standard usage is `simplemake [opts] makefile.txt`, where `makefile.txt`
contains a list of dependencies, and `opts` are optional parameters. Run
`simplemake --help` for an overview.

Each line in `makefile.txt` represents a single build step and has the
following format:

```
[varname = ] [!]modulename.funcname(arglist)  [modifier_list]
``` 

The lines in `makefile.txt` are evaluated and executed in the order they appear.

`modulename.funcname` is the fully qualified name of the python function to be
  executed. If the name is preceeded by an exclamation sign `!`, the return value
  is serialized by `simplemake` (see options). Otherwise, the serialization is
  assumed to be performed by the function itself, and the return value is
  assumed to be the path of a temporary file containing the serialized result.
  The temporary file is then renamed by `simplemake` according to its internal
  naming scheme (see options).

`varname` is required if the result of the function evaluation is used by
  subsequent build steps. It can be any valid python variable name, and
  contains the path to the file where the serialized function result is stored.
  There is one predefined varname, `makefile`, which represents the input file
  passed as command line argument. 

`arglist` is a comma-separated list of arguments passed to the python
  function, possibly including varnames from previous build steps. A varname
  from a previous build step is normally passed to the function as a file name.
  There are two exceptions:
  
  * Any varname preceeded by an exclamation mark `!` is deserialized by
    `simplemake` before being passed to the function (see options).
  * Any varname enclosed by square brackets `[]` is assumed to be a
    *jobarray* file. In this case, `simplemake` executes the command
    repeatedly with arguments given by the lines in the jobarray file, and
    returns a summary file containing the file names of the serialized results,
    one file name per line.  

`modifier_list` is an optional comma-separated list of keywords which indicates
  how the function call should be interpreted. A list of possible modifiers is
  given below:

  * `SUFFIX=.suffix`: Appends `.suffix` to the generated key.

  * `EAGER`: Specify eager evaluation, i.e., the function is evaluated regardless
    of any previously cached results. When this parameter is specified, the key
    is generated based on the contents of the file and not the function arguments.


## Usage: memoize

Simple usage: 

```python
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
