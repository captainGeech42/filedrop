import contextlib
import io

import filedrop.lib.config as f_config
import filedrop.lib.exc as f_exc
import filedrop.tests.utils as f_tests


class ConfigTests(f_tests.FiledropTest):
    def test_configoption(self):
        self.assertEqual(f_config.ConfigOption("hi", "good desc", str).envvar_suffix, "HI")
        self.assertEqual(f_config.ConfigOption("hi.yes.asdf", "good desc", str).envvar_suffix, "HI_YES_ASDF")

        bad = [
            f_config.ConfigOption("***:yeet", "hello there", int),
            f_config.ConfigOption("asdf", "zxcv", list),  # type: ignore
            f_config.ConfigOption("vvv", "jjj", str, default=123),
            f_config.ConfigOption("vvv", "jjj", int, default=123, required=True),
        ]

        for opt in bad:
            with self.assertRaises(f_exc.BadArgs, msg=opt):
                opt.validate()

    def test_configloader(self):
        # make sure arg validation happens on config definition
        self.assertRaises(
            f_exc.BadArgs, f_config.ConfigLoader, "test", [f_config.ConfigOption("badval*123", "hi", str)]
        )

        @contextlib.contextmanager
        def test_cfg(check_vals=True):
            c = f_config.ConfigLoader(
                "test",
                [
                    f_config.ConfigOption("key1", "hi", str, required=True),
                    f_config.ConfigOption("jjj", "kkk", str, default="yesitshere"),
                    f_config.ConfigOption("a.s.d.f", "lol", int, required=True),
                    f_config.ConfigOption("key2", "something true", bool),
                    f_config.ConfigOption("key3", "something false", bool, default=True),
                ],
            )
            yield c

            if check_vals:
                self.assertEqual(c.get_value("key1"), "hello")
                self.assertEqual(c.get_value("jjj"), "yesitshere")
                self.assertEqual(c.get_value("a.s.d.f"), 5)
                self.assertEqual(c.get_value("key2"), True)
                self.assertEqual(c.get_value("key3"), False)

        # print help
        for v in ["-h", "--help"]:
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                with test_cfg(check_vals=False) as c:
                    self.assertFalse(c.load_config([v]))
                    self.assertIn("usage: ", output.getvalue())
                    self.assertIn("options:", output.getvalue())

        # try all in argv
        with test_cfg() as c:
            self.assertTrue(c.load_config(["--key1", "hello", "--a-s-d-f", "5", "--key2", "--key3"]))

        # try all in env var
        with self.customEnvVars({"FD_KEY1": "hello", "FD_A_S_D_F": "5", "FD_KEY2": "", "FD_KEY3": "hi"}):
            with test_cfg() as c:
                self.assertTrue(c.load_config([]))

        # try a mix
        with self.customEnvVars({"FD_A_S_D_F": "5", "FD_KEY2": ""}):
            with test_cfg() as c:
                self.assertTrue(c.load_config(["--key1", "hello", "--key3"]))
