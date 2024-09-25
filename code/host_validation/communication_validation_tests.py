"""
Usage:
```
python communication_validation_tests.py --test
```

where test is one of {group_ib, p2p_ib, nvlink, wait, all_single_node}
"""

import argparse
import json
import os
import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Dict
from typing import Final
from typing import Generator
from typing import Iterable
from typing import List
from typing import Mapping
from typing import NewType
from typing import Optional
from typing import Sequence
from typing import Tuple
from typing import TypeVar
from typing import Union

import numpy as np
from gpu_connection_test import IbResultsSchema
from loguru import logger
from p2p_ib_test import run_p2p_ib_tests
from p2p_ib_test import shutdown_test
from utils.events import get_expiration_event
from utils.run_command import CommandRunner
from utils.run_command import ContainerSSHConnectionData
from utils.run_command import RemoteCommandRunner
from utils.run_command import run_local_command
from utils.serialization import deserialize_from_json

_PORT_LOCK = threading.Lock()
_PORTS_PER_HOST: Final[Dict[str, int]] = {}

IP = str


def get_port_to_use(master_addr: str) -> int:
    with _PORT_LOCK:
        port_to_use = _PORTS_PER_HOST.get(master_addr, 9000)
        _PORTS_PER_HOST[master_addr] = port_to_use + 1
    return port_to_use


T = TypeVar("T")


def format_env(env: Dict[str, str]) -> str:
    return " ".join(f"{key}={value}" for key, value in env.items())


EXPIRATION_SECONDS: Final[float] = 100.0

ENV_VARS = {
    "NCCL_NET": "IB",
    "NCCL_DEBUG_SUBSYS": "ALL",
    "TORCH_NCCL_ASYNC_ERROR_HANDLING": "1",
    # "NCCL_NET_GDR_LEVEL": "LOC", # LOC = DISABLE GDR (if it's enabled on the kernel)
}

CONFIG_FILE = Path(os.path.realpath(__file__)).parent / "config.json"
with open(CONFIG_FILE, 'r') as f:
    CONFIG_FILE = json.load(f)

ENV_VARS["NCCL_IB_HCA"] = "=" + ",".join(CONFIG_FILE["infiniband_status"]["device_names"])

ErrorString = NewType("ErrorString", str)
TestResultType = Union[Tuple[float, ...], ErrorString]


def generate_chunks(iterable: Iterable[T], chunk_size: int) -> Generator[Tuple[T, ...], None, None]:
    """Yield successive n-sized chunks from any iterable"""
    chunk = []
    for item in iterable:
        chunk.append(item)
        if len(chunk) == chunk_size:
            yield tuple(chunk)
            chunk = []
    if len(chunk) > 0:
        yield tuple(chunk)


def parse_nvlink_test_for_stats(
    ip_to_times: Mapping[IP, List[float]]
) -> Dict[str, Dict[str, Union[str, float, List[float]]]]:
    ip_to_times_summary = {}
    for ip, times in ip_to_times.items():
        if not (all([isinstance(time, float) for time in times])):
            # Add the mean with an error message as well, then we can always read one value in the health check
            ip_to_times_summary[ip] = {
                "error": "times are not all floats",
                "mean": "Error: times are not all floats",
                "times": times,
            }
        else:
            ip_to_times_summary[ip] = {
                "count": len(times),
                "min": min(times),
                "max": max(times),
                "mean": sum(times) / len(times),
                "25_percentile": np.percentile(times, 25),
                "50_percentile": np.percentile(times, 50),
                "75_percentile": np.percentile(times, 75),
            }
    print(ip_to_times_summary)
    return ip_to_times_summary


def run_ib_test(
    connection: CommandRunner,
    master_addr: str,
    master_port: int,
    rail: int,
    rank: int,
    world_size: int,
    extra_flags: Optional[Dict[str, str]] = None,
) -> TestResultType:
    try:
        with get_expiration_event(EXPIRATION_SECONDS) as event:
            extra_flags_str = " ".join([f"--{k} {v}" for k, v in extra_flags.items()]) if extra_flags else ""
            app_path = os.path.abspath(os.path.dirname(__file__))
            command = (
                f"{format_env(ENV_VARS)} python3 {app_path}/gpu_connection_test.py ib --rail {rail} --master_addr {master_addr}"
                + f" --master_port {master_port} --rank {rank} --world_size {world_size} {extra_flags_str}"
            )
            #print("commands:",command)
            print(f"running {command} on {connection}")
            result = connection.run_command(command=command,  shutdown_event=event, )
            #print("************************************************************")
            #print(result)
            #print("************************************************************")
            
            #ib_results_str = result.output.strip().split("\n")[-1]
            #ib_results: IbResultsSchema = deserialize_from_json(ib_results_str)
            #if ib_results.rail != rail:
            #    print(
            #        f"WARNING: Expected output for rail {rail} but actually got output for rail {ib_results.rail}"
            #    )
            #logger.debug(f"success running {command} on {connection}; result {ib_results.results}")
            return result
    except Exception as e:
        print(f"caught exception running {command} on {connection}:\n{e}")
        #shutdown_test(connection, "tests.ib_tes[t]")
        return ErrorString(f"Caught exception running tests: {e}")


def run_single_group(group: Sequence[CommandRunner], rail: int) -> Dict[Tuple[CommandRunner, int], TestResultType]:
    master_addr = group[0].ip
    master_port = get_port_to_use(master_addr)
    print(f"running {len(group)} node group {[x.ip for x in group]} on rail {rail}")
    with ThreadPoolExecutor(max_workers=len(group)) as executor:
        results = executor.map(
            lambda rank_and_connection: run_ib_test(
                rank_and_connection[1], master_addr, master_port, rail, rank_and_connection[0], len(group)
            ),
            enumerate(group),
        )
    result = {(connection, rail): scores for connection, scores in zip(group, results)}
    # result is kinda messy to print here
    print(f"finished running {len(group)} node group {[x.ip for x in group]} on rail {rail}")
    return result


def run_single_group_across_all_rails(
    group: Sequence[CommandRunner],
) -> Dict[Tuple[CommandRunner, int], TestResultType]:
    master_addr = group[0].ip
    master_port = get_port_to_use(master_addr)
    connection_and_rail = [(connection, rail) for connection in group for rail in range(8)]
    print(
        f"running {len(group)} node group {[x.ip for x in group]} across all rails with {len(connection_and_rail)} total workers"
    )
    with ThreadPoolExecutor(max_workers=len(connection_and_rail)) as executor:
        results = executor.map(
            lambda rank_connection_rail: run_ib_test(
                rank_connection_rail[1][0],
                master_addr,
                master_port,
                rank_connection_rail[1][1],
                rank_connection_rail[0],
                len(connection_and_rail),
            ),
            enumerate(connection_and_rail),
        )
    result = {connection_rail: scores for connection_rail, scores in zip(connection_and_rail, results)}
    # result is kinda messy to print here
    print(f"finished running {len(group)} node group {[x.ip for x in group]} on all rails")
    return result


def run_experiments(
    groups: Sequence[Sequence[CommandRunner]],
    rail_aligned: bool = True,
) -> Dict[Tuple[CommandRunner, str], TestResultType]:
    # each thread runs a single (group, rail) pair, so it will open group_size SSH connections
    concurrent_groups = len(groups) * 8
    with ThreadPoolExecutor(max_workers=concurrent_groups) as executor:
        if not rail_aligned:
            #print("run_experiments************************************02**************")
            results = executor.map(run_single_group_across_all_rails, groups)
            scores_by_connection_rail = {}
            #for result in results:
            #    for (connection, rail), scores in result.items():
            #        scores_by_connection_rail[(connection, str(rail))] = scores
            return scores_by_connection_rail
        else:
            #print("run_experiments************************************03**************")
            results = executor.map(
                lambda group_and_rail: run_single_group(*group_and_rail),
                [(group, rail) for group in groups for rail in range(8)],
            )
            scores_by_connection_rail = {(connection, "total"): 0.0 for group in groups for connection in group}
            #for result in results:
            #    for (connection, rail), scores in result.items():
            #        if all(isinstance(s, float) for s in scores):
            #            scores_by_connection_rail[(connection, "total")] += sum(
            #                [s for s in scores if isinstance(s, float)]
            #            )
            #        else:
            #            scores_by_connection_rail[(connection, "total")] = ErrorString(f"Error on gpu {rail}")
            #        scores_by_connection_rail[(connection, str(rail))] = scores
            return scores_by_connection_rail


def run_group_ib_tests(
    connections: Sequence[CommandRunner],
    output_file: Optional[Path] = None,
    rail_aligned: bool = True,
    group_sizes: Tuple[int] = (1000,),
    max_iterations: int = 1,
) -> Dict[Tuple[int, int], Dict[Tuple[CommandRunner, str], TestResultType]]:
    if output_file:
        with output_file.open("a+") as f:
            f.write(f"Starting group IB tests with connections {[connection.ip for connection in connections]}\n")
    iteration_to_scores = dict()
    for count in range(max_iterations):
        random.seed(count)
        for group_size in group_sizes:
            group_size = min(group_size, len(connections))
            scores_by_connection = dict()
            print(f"Running tests for group size {group_size}")
            mixed_nodes = list(connections)
            #random.shuffle(mixed_nodes)
            
            for connect in mixed_nodes:
                shutdown_test(connect,"gpu_connection_test.[p]y")
            time.sleep(1)

            groups = tuple(generate_chunks(mixed_nodes, group_size))
            for connection_and_rail, scores in run_experiments(groups, rail_aligned).items():
                scores_by_connection[connection_and_rail] = scores

            print(f"Finished tests for group size {group_size}")

            log_lines = [
                f"{connection.ip}-{rail}: {scores}"
                for (connection, rail), scores in sorted(scores_by_connection.items())
            ]
            #print(scores_by_connection)
            #print(f"Results for group size {group_size}: \n" + "\n".join(log_lines))
            #if output_file:
            #    with output_file.open("a+") as f:
            #        f.write(f"Results for group size {group_size}: \n" + "\n".join(log_lines) + "\n")

            iteration_to_scores[(count, group_size)] = scores_by_connection
    
    #print(iteration_to_scores)
    for connect in connections:
        shutdown_test(connect,"gpu_connection_test.[p]y")

    return "successful"


def run_nvlink_test_single_host(
    connection: CommandRunner,
    dims: int,
    loops: int,
) -> Tuple[Union[CommandRunner, str], str]:
    print(f"nvlink_test running on {connection.ip} node")
    try:
        with get_expiration_event(EXPIRATION_SECONDS) as event:
            # 获取文件所在路径
            app_path = os.path.abspath(os.path.dirname(__file__))
            command = (
                f"{format_env(ENV_VARS)} torchrun --nproc_per_node 8 {app_path}/gpu_connection_test.py nvlink --dims {dims} --loops {loops}"
            )
            #print("commands:",command)
            nvlink_results_str = connection.run_command(command=command,shutdown_event=event,)
            # nvlink_results_str = result.output.strip().split("\n")[-1]
            #print("nvlink_results_str:",nvlink_results_str.output)
            # nvlink_results = deserialize_from_json(nvlink_results_str)
            return connection, nvlink_results_str.output
    except Exception as e:
        print(f"caught exception running torchrun on {connection}:\n{e}")
        # shutdown_test(connection, "tests.nvlink_tes[t]")
        return connection, ErrorString(f"Caught exception running tests: {e}")


def run_nvlink_tests(
    connections: Sequence[CommandRunner],
    output_file: str = None,
    dims: int = 1_000_000_000,
    loops: int = 20,
) -> Dict[str, Dict[str, Union[float, List[float]]]]:
    if output_file:
        with open(output_file,"a+") as f:
            f.write(f"Starting nvlink tests with connections {[connection.ip for connection in connections]}\n")
    group_size = 1
    scores_by_connection = {}
    

    nodes = [group[0] for group in generate_chunks(connections, group_size)]
    #print("nodes:",nodes)
    with ThreadPoolExecutor(max_workers=len(nodes)) as executor:
        results = executor.map(lambda node: run_nvlink_test_single_host(node, dims, loops), nodes)
    for connection, scores in results:
        scores_by_connection[connection.ip] = scores

    log_lines = [
        f"{connection}: {json.dumps(scores)}"
        for connection, scores in sorted(scores_by_connection.items(), key=lambda item: item[1])
    ]

    #print(log_lines)
    #print(f"Results: \n" + "\n".join(log_lines))
    if output_file:
        with open(output_file,"a+") as f:
            f.write(f"Results: \n" + "\n".join(log_lines) + "\n")

    #parse_nvlink_test_for_stats(scores_by_connection)

    return "successful"


def run_tests_single_node(command_runner: RemoteCommandRunner) -> None:
    #time = datetime.now()
    print(f"Starting single node tests for {command_runner.ip}")
    print(f"Starting running nvlink tests for {command_runner.ip}")
    # = time.strftime("%Y-%m-%d %H:%M:%S")
    #filename_time = time.strftime("%Y%m%d%H%M%S")
    #output_path = os.path.abspath(os.path.dirname(__file__))
    #tests_dir = os.path.join(output_path,f"health_tests/{command_runner.ip}/")
    #if os.path.exists(tests_dir) == False:
    #    res = run_local_command(["mkdir" "-p" f"{tests_dir}"])
    #    print("create path ",tests_dir,res)
    #run_local_command(["sudo" "mkdir" "-p" f"{tests_dir}"])
    #run_local_command(["sudo" "chown" "root" f"{tests_dir}"])
    #run_local_command(["sudo" "chgrp" "root" f"{tests_dir}"])

    nvlink_results_full = run_nvlink_tests(
        [command_runner], output_file=None, dims=16_000_000, loops=10
    )
    #nvlink_results = nvlink_results_full
    #print(nvlink_results_full)
    print(f"Finished running nvlink tests for {command_runner.ip}")
    print(f"Starting running p2p tests for {command_runner.ip}")

    #results_dict = {
    #    "time": readable_time,
    #    "ip": command_runner.ip,
    #    "nvlink": nvlink_results_full,
    #}
   #with open(os.path.join(tests_dir, "summary.json"), "w+") as f:
    #    json.dump(results_dict, f)

    p2p_results = run_p2p_ib_tests(
        [command_runner], single_host=True, output_file=None, num_iterations=5
    )
    
    print(f"Finished running p2p tests for {command_runner.ip}")

    #results_dict["p2p_ib"] = p2p_results
    #with open(os.path.join(tests_dir, "summary.json"), "w+") as f:
    #    json.dump(results_dict, f)

    print(f"Finished running tests for {command_runner.ip}")

def run_all_single_node_tests(connections: List[CommandRunner]) -> None:
    with ThreadPoolExecutor(max_workers=len(connections)) as executor:
        executor.map(run_tests_single_node, connections)
    print(f"Finished running all single node tests")


POSSIBLE_TESTS = ["group_ib", "all_rail_group_ib", "p2p_ib", "nvlink", "all_single_node"]


def get_worker_connections() -> List[RemoteCommandRunner]:
    host_info = CONFIG_FILE["node_info"]
    nodes, port, user = host_info["nodes"], int(host_info["port"]), host_info["user"]
    return [RemoteCommandRunner(connection=ContainerSSHConnectionData(ip=node, port=port, user=user)) for node in nodes]


def run(test: str,output_file: Optional[Path] = None) -> None:
    assert test in POSSIBLE_TESTS, f"test {test} not in {POSSIBLE_TESTS}"
    connections = get_worker_connections()
    match test:
        case "group_ib":
            run_group_ib_tests(connections, rail_aligned=True)

        case "all_rail_group_ib":
            run_group_ib_tests(connections, rail_aligned=False)
        
        case "nvlink":
            run_nvlink_tests(connections,output_file)

        case "p2p_ib":
            run_p2p_ib_tests(connections)

        case "all_single_node":
            print(f"Starting single node tests on {','.join([str(c.ip) for c in connections])}")
            run_all_single_node_tests(connections)

def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument("--test")
    parser.add_argument("--output")

    args = parser.parse_args()

    run(test=args.test)


if __name__ == "__main__":
    main()


