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
        memfn = cache.memoize(fn)
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
        memfn = cache.memoize(fn)

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
        memfn = cache.memoize(fn, '.txt')
        fname = memfn('hello', b=1.0)
        unlink(fname)

        assert str(fname) == "fn_hello_b=1.0.txt"

    def test_file_param_names_are_converted_to_hashed_basename(self):
        def fn(_):
            with open('testfile.txt', 'w') as f:
                f.write("Hello")
            return 'testfile.txt'

        import pathlib
        import os

        cache = fscacher.Cache('.')
        memfn = cache.memoize(fn)

        fname_1 = memfn(pathlib.Path('nofile.txt'))
        unlink(fname_1)
        fname_2 = memfn(pathlib.Path(os.path.abspath('nofile.txt')))
        unlink(fname_2)

        assert str(fname_1) == "fn_@4895ac421ec60ef4"
        assert str(fname_2) == str(fname_1)

    def test_accepts_directory_as_return_value(self):
        def fn():
            import os
            os.mkdir('./testdir')
            with open('./testdir/testfile.txt', 'w') as f:
                f.write("Hello")
            return './testdir'

        cache = fscacher.Cache('.')
        memfn = cache.memoize(fn)
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

    def test_can_use_file_contents_as_key(self):
        def fn(_):
            with open('testfile.txt', 'w') as f:
                f.write("Hello")
            return 'testfile.txt'

        from pathlib import Path

        d1 = Path('data1.txt')
        d2 = Path('data2.txt')
        d3 = Path('data3.txt')

        with open(d1, 'w') as f1, open(d2, 'w') as f2, open(d3, 'w') as f3:
            f1.write("Test")
            f2.write("Test")
            f3.write("Nothing")

        cache = fscacher.Cache('.')
        memfn = cache.memoize(fn, contents=True)

        fname1 = memfn(d1)
        fname2 = memfn(d2)
        fname3 = memfn(d3)

        try:
            assert fname1 == fname2
            assert fname1 != fname3
        finally:
            for f in [d1, d2, d3, fname1, fname2, fname3]:
                unlink(f)
