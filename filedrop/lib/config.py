import argparse
import os
import re
import sys
import typing
from dataclasses import dataclass

import filedrop.lib.exc as f_exc

ConfigValueType = typing.Union[int, str, bool]
VALID_CONFVAL_TYPES: typing.Iterable[type] = ConfigValueType.__args__  # type: ignore


VALID_CONFKEY_PAT = re.compile(r"^([a-z0-9]+(\.?))*[a-z0-9]+$")


@dataclass
class ConfigOption:
    """A single config value definition"""

    key: str
    desc: str
    valtype: type[ConfigValueType]
    required: bool = False
    default: ConfigValueType | None = None

    def validate(self):
        """Ensure the config option is valid."""

        if not self.key:
            raise f_exc.BadArgs("config option is not set")

        if not self.desc:
            raise f_exc.BadArgs(f"config desc is not set: {self.key}")

        disallowed_keys = ["help"]
        if self.key in disallowed_keys:
            raise f_exc.BadArgs(f"invalid config option name: {self.key}")

        if not VALID_CONFKEY_PAT.match(self.key):
            raise f_exc.BadArgs(f"invalid config option name: {self.key}")

        if self.valtype not in VALID_CONFVAL_TYPES:
            raise f_exc.BadArgs(f"invalid config option type ({self.valtype}): {self.key}")

        if self.default is not None:
            if not isinstance(self.default, self.valtype):
                raise f_exc.BadArgs(
                    f"invalid config option, default value doesn't match the option type ({self.valtype}): {self.key}"
                )

            if self.required:
                raise f_exc.BadArgs(
                    f"invalid config option, a default value was specified for a required option: {self.key}"
                )

    def parse(self, v: str) -> ConfigValueType:
        """Parse a value as the type of the option, otherwise raise a BadArgs exception."""

        try:
            return self.valtype(v)
        except ValueError as exc:
            raise f_exc.BadArgs(
                f"failed to parse cli arg value for {self.key} as {self.valtype().__class__.__name__}: '{v}'"
            ) from exc

    @property
    def envvar_suffix(self) -> str:
        """Get the environment variable key suffix for this config option."""

        return self.key.replace(".", "_").upper()

    @property
    def flag(self) -> str:
        """Get a CLI arg flag for this config option."""

        return "--" + self.key.replace(".", "-")

    @property
    def namespace_key(self) -> str:
        """Get a key for the argparse namespace entries for this config option."""

        return self.key.replace(".", "_")

    def __repr__(self) -> str:
        return f"<ConfigOption {self.key} ({self.valtype().__class__.__name__}) - {self.desc}{' (required)' if self.required else ''}>"

    def __str__(self) -> str:
        return repr(self)


class ConfigLoader:
    """
    Load config options from argv or environment variables.

    Command line options take precedence over environment variable options.
    """

    def __init__(self, prog: str, options: list[ConfigOption], env_prefix: str = "FD"):
        self._prog = prog
        self._options = options
        self._env_prefix = env_prefix

        self._loaded_vals = False
        self._vals: dict[str, ConfigValueType] = {}

        self._validate_opts()
        self._argparser = self._gen_argparser()

    def _validate_opts(self):
        """Ensure all of the config options are valid. Raises BadArgs on an invalid option."""

        for co in self._options:
            co.validate()

    def _gen_argparser(self) -> argparse.ArgumentParser:
        """Generate an argparser based on the specified config values"""

        p = argparse.ArgumentParser(prog=self._prog)

        for opt in self._options:
            desc = (
                opt.desc
                + f" ({'required; ' if opt.required else ''}{'default: ' + str(opt.default) + '; ' if opt.default is not None else ''}or ${self._env_prefix}_{opt.envvar_suffix})"
            )

            if opt.valtype == bool:
                p.add_argument(opt.flag, action="store_true", help=desc)
            else:
                p.add_argument(opt.flag, help=desc)

        return p

    def load_config(self, argv: list[str] | None = None) -> bool:
        """
        Load the config via argv and the process env vars.

        If argv is none, sys.argv[1:] is used.

        If argv[0] is "-h" or "--help", the argparser help is printed.

        Returns True if program execution can continue, otherwise False.
        """

        if argv is None:
            argv = sys.argv[1:]

        # check if help is needed
        if len(argv) > 0 and argv[0] in ["-h", "--help"]:
            self._argparser.print_help()
            return False

        # handle argv first
        if len(argv) > 0:
            cli_args = self._argparser.parse_args(argv)
            print(argv)
            print(cli_args)
            for opt in self._options:
                v = getattr(cli_args, opt.namespace_key)
                if v is not None:
                    if opt.valtype is bool:
                        # if the bool flag is set and the default is true, that means the flag being set negates it
                        # otherwise, if the default is False or None, it is True
                        self._vals[opt.key] = not opt.default
                    else:
                        self._vals[opt.key] = opt.parse(v)

        # populate things from env
        for opt in self._options:
            if opt.key not in self._vals:
                k = f"{self._env_prefix}_{opt.envvar_suffix}"
                if opt.valtype == bool:
                    defined = k in os.environ
                    if defined:
                        if opt.default is True:
                            self._vals[opt.key] = False
                        else:
                            self._vals[opt.key] = True
                else:
                    v = os.getenv(k)
                    if v is not None:
                        self._vals[opt.key] = opt.parse(v)

        # check if all the required ones are set, and populate defaults
        for opt in self._options:
            if opt.required and opt.key not in self._vals:
                raise f_exc.BadArgs(f"a required config value was not specified: {opt.key}")

            if opt.default is not None and opt.key not in self._vals:
                self._vals[opt.key] = opt.default

        self._loaded_vals = True

        return True

    def get_value(self, opt: str) -> ConfigValueType | None:
        """Get the value for a config option, or None if it's not specified."""

        if not self._loaded_vals:
            raise f_exc.BadArgs("no config values available, haven't loaded them yet!")

        return self._vals.get(opt)
