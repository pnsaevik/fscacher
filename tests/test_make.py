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

    def test_can_generate_outfile(self):
        with runmake('makefile_simple.txt', outfile='out.txt') as outdir:
            assert os.path.exists(os.path.join(outdir, 'out.txt'))

    def test_renames_outfiles(self):
        with runmake('makefile_simple.txt') as outdir:
            fnames = os.listdir(outdir)
            assert 'jsondump something' in fnames
            assert 'jsondump 123' in fnames


class Test_parse_makeline:
    def test_finds_funcname_when_args(self):
        cmd = make.parse_makeline("package.module.func(arg1, arg2)")
        assert cmd['funcname'] == "package.module.func"

    def test_finds_funcname_when_no_args(self):
        cmd = make.parse_makeline("package.module.func()")
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


class Test_get_makeline_funccall:
    def test_evaluates_function(self):
        fn_name = make.__name__ + '.' + make.get_makeline_funccall.__name__
        cmd = dict(
            funcname=fn_name,
            args=dict(names=['myfile', None], values=[None, 2]),
        )
        func, args, kwargs = make.get_makeline_funccall(cmd, dict())
        assert func == make.get_makeline_funccall

    def test_evaluates_variable_names(self):
        fn_name = make.__name__ + '.' + make.get_makeline_funccall.__name__
        varnames = dict(myfile='myfile.txt')
        cmd = dict(
            funcname=fn_name,
            args=dict(names=['myfile', None], values=[None, 2]),
        )
        func, args, kwargs = make.get_makeline_funccall(cmd, varnames)
        assert args == ('myfile.txt', 2)
        assert kwargs == dict()


class Test_load_funcname:
    def test_can_load_function(self):
        fn = make.load_funcname('sys.exit')
        assert callable(fn)


@contextlib.contextmanager
def runmake(fname, outfile=None):
    outdir = conftest.outpath(fname + '_tmpdir')
    try:
        os.makedirs(outdir, exist_ok=True)
        orgfile = conftest.fixturepath(fname)
        newfile = os.path.join(outdir, fname)
        shutil.copy(orgfile, newfile)
        make.make(newfile, outfile_fname=outfile)
        yield outdir
    finally:
        shutil.rmtree(outdir, ignore_errors=True)
