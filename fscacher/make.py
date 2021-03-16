import re
import os
import shutil
import json


def runmake():
    import argparse

    parser = argparse.ArgumentParser(
        description='Build a set of files from given dependencies',
    )
    parser.add_argument(
        'makefile',
        type=str,
        help='The file containing the dependencies',
    )
    parser.add_argument(
        '--serializer',
        metavar='S',
        type=str,
        help=(
            'Python module used for serializing data. Must have a public function '
            '`dump(obj, fname)` which serializes the contents of `obj` into the file '
            '`fname`. Must also include a corresponding deserializer function '
            '`obj = load(fname)`. Default functions are `fscacher.dump` '
            'and `fscacher.load`, which utilize the python pickle module. '
        ),
        default=None,
    )
    parser.add_argument(
        '--keygen',
        metavar='K',
        type=str,
        help=(
            'Python function used to generate file names for the build files. Must '
            'have the signature `name = fn(func, args, kwargs)` where `name` is a '
            'valid file name uniquely generated from a function handle `func`, the '
            'positional arguments `args` and the keyword arguments `kwargs`. Default '
            'keygen function is `fscacher.key`, which returns the function name plus '
            'a string representation of the arguments. If they are too long or contain '
            'invalid characters, the arguments are replaced by hash representations. '
        ),
        default=None,
    )
    args = parser.parse_args()
    parser.add_argument(
        '--outfile',
        metavar='O',
        type=str,
        help=(
            'Output file where generated build files are stored, one per line.'
        ),
        default=None,
    )

    make(args.makefile, args.serializer, args.keygen, args.outfile)


def make(makefile, serializer=None, keygen=None, outfile_fname=None):
    # Handle variations on the makefile argument
    if isinstance(makefile, list):
        makelines = makefile
    else:
        with open(makefile, 'r', encoding='utf-8') as f:
            makelines = f.readlines()

    # Handle default arguments
    if serializer is None:
        from . import dump
        from . import load
    else:
        dump = None
        load = None

    # Handle default arguments
    if keygen is None:
        from . import key
        from . import key_content
    else:
        key = None
        from . import key_content

    # Create cache
    import os
    from .fscacher import Cache
    cache = Cache(os.path.dirname(makefile))

    # Execute build process
    varnames = dict(makefile=makefile)
    outfiles = [
        build(makeline, varnames, dump, load, key, key_content, cache)
        for makeline in makelines
    ]

    # Store outfile if specified
    if outfile_fname:
        outfile_path = os.path.join(os.path.dirname(makefile), outfile_fname)
        with open(outfile_path, 'w', encoding='utf-8') as f:
            f.writelines([str(n) + '\n' for n in outfiles])

    return outfiles


def _key_with_suffix(keyfn, suffix):
    if suffix:
        return lambda *args, **kwargs: keyfn(*args, **kwargs) + suffix
    else:
        return keyfn


def build(makeline, varnames, dump, load, key, key_content, cache):
    cmd = parse_makeline(makeline)
    fn, args, kwargs = get_makeline_funccall(cmd, varnames)
    suffix = dict(zip(cmd['mods']['names'], cmd['mods']['values'])).get('SUFFIX', None)

    # Use eager evaluation if specified
    if 'EAGER' in cmd['mods']['names']:
        outfile = cache.eval(
            fn, args, kwargs,
            digest=key_content,
            dump=lambda obj, fname: shutil.move(obj, os.path.join(cache.path, fname)),
        )

    else:
        # Define memoized function
        memfn = cache.memoize(
            fn,
            key=_key_with_suffix(key, suffix),
            dump=lambda obj, fname: shutil.move(obj, os.path.join(cache.path, fname)),
            load=lambda fname: fname,
        )

        # Run memoized function
        outfile = memfn(*args, **kwargs)

    # Store result in variable if requested
    if cmd['varname']:
        varnames[cmd['varname']] = str(outfile)

    return outfile


def get_makeline_funccall(cmd, varnames):
    arg_names_and_vals = zip(cmd['args']['names'], cmd['args']['values'])

    func = load_funcname(cmd['funcname'])
    args = tuple(varnames.get(n, v) for n, v in arg_names_and_vals)
    kwargs = dict()

    return func, args, kwargs


def parse_makeline(makeline):
    # Standard interpretation: var = func(arg1, arg2) MOD1, MOD2=4
    m = re.match(r'(^[a-zA-Z0-9_ ]*?)=(.*?)\((.*?)\)(.*)', makeline)

    # Possibly no `var =` in the beginning of string
    if m is None:
        m = re.match(r'(^)(.*?)\((.*?)\)(.*)', makeline)

    # Four parts of the makeline string
    varname = m.group(1).strip()
    funcstr = m.group(2).strip()
    arglist = m.group(3).strip()
    modlist = m.group(4).strip()

    def parse_argument_list(arg_list):
        # Split by comma + possible whitespace
        arg_items = [a for a in re.split("\\s*,\\s*", arg_list) if a != '']

        # Check if exclamation or brackets are present
        arg_has_exclamation = [s.startswith("!") for s in arg_items]
        arg_start_and_stop = [s[0] + s[-1] for s in arg_items]
        arg_has_bracket = [ends == "[]" for ends in arg_start_and_stop]

        # Parse literal arguments
        arg_names = list([s.strip("[]!") for s in arg_items])
        arg_vals = [None] * len(arg_names)
        for i, s in enumerate(arg_names):
            # String argument
            ends = s[0] + s[-1]
            if ends == "''" or ends == '""':
                arg_names[i] = None
                arg_vals[i] = s[1:-1]

            # Numeric argument
            elif re.match('[0-9].*', s):
                arg_vals[i] = json.loads(s)
                arg_names[i] = None

            # Otherwise: Named argument
            else:
                pass

        return dict(names=arg_names, expr=arg_items, excl=arg_has_exclamation,
                    bracket=arg_has_bracket, values=arg_vals)

    def parse_mod_list(mod_list):
        mod_items = [a.split('=') for a in mod_list.split(',') if a != '']
        mod_names = [a[0].strip() for a in mod_items]
        mod_strval = [a[1].strip() if len(a) > 1 else None for a in mod_items]
        mod_values = [json.loads(a) if a and re.match('[0-9].*', a) else a
                      for a in mod_strval]

        return dict(names=mod_names, values=mod_values)

    return dict(
        varname=varname,
        funcname=funcstr,
        arglist=arglist,
        modlist=modlist,
        args=parse_argument_list(arglist),
        mods=parse_mod_list(modlist),
    )


def load_funcname(funcname: str):
    pkg_name, fn_name = funcname.rsplit('.', 1)
    import importlib
    pkg = importlib.import_module(pkg_name)
    return getattr(pkg, fn_name)
