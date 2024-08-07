import subprocess

IP = str
import shlex
from typing import Protocol

import attr


def run_local_command(
    command: str,
) -> str:
    print("command:",command)
    # This call to subprocess.Popen is not robust and is meant to be a placeholder for whatever method
    # you use for running arbitrary commands locally.
    process = subprocess.Popen(
        command.split(" "),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    msg_stdout, msg_stderr = process.communicate()
    print("stdout:",msg_stdout)
    print("stderr:",msg_stderr)
    return msg_stdout


@attr.s(auto_attribs=True, frozen=True)
class ProcessResult:
    returncode: int
    output: str


class CommandRunner(Protocol):
    def run_command(self, command: str, **kwargs: object) -> ProcessResult:
        print("CommandRunner base")
        ...

    @property
    def ip(self) -> IP:
        ...


@attr.s(auto_attribs=True, frozen=True)
class ContainerSSHConnectionData:
    ip: str
    port: int
    user: str

    def run_command(self, command: str) -> str:
        print("ContainerSSHConnectionData :",command)
        escaped_command = shlex.quote(command)
        return run_local_command(f"ssh {self.user}@{self.ip} -p {self.port} {escaped_command}")


@attr.s(auto_attribs=True, frozen=True)
class RemoteCommandRunner(CommandRunner):
    connection: ContainerSSHConnectionData

    def run_command(self, command: str, **kwargs: object) -> ProcessResult:
        print("RemoteCommandRunner ...")
        # This is a placeholder for whatever method you use to run commands over ssh
        msg_stdout = self.connection.run_command(command)
        return ProcessResult(returncode=0, output=str(msg_stdout))

    @property
    def ip(self) -> IP:
        return self.connection.ip

    def __str__(self) -> str:
        return f"{self.connection.ip}:{self.connection.port}"


@attr.s(auto_attribs=True, frozen=True)
class FullConnection:
    ssh_connection: CommandRunner
    internal_ip: str
