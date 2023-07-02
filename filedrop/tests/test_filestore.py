import filedrop.tests.utils as f_utils


class FilestoreTests(f_utils.FiledropTest):
    def test_adding(self):
        with self.getTestFilestore() as fs:
            bytz = b"hello there. general kenobi!"
            name = "script.txt"

            self.assertIsNotNone(fs.save_file(name, bytz, anon_upload=True))
