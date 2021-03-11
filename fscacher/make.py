
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
        default='fscacher',
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
        default='fscacher.key',
    )
    args = parser.parse_args()
    print(args)
