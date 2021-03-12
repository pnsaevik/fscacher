from fscacher import keygen


class Test_key:
    def test_when_no_args(self):
        k = keygen.key(keygen.key, (), {})
        assert k == "key"

    def test_when_args_and_kwargs(self):
        k = keygen.key(keygen.key, (1, 2.0, "asdf"), {"a": 1, "b": "hello"})
        assert k == "key 1 2.0 asdf a=1 b=hello"

    def test_when_invalid_args(self):
        k = keygen.key(keygen.key, (1, 2.0, "a*df", "a df", "a" * 50), {})
        assert k == "key 1 2.0 c8f8279ad17c20bd 14c7d13b586b945b 160b4e433e384e05"

    def test_when_long_key(self):
        k = keygen.key(keygen.key, ("*", ) * 20, {})
        assert k == "key e193cc64f08eedec96b6195385ac364cf6da879f5073f2ad89de93300c639cd4"


class Test_key_content:
    def test_empty_stream(self):
        import io
        from hashlib import sha256
        buf = io.BytesIO()
        k = keygen.key_content(keygen.key_content, buf)
        assert k == "key_content " + sha256().digest().hex()
