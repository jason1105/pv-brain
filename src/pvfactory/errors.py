"""Error taxonomy. Exit codes per docs/specs/04-cli-and-outputs.md."""


class PvError(Exception):
    """Base error. exit_code drives the CLI."""

    exit_code = 1


class ConfigError(PvError):
    """Configuration or environment problem (bad profile, missing provider)."""

    exit_code = 2


class ValidationError(PvError):
    """An artifact failed its contract at a step boundary."""

    exit_code = 1


class StepError(PvError):
    """A step failed during execution."""

    exit_code = 1

    def __init__(self, step: str, message: str):
        super().__init__(f"step '{step}': {message}")
        self.step = step
