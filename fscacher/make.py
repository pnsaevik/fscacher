import re


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

    make(args.makefile, args.serializer, args.keygen)


def make(makefile, serializer=None, keygen=None):
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

    # Execute build process
    varnames = dict(makefile=makefile)
    for makeline in makelines:
        build(makeline, varnames, dump, load, key, key_content)


def build(makeline, varnames, dump, load, key, key_content):
    cmd = parse_makeline(makeline)
    fn = load_funcname(cmd['funcname'])

    nargs = len(cmd['args']['values'])
    args = [None] * nargs
    for i in range(nargs):
        # Literal argument
        if cmd['args']['values'][i] is not None:
            arg = cmd['args']['values'][i]

        # Pass-directly named argument
        else:
            arg = varnames[cmd['args']['names'][i]]

        args[i] = arg

    result = fn(*args)
    return result


def parse_makeline(makeline):
    m = re.match(r'(^.*?)=(.*?)\((.*?)\)(.*)', makeline)
    if m is None:  # No equals sign
        m = re.match(r'(^)(.*?)\((.*?)\)(.*)', makeline)

    varname = m.group(1).strip()
    funcstr = m.group(2).strip()
    arglist = m.group(3).strip()
    modlist = m.group(4).strip()

    arg_expr = re.split(",\\s*", arglist)
    arg_excl = [s.startswith("!") for s in arg_expr]
    arg_ends = [s[0] + s[-1] for s in arg_expr]
    arg_bracket = [ends == "[]" for ends in arg_ends]

    arg_names = list([s.strip("[]!") for s in arg_expr])
    arg_vals = [None] * len(arg_names)
    for i, s in enumerate(arg_names):
        # String argument
        ends = s[0] + s[-1]
        if ends == "''" or ends == '""':
            arg_names[i] = None
            arg_vals[i] = s[1:-1]

        # Numeric argument
        elif re.match('[0-9].*', s):
            import json
            arg_vals[i] = json.loads(s)
            arg_names[i] = None

        # Otherwise: Named argument

    return dict(
        varname=varname,
        funcname=funcstr,
        arglist=arglist,
        modlist=modlist,
        args=dict(
            names=arg_names,
            expr=arg_expr,
            excl=arg_excl,
            bracket=arg_bracket,
            values=arg_vals,
        ),
    )


def load_funcname(funcname: str):
    pkg_name, fn_name = funcname.rsplit('.', 1)
    import importlib
    pkg = importlib.import_module(pkg_name)
    return getattr(pkg, fn_name)
