import filedrop.tests.utils as f_tests


class ServerTests(f_tests.ServerTest):
    def test_healthcheck(self):
        r = self.client.get("/healthcheck")
        self.assertEqual(r.json, {"status": "good"})
