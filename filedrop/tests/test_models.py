import filedrop.lib.models as f_models
import filedrop.tests.utils as f_tests


class UserTest(f_tests.FiledropTest):
    def test_user(self):
        u1 = f_models.User.new("user1", "hunter2")
        self.assertIsNotNone(u1)
        self.assertTrue(u1.enabled)
        self.assertFalse(u1.is_anon)

        u1p = f_models.User.new("user1", "hunter2")
        self.assertIsNotNone(u1p)

        self.assertNotEqual(u1, u1p)

        u2 = f_models.User.new("user2", "asdf")
        self.assertIsNotNone(u2)

        u3 = f_models.User.new("user3", "asdf")
        self.assertIsNotNone(u3)

        self.assertNotEqual(u2.salt, u3.salt)
        self.assertNotEqual(u2.password_hash, u3.password_hash)

        self.assertTrue(u2.check_password("asdf"))

        u2.update_password("zxcv")
        self.assertFalse(u2.check_password("asdf"))
        self.assertTrue(u2.check_password("zxcv"))

    def test_file(self):
        pass
