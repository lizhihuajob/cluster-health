import subprocess

IP = str
#import shlex
from typing import Protocol

import attr


def run_local_command( command: list) -> str:
    #print("command:",command)
    # This call to subprocess.Popen is not robust and is meant to be a placeholder for whatever method
    # you use for running arbitrary commands locally.
    result = subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
    msg_stdout = result.stdout
    msg_stderr = result.stderr
    #print("returncode:",result.returncode)
    if result.returncode != 0:
        print(msg_stderr)
    else:
        print(msg_stdout)
    return  result.returncode,msg_stdout,msg_stderr


@attr.s(auto_attribs=True, frozen=True)
class ProcessResult:
    returncode: int
    output: str


class CommandRunner(Protocol):
    def run_command(self, command: str, **kwargs: object) -> ProcessResult:
        #print("CommandRunner base")
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
        #print("ContainerSSHConnectionData :",command)
        #escaped_command = shlex.quote(command)
        #self.port = 16802
        command_line = ["ssh", "-p", f"{self.port}", f"{self.user}@{self.ip}", f"{command}"]
        return run_local_command(command_line)


@attr.s(auto_attribs=True, frozen=True)
class RemoteCommandRunner(CommandRunner):
    connection: ContainerSSHConnectionData

    def run_command(self, command: str, **kwargs: object) -> ProcessResult:
        #print("RemoteCommandRunner ...")
        # This is a placeholder for whatever method you use to run commands over ssh
        rescode,msg_stdout,msg_stderr = self.connection.run_command(command)
        if rescode != 0:
            return ProcessResult(returncode=rescode, output=str(msg_stderr))
        else:
            return ProcessResult(returncode=rescode, output=str(msg_stdout))
        

    @property
    def ip(self) -> IP:
        return self.connection.ip

    def __str__(self) -> str:
        return f"{self.connection.ip}:{self.connection.port}"


@attr.s(auto_attribs=True, frozen=True)
class FullConnection:
    ssh_connection: CommandRunner
    internal_ip: str
    internal_index: int