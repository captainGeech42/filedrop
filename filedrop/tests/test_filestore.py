import hashlib
import os

import filedrop.lib.exc as f_exc
import filedrop.lib.models as f_models
import filedrop.tests.utils as f_utils


class FilestoreTests(f_utils.FiledropTest):
    def test_adding(self):
        bytz = b"hello there. general kenobi!"
        fhash = hashlib.sha256(bytz).hexdigest()
        name = "script.txt"

        with self.getTestDatabase() as db:
            u1 = f_models.User.new("user1", "hunter2")
            db.add_user(u1)

            with self.getTestFilestore(db=db) as fs:
                self.assertIsNotNone(fs.save_file(name, bytz, anon_upload=True))
                self.assertIsNotNone(fs.save_file(name, bytz, username="user1"))

                # make sure the arg validation works
                self.assertRaises(f_exc.BadArgs, fs.save_file, name, bytz)
                self.assertRaises(f_exc.BadArgs, fs.save_file, name, bytz, anon_upload=True, username="hi")

                # ensure that we can't upload for a non-existent user
                self.assertRaises(f_exc.InvalidUser, fs.save_file, name, bytz, username="user2")

                # make sure the file actually hit disk
                with db.cursor() as c:
                    x = c.execute("SELECT path, hash FROM files;")
                    for p, h in x.fetchall():
                        self.assertEqual(fhash, h)
                        self.assertTrue(p.endswith(f"/{fhash[0:2]}/{fhash[2:4]}/{fhash[4:6]}/{fhash[6:]}"))

                        with open(p, "rb") as f:
                            file_contents = f.read()
                            self.assertEqual(len(file_contents), len(bytz))
                            self.assertEqual(hashlib.sha256(file_contents).hexdigest(), fhash)

    def test_bad_add(self):
        bytz = b"hello there. general kenobi!"
        name = "script.txt"

        with self.getTestDatabase() as db:
            u1 = f_models.User.new("user1", "hunter2")
            db.add_user(u1)

            # make sure max files error and don't hit disk
            max_size = 8
            with self.getTestFilestore(db=db, max_size=max_size) as fs:
                self.assertGreater(len(bytz), max_size)  # sanity check to make sure this test works as intended

                self.assertRaises(f_exc.FileTooLarge, fs.save_file, name, bytz, anon_upload=True)
                self.assertEqual(len(os.listdir(fs.root_path)), 0)

                with db.cursor() as c:
                    x = c.execute("SELECT COUNT(*) from FILES;")
                    self.assertEqual(x.fetchone()[0], 0)
