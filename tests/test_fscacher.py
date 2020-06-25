import fscacher


def unlink(p):
    try:
        p.unlink()
    except FileNotFoundError:
        pass


class Test_Cache:
    def test_renames_file(self):
        def fn():
            with open('testfile.txt', 'w') as f:
                f.write("Hello")
            return 'testfile.txt'

        cache = fscacher.Cache('.')
        memfn = cache.memoize(fn, protocol='filename')
        new_fname = memfn()

        assert str(new_fname) != 'testfile.txt'
        assert new_fname.exists()

        try:
            with open(new_fname, 'r') as file:
                assert file.read() == "Hello"
        finally:
            unlink(new_fname)

    def test_recomputes_only_once(self):
        num_called = [0]

        def fn():
            num_called[0] += 1
            with open('testfile.txt', 'w') as f:
                f.write("Hello")
            return 'testfile.txt'

        cache = fscacher.Cache('.')
        memfn = cache.memoize(fn, protocol='filename')

        fname = memfn()

        try:
            assert memfn() == fname
            assert memfn() == fname
            assert num_called[0] == 1
        finally:
            unlink(fname)

    def test_param_names_are_in_new_filename(self):
        def fn(a, b, c=0):
            with open('testfile.txt', 'w') as f:
                f.write(str(a) + str(b) + str(c))
            return 'testfile.txt'

        cache = fscacher.Cache('.')
        memfn = cache.memoize(fn, protocol='filename/.txt')
        fname = memfn('hello', b=1.0)
        unlink(fname)

        assert str(fname) == "fn hello b=1.0.txt"

    def test_accepts_directory_as_return_value(self):
        def fn():
            import os
            os.mkdir('./testdir')
            with open('./testdir/testfile.txt', 'w') as f:
                f.write("Hello")
            return './testdir'

        cache = fscacher.Cache('.')
        memfn = cache.memoize(fn, protocol='filename')
        dirname = memfn()

        try:
            assert dirname.exists()
            assert dirname.is_dir()
            assert dirname.name == "fn"
            assert [f.name for f in dirname.iterdir()] == ['testfile.txt']
        finally:
            for fname in list(dirname.iterdir()):
                unlink(fname)
            dirname.rmdir()
