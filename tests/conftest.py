import os
import hashlib
import inspect


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "slow: mark tests as slow (deselect with 'm \"not slow\"')"
    )


def fixturepath(*f):
    fp = os.path.join(os.path.dirname(__file__), 'fixtures')
    return os.path.join(fp, *f)


def outpath(*f):
    op = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(op, *f)


def filehash(fname):
    with open(fname, 'rb') as file:
        return get_hash_from_file(file).hex()


def get_hash_from_file(file):
    page_size = 65536
    hasher = hashlib.sha256()

    read_data = file.read(page_size)
    while read_data:
        hasher.update(read_data)
        read_data = file.read(page_size)

    return hasher.digest()


def snapshotmatch(fname):
    basename = os.path.basename(fname)
    snapname = fixturepath('snapshots', basename)
    if not os.path.exists(snapname):
        return False
    return filehash(fname) == filehash(snapname)


def caller_name(skip=2):
    """Get a name of a caller in the format module.class.method

       `skip` specifies how many levels of stack to skip while getting caller
       name. skip=1 means "who calls me", skip=2 "who calls my caller" etc.

       An empty string is returned if skipped levels exceed stack height
    """
    stack = inspect.stack()
    start = 0 + skip
    if len(stack) < start + 1:
        return ''
    parentframe = stack[start][0]

    name = []
    module = inspect.getmodule(parentframe)
    # `modname` can be None when frame is executed directly in console
    if module:
        name.append(module.__name__)
    # detect classname
    if 'self' in parentframe.f_locals:
        # I don't know any way to detect call from the object method
        # XXX: there seems to be no way to detect static method call - it will
        #      be just a function call
        name.append(parentframe.f_locals['self'].__class__.__name__)
    codename = parentframe.f_code.co_name
    if codename != '<module>':  # top level usually
        name.append(codename)  # function or a method
    del parentframe
    return ".".join(name)


class tempfile:
    def __init__(self, extension='', fname=None, delete=True, folder=False):
        if fname is None:
            fname = caller_name(skip=2)
        self.fname_full = outpath(fname + extension)
        self.folder = folder
        self.delete = delete

    def __enter__(self):
        if self.folder:
            try:
                os.mkdir(self.fname_full)
            except FileExistsError:
                pass

        return self.fname_full

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type == AssertionError:
            # Return without deleting the tempfile if a pytest assert exception
            return

        try:
            if self.delete:
                if self.folder:
                    for root, dirs, files in os.walk(self.fname_full,
                                                     topdown=False):
                        for name in files:
                            os.remove(os.path.join(root, name))
                        for name in dirs:
                            os.rmdir(os.path.join(root, name))
                    os.rmdir(self.fname_full)
                else:
                    os.remove(self.fname_full)
        except OSError:
            pass
