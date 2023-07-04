import filedrop.lib.utils as f_utils
import filedrop.tests.utils as f_tests


class UtilsTests(f_tests.FiledropTest):
    def test_uuid(self):
        self.assertEqual(len(f_utils.gen_uuid()), 16)

    def test_hexstr(self):
        a = b"\x80\x90\x30\x58\xab"

        b = f_utils.hexstr(a)
        self.assertEqual(b, "80903058ab")

        self.assertEqual(f_utils.unhexstr(b), a)
