import os
import tempfile
from datetime import timedelta

import filedrop.lib.database as f_db
import filedrop.lib.models as f_models
import filedrop.lib.time as f_time
import filedrop.tests.utils as f_tests


class DatabaseTests(f_tests.FiledropTest):
    def test_migrations(self):
        num_migrations = len(
            list(filter(lambda x: x.endswith(".sql"), os.listdir(f_db.Database.get_migrations_folder())))
        )

        # ensure the migrations can be executed multiple times against the same db idempotently
        with tempfile.TemporaryDirectory() as tmpdir:
            fn = os.path.join(tmpdir, "filedrop.db")

            with self.getTestDatabase(path=fn) as db:
                self.assertTrue(db.migrated)

            with self.getTestDatabase(path=fn) as db:
                self.assertTrue(db.migrated)

                with db.cursor() as c:
                    x = c.execute("select count(*) from migrations;")
                    self.assertEqual(x.fetchone()[0], num_migrations)

                    # migration 000
                    x = c.execute("select count(*) from users where username = 'anonymous' and is_anon = True;")
                    self.assertEqual(x.fetchone()[0], 1)

    def test_users(self):
        with self.getTestDatabase() as db:
            u = db.get_user("anonymous")
            self.assertIsNotNone(u)
            u = db.get_anon_user()
            self.assertIsNotNone(u)

            u = db.get_user("asdfasdf")
            self.assertIsNone(u)

            u2 = f_models.User.new("hello", "world")
            self.assertIsNotNone(u2)
            self.assertTrue(db.add_user(u2))
            self.assertFalse(db.add_user(u2))

            u2p = db.get_user("hello")
            self.assertEqual(u2, u2p)

            u2p.update_password("asdf")
            db.update_user_pw(u2p)

            u3 = db.get_user("hello")
            self.assertNotEqual(u2, u3)

            self.assertIsNotNone(db.get_user_id("anonymous"))
            self.assertIsNone(db.get_user_id("zzxxxcvc"))

    def test_files(self):
        with self.getTestDatabase() as db:
            u = f_models.User.new("user1", "pass2")
            db.add_user(u)

            now = f_time.now()

            f = f_models.File.new("hi", "/asdf", 8, "aaaaaaaaaaaaaaaaa", "user1", expiration_time=now, max_downloads=5)
            ts = db.add_new_file(f)
            self.assertTrue(ts >= now - timedelta(seconds=3))
            self.assertTrue(ts <= now + timedelta(seconds=3))
            f2 = db.get_file(f.uuid)
            self.assertEqual(f, f2)

            self.assertIsNone(f.uploaded_at)
            self.assertIsNotNone(f2.uploaded_at)

            f3 = f_models.File.new("hi", "/asdf", 8, "aaaaaaaaaaaaaaaaa", "user1", max_downloads=1)
            db.add_new_file(f3)
            f4 = f_models.File.new("hi", "/asdf", 8, "aaaaaaaaaaaaaaaaa", "user1")
            db.add_new_file(f4)
            self.assertTrue(db.inc_download_count(f3.uuid))
            self.assertFalse(db.inc_download_count(f3.uuid))
            self.assertTrue(db.inc_download_count(f4.uuid))
            self.assertTrue(db.inc_download_count(f4.uuid))
            self.assertTrue(db.inc_download_count(f4.uuid))
