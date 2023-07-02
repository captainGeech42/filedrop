import os
import unittest

import filedrop.lib.database as f_db
import filedrop.lib.models as f_models

class DatabaseTest(unittest.TestCase):

    def test_migrations(self):
        num_migrations = len(list(filter(lambda x: x.endswith(".sql"), os.listdir(f_db.Database.migrations_folder))))

        with f_db.Database() as db:
            self.assertTrue(db.migrated)

            with db.cursor() as c:
                x = c.execute("select count(*) from migrations;")
                self.assertEqual(x.fetchone()[0], num_migrations)

                # migration 000
                x = c.execute("select count(*) from users where username = 'anonymous' and is_anon = True;")
                self.assertEqual(x.fetchone()[0], 1)

    def test_users(self):
        with f_db.Database() as db:

            u = db.get_user("anonymous")
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