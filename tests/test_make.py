import contextlib
import shutil
import os
from . import conftest
from fscacher import make


class Test_make:
    def test_generates_files(self):
        with runmake('makefile_simple.txt') as outdir:
            fnames = os.listdir(outdir)
            assert len(fnames) == 4  # makefile + 3 result files


class Test_parse_makeline:
    def test_finds_funcname(self):
        cmd = make.parse_makeline("package.module.func(arg1, arg2)")
        assert cmd['funcname'] == "package.module.func"

    def test_finds_args(self):
        cmd = make.parse_makeline('m.fn(arg1, !arg2, [arg3], 4, 5.25, "6")')
        assert cmd['arglist'] == 'arg1, !arg2, [arg3], 4, 5.25, "6"'
        assert cmd['args']['names'] == ["arg1", "arg2", "arg3", None, None, None]
        assert cmd['args']['values'] == [None, None, None, 4, 5.25, "6"]
        assert cmd['args']['expr'] == ["arg1", "!arg2", "[arg3]", "4", "5.25", '"6"']
        assert cmd['args']['excl'] == [False, True] + [False] * 4
        assert cmd['args']['bracket'] == [False, False, True] + [False] * 3

    def test_finds_modifiers(self):
        cmd = make.parse_makeline("package.module.func(arg1, arg2) MOD1, MOD2=4")
        assert cmd['modlist'] == "MOD1, MOD2=4"

    def test_finds_varname(self):
        cmd = make.parse_makeline("myvar = package.module.func(arg1, arg2)")
        assert cmd['varname'] == 'myvar'


class Test_load_funcname:
    def test_can_load_function(self):
        fn = make.load_funcname('sys.exit')
        assert callable(fn)


@contextlib.contextmanager
def runmake(fname):
    outdir = conftest.outpath(fname + '_tmpdir')
    prevdir = os.curdir
    try:
        os.makedirs(outdir, exist_ok=True)
        os.chdir(outdir)
        orgfile = conftest.fixturepath(fname)
        newfile = os.path.join(outdir, fname)
        shutil.copy(orgfile, newfile)
        make.make(newfile)
        yield outdir
    finally:
        os.chdir(prevdir)
        shutil.rmtree(outdir, ignore_errors=True)
