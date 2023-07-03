import filedrop.lib.utils as f_utils
import filedrop.tests.utils as f_tests


class UtilsTests(f_tests.FiledropTest):
    def test_uuid(self):
        self.assertEqual(len(f_utils.gen_uuid()), 16)
