from fscacher import serialize
import pytest
import os
import tempfile


class Test_pickle_dumper_loader:
    @pytest.mark.parametrize("item", [123, 3.25], ids=['integer', 'float'])
    def test_dump_load_cycle_gives_identical_item(self, item):
        fid, fname = None, None
        try:
            fid, fname = tempfile.mkstemp()
            serialize.dump_pickle(item, fname)
            load_item = serialize.load_pickle(fname)
            assert load_item == item
        finally:
            try:
                os.close(fid)
                os.unlink(fname)
            except IOError:
                pass
