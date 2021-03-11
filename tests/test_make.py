from fscacher import make




class Test_parse_makeline:
    def test_finds_funcname(self):
        cmd = make.parse_makeline("package.module.func(arg1, arg2)")
        assert cmd['funcstr'] == "package.module.func"

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


