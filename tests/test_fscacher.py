import fscacher
from pathlib import Path


def unlink(p):
    try:
        Path(p).unlink()
    except FileNotFoundError:
        pass


class Test_Cache_when_filename_protocol:
    def test_renames_file(self):
        def make_hello_file():
            with open('testfile.txt', 'w') as f:
                f.write("Hello")
            return 'testfile.txt'

        cache = fscacher.Cache('.')
        memfn = cache.memoize(make_hello_file, protocol='filename')
        new_fname = memfn()

        assert str(new_fname) != 'testfile.txt'
        assert Path(new_fname).exists()

        try:
            with open(new_fname, 'r') as file:
                assert file.read() == "Hello"
        finally:
            unlink(new_fname)

    def test_recomputes_only_once(self):
        num_called = [0]

        def make_hello_file_and_count():
            num_called[0] += 1
            with open('testfile.txt', 'w') as f:
                f.write("Hello")
            return 'testfile.txt'

        cache = fscacher.Cache('.')
        memfn = cache.memoize(make_hello_file_and_count, protocol='filename')

        fname = memfn()

        try:
            assert memfn() == fname
            assert memfn() == fname
            assert num_called[0] == 1
        finally:
            unlink(fname)

    def test_param_names_are_in_new_filename(self):
        def store_arguments_in_file(a, b, c=0):
            with open('testfile.txt', 'w') as f:
                f.write(str(a) + str(b) + str(c))
            return 'testfile.txt'

        cache = fscacher.Cache('.')
        memfn = cache.memoize(store_arguments_in_file, protocol='filename')
        fname = memfn('hello', b=1.0)
        unlink(fname)

        assert str(fname) == "store_arguments_in_file hello b=1.0"

    def test_can_append_suffix(self):
        def make_hello_file():
            with open('testfile.txt', 'w') as f:
                f.write("Hello")
            return 'testfile.txt'

        cache = fscacher.Cache('.')
        memfn = cache.memoize(make_hello_file, protocol='filename/.csv')
        fname = memfn()
        unlink(fname)

        assert str(fname).endswith(".csv")

    def test_accepts_directory_as_return_value(self):
        def make_hellofile_in_subdir():
            import os
            os.mkdir('./testdir')
            with open('./testdir/testfile.txt', 'w') as f:
                f.write("Hello")
            return './testdir'

        cache = fscacher.Cache('.')
        memfn = cache.memoize(make_hellofile_in_subdir, protocol='filename')
        dirname = memfn()
        dirpath = Path(dirname)

        assert dirpath.exists()
        assert dirpath.is_dir()

        try:
            assert dirpath.name == "make_hellofile_in_subdir"
            assert [f.name for f in dirpath.iterdir()] == ['testfile.txt']
        finally:
            for fname in list(dirpath.iterdir()):
                unlink(fname)
            dirpath.rmdir()
