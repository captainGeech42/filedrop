from datetime import datetime, timedelta

import filedrop.lib.time as f_time
import filedrop.lib.utils as f_utils
import filedrop.tests.utils as f_tests


class ServerTests(f_tests.ServerTest):
    def test_healthcheck(self):
        r = self.client.get("/healthcheck")
        self.assertEqual(r.json, {"status": "good"})

    def test_file_info(self):
        n = "test.txt"
        d = b"this is a good test file"
        exp = f_time.now() + timedelta(days=3)
        f = self.fs.save_file(n, d, anon_upload=True, expiration_time=exp, max_downloads=5)

        # TODO make the request. prob need to serialize the timestamps in the blueprint route

    def test_file_download(self):
        n = "test.txt"
        d = b"this is a good test file"
        f = self.fs.save_file(n, d, anon_upload=True)
        self.assertIsNotNone(f)

        r = self.client.get(f"/api/v1/file/{f_utils.hexstr(f.uuid)}/download")  # type: ignore
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers.get("Content-Disposition"), f"attachment; filename={n}")
        self.assertEqual(r.data, d)

        r = self.client.get("/api/v1/file/asdf/download")
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json, {"status": "error", "msg": "file doesn't exist", "data": {"uuid": "asdf"}})

        r = self.client.get("/api/v1/file/aabbccdd/download")
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json, {"status": "error", "msg": "file doesn't exist", "data": {"uuid": "aabbccdd"}})
