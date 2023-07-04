from datetime import datetime

import pytz

import filedrop.lib.time as f_time
import filedrop.tests.utils as f_tests


class TimeTests(f_tests.FiledropTest):
    def test_time(self):
        dt = datetime(2013, 8, 23, 15, 57, 31)

        s = f_time.repr(dt)
        self.assertEqual(s, "Aug 23, 2013 at 15:57:31 UTC")
        s = f_time.repr(dt, as_utc=False)
        self.assertEqual(s, "Aug 23, 2013 at 15:57:31 UTC")

        s = f_time.iso8601(dt)
        self.assertEqual(s, "2013-08-23T15:57:31Z")

        dt = f_time.now()
        self.assertEqual(dt.tzinfo, pytz.UTC)
