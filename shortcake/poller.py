#!/usr/bin/env python3.10
"""Pollers that periodically get the output of a Shell command or function."""
import dataclasses as dc
import subprocess as sp
import time
import typing as t


@dc.dataclass
class Poller:
    """Poll the output of a Shell command or a function periodically."""

    command: t.Union[str, callable] = "echo 'hello world'"
    timespan: float = 1 / 30
    formatter: callable = lambda x: x

    last_timestamp: t.Optional[int] = None
    raw: t.Any = None
    process: t.Optional[sp.Popen] = None

    def get(self):
        """Get the value."""
        self.update()
        if self.raw is None:
            return None
        return self.formatter(self.raw)

    def update(self) -> None:
        """Run the command again in case enough time has passed."""
        should_update = (
            self.last_timestamp is None
            or time.time() - self.last_timestamp > self.timespan
        )

        if should_update:
            # Call functions normally.
            if callable(self.command):
                self.raw = self.command()
                return

            # Start a new process.
            self.last_timestamp = time.time()
            self.process = sp.Popen(
                self.command, shell=True, stdout=sp.PIPE, stderr=sp.DEVNULL
            )

            if self.process is not None and self.process.poll() is not None:
                self.raw = self.process.stdout.read().strip()
                self.process = None
