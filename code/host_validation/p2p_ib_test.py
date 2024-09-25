#!/usr/bin/env python3
"""
This file is used to test the performance of the Infiniband network on the host.
It is run as a script on each host in the cluster.
"""
import json
import os
import random
import re
import time
import ipaddress
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict
from typing import Final
from typing import List
from typing import Optional
from typing import Sequence
from typing import Tuple
from typing import Union

import attr
from loguru import logger
from utils.events import get_expiration_event
from utils.run_command import CommandRunner
from utils.run_command import FullConnection

EXPIRATION_SECONDS: Final[float] = 100.0


BW_ERROR_VALUE: Final[float] = 0.0
LAT_ERROR_VALUE: Final[float] = 10000000

USE_GDR: Final[bool] = True
BW_LOWER_LIMIT_GDR: Final[float] = 720
BW_LOWER_LIMIT_NO_GDR: Final[float] = 300

LAT_UPPER_LIMIT: Final[float] = 4.2

BW_TEST_OUTPUT_KEY = "BWaverage[Gb/sec]"
LAT_TEST_OUTPUT_KEY = "99%percentile[usec]"

IP = str



@attr.s(auto_attribs=True, frozen=True)
class HcaDescription:
    pcie_device_description: str

    @property
    def pcie_slot_index(self) -> int:
        return int(self.pcie_device_description.split("_")[1])

    def __str__(self) -> str:
        return self.pcie_device_description


EXPECTED_VERSION_FILE = Path(os.path.realpath(__file__)).parent/ "config.json"
with open(EXPECTED_VERSION_FILE, 'r') as f:
    EXPECTED_VERSIONS = json.load(f)
    
#EXPECTED_NETDEV_FILE = Path(os.path.realpath(__file__)).parent/ "ibdev2netdev_info.json"
#with open(EXPECTED_NETDEV_FILE, 'r') as f:
#    MLX_CARDS_NETDEV = json.load(f)

MLX_CARDS: Final[Tuple[HcaDescription, ...]] = tuple(HcaDescription(device_name) for device_name in EXPECTED_VERSIONS["infiniband_status"]["device_names"])
MLX_CARDS_SUBNET=EXPECTED_VERSIONS["infiniband_status"]["device_subnet_prefix"]


def is_passing_host(card_to_result: Dict[str, Tuple[float, float]], gdr_enabled: bool = USE_GDR) -> bool:
    if gdr_enabled:
        bw_lower_limit = BW_LOWER_LIMIT_GDR
    else:
        bw_lower_limit = BW_LOWER_LIMIT_NO_GDR
    for card, (bw, lat) in card_to_result.items():
        if bw < bw_lower_limit or lat > LAT_UPPER_LIMIT:
            return False
    return True


def find_good_hosts(
    connections_to_result: Dict[str, Dict[str, Tuple[float, float]]], gdr_enabled: bool = USE_GDR
) -> List[str]:
    good_hosts = []
    for connection, result in connections_to_result.items():
        if is_passing_host(result, gdr_enabled):
            good_hosts.append(connection)
    return good_hosts


def parse_p2p_output(uncleaned_output: str, key: str) -> Optional[float]:
    """
    The p2p output is terrible:
    - The headers are not separated by tabs, but by variable numbers of spaces.
    - The header values may themselves contain spaces.
    - The --output=json option produces invalid JSON.

    As a result, we have some nasty parsing logic here; see the unit tests for illustrative
    examples.

    If/when there is a better way to extract the desired information, we should use it.
    """
    split_text = re.split("-+", uncleaned_output)
    if len(split_text) < 3:
        return 0
    data_values = split_text[-2].strip()
    # Change all the headers to not have spaces within them
    data_values = data_values.replace("% percentile", "%percentile")
    data_values = data_values.replace("BW ", "BW")
    data_values = re.sub("Conflicting CPU frequency.*", "", data_values)
    lines = [l for l in data_values.splitlines() if len(l.strip()) > 0]
    headers = [x.strip() for x in re.split(r"\s+", lines[0]) if len(x.strip()) > 0]
    values = [x.strip() for x in re.split(r"\s+", lines[1]) if len(x.strip()) > 0]
    for header, val in zip(headers, values):
        if header == key:
            return float(val)
    raise ValueError(f"Could not find key {key} in output {uncleaned_output}, output format may have changed")


def _build_ib_write_bw_command(
    card: HcaDescription,
    iters: int,
    port: int,
    other_ip: Optional[str] = None,
) -> str:
    return " ".join(
        (
            "ib_write_bw",
            "-b",
            f"-d {card}",
            f"--iters {iters}",
            f"-p {port}",
            *((other_ip,) if other_ip is not None else ()),
            "--report_gbits",
        )
    )


def shutdown_test(connection: CommandRunner, command: str) -> None:
    if "[" not in command:
        # This is to escape the command, so we don't end up killing the pkill before it kills the process we care about
        command = "[" + command[0] + "]" + command[1:]
    tries = 0
    max_retries = 16
    while True:
        connection.run_command(f"pkill -f {command}")
        running_commands_res = connection.run_command(f"ps aux | grep {command} | wc -l ")
        if running_commands_res.returncode != "0":
            break
        if running_commands_res.output.strip() == "0":
            break
        try:
            print(f"killed {command} on {connection} on try {tries}")
            connection.run_command(f"pkill -f {command}")
        except:
            pass
        tries += 1
        if tries >= max_retries:
            print(f"failed to kill {command} on {connection} after {max_retries} tries")
            break
        

def run_single_rail_test(
    connection: CommandRunner,
    other_ip: str,
    is_head: bool,
    gpu_idx_and_card:  HcaDescription,
    same_host: bool = False,
    card_index : int = 0,
    iters: int = 5_000,
) -> Tuple[Union[CommandRunner, str], str, Tuple[float, float]]:
    card = gpu_idx_and_card
    bw_output, lat_output = BW_ERROR_VALUE, LAT_ERROR_VALUE
    try:
        if is_head:
            # Ensure the other card acting as a server has time to spin up
            time.sleep(5)
        with get_expiration_event(EXPIRATION_SECONDS) as event:
            other_ip = other_ip if is_head else ""
            if same_host:    
                port = 18515 + card_index
            else:
                port = 18515 + int(card.pcie_slot_index)
            
            command = _build_ib_write_bw_command( card=card,  other_ip=other_ip, iters=iters, port=port)
            print(f" {connection.ip} run command: {command} ")
            bw_result = connection.run_command(command, shutdown_event=event)
            #print(f"result:{bw_result.returncode}")
            #print(f"output:{bw_result.output}")
            #print(f" {connection.ip} -----02------ command: {command} ")
            if bw_result.returncode == 0 :
                bw_output = parse_p2p_output(bw_result.output, key=BW_TEST_OUTPUT_KEY)
            else:
                print(
                    f"Trying to kill ib_write_bw on {connection.ip}:{card.pcie_device_description} with {bw_result.returncode} {bw_result.output}"
                )
                shutdown_test(connection, f"'ib_write_b[w] -b -d {card.pcie_device_description}'")
        if is_head:
            # Ensure the other card acting as a server has time to spin up
            time.sleep(5)
        
        #print(f"end bandwidth test on {connection.ip}")
        #print(f"start latency test on {connection.ip}")

        with get_expiration_event(EXPIRATION_SECONDS) as event:
            other_ip = other_ip if is_head else ""
            if same_host:
                port = 18514 - card_index
            else:
                port = 18514 - int(card.__str__().split("_")[1])
            # Perftest supports CUDA latency tests with read/send verbs only
            command = f"ib_write_lat -d {card.pcie_device_description} {other_ip} --iters {iters} -p {port}"
            print(f" {connection.ip} run command: {command} ")
            lat_result = connection.run_command(command, shutdown_event=event)
            #print(f" {connection.ip} -----04------ command: {command} ")
            if lat_result.returncode == 0:
                lat_output = parse_p2p_output(lat_result.output, key=LAT_TEST_OUTPUT_KEY)
            else:
                print(
                    f"Trying to kill ib_write_lat on {connection.ip}:{card.pcie_device_description} with {lat_result.returncode} {lat_result.output}"
                )
                shutdown_test(connection, f"'ib_write_[l]at -d {card.pcie_device_description}'")
        print(f"Results for {connection.ip}:{card.pcie_device_description} bw: {bw_output} lat: {lat_output}")
        return connection, card, (bw_output, lat_output)
    except Exception as e:
        # We add square brackets around the w such that we avoid killing the `pkill` command itself?
        shutdown_test(connection, f"'ib_write_[l]at -d {card.pcie_device_description}'")
        shutdown_test(connection, f"'ib_write_b[w] -d {card.pcie_device_description}'")
        logger.info(f"caught exception on {connection}:\n{e}")
        return connection, card, (bw_output, lat_output)
    

def ip_prefix_to_ipaddress(ip_prefix: str,index:int) -> str:
    #将IP地址前缀+序号index，生成对应的IP地址
    p2p_ip = ""
    #从前缀字符串中，提取掩码
    mask = ipaddress.ip_network(ip_prefix).netmask
    ip_subnet = ipaddress.ip_network(ip_prefix).network_address
    
    #ip_subnet + index 生成IP地址
    ip_subnet._ip = ip_subnet._ip + index
    p2p_ip = str(ip_subnet)
    
    return p2p_ip 

def run_p2p_ib_test(
    connection: Union[CommandRunner, str], other_ip: int, is_head: True
) -> Tuple[str, Dict[str, Tuple[float, float]]]:
    card_to_result = {}
    for index,card in enumerate(MLX_CARDS):
        #print(card)
        #print(MLX_CARDS_SUBNET)
        ip_prefix = MLX_CARDS_SUBNET[str(card.pcie_device_description)]
        p2p_ip = ip_prefix_to_ipaddress(ip_prefix,other_ip)
        
        _, _, card_result = run_single_rail_test(connection, p2p_ip, is_head, card, same_host=False)
        card_to_result[card] = card_result
    return connection.ip, card_to_result

def set_host_ib_card_ip( connection: CommandRunner, ip_index: int) :
    
    for index,card in enumerate(MLX_CARDS):
       
        ip_prefix = MLX_CARDS_SUBNET[str(card.pcie_device_description)]
        card_ip = ip_prefix_to_ipaddress(ip_prefix,ip_index)
        mask = ipaddress.ip_network(ip_prefix).netmask
        app_path = os.path.abspath(os.path.dirname(__file__))
        #set card ip
        card_name = str(card.pcie_device_description)
        ifconfig_path = os.path.join(app_path,"set_mlx_ipaddress.sh")
        command = f"bash {ifconfig_path} {card_name} {card_ip}  {mask}"
        #card_name = str(card.pcie_device_description)
        #command = f"ibdev2netdev |grep {card_name} |awk '{print$5}'|xargs -I {} bash -c 'ifconfig {} {card_ip} netmask {mask} up'"
        #print(connection,command,ip_index)
        res = connection.run_command(command)
        #print(res)
        
    #关闭之前的残留指令
    shutdown_test(connection, f"ib_write_b[w] ")
    shutdown_test(connection, f"ib_write_la[t] ")

def run_single_p2p(
    run: int,
    connections: Sequence[FullConnection],
    output_file: Optional[Path] = None,
) -> Dict[str, Dict[str, Tuple[float, float]]]:
    connection_pairs = list(zip(connections[: len(connections) // 2], connections[len(connections) // 2 :]))
    servers = [(pair[0].ssh_connection, pair[1].internal_index, False) for pair in connection_pairs]
    clients = [(pair[1].ssh_connection, pair[0].internal_index, True) for pair in connection_pairs]
    alternating_server_client = [item for pair in zip(servers, clients) for item in pair]
    
    #设置测试网卡IP地址
    for connection in connections:
        #print(connection)
        set_host_ib_card_ip(connection.ssh_connection,connection.internal_index)
    
    connection_to_result = {}
    
    with ThreadPoolExecutor(max_workers=len(alternating_server_client)) as executor:
        results = executor.map(
            lambda group_and_card: run_p2p_ib_test(
                connection=group_and_card[0],
                other_ip=group_and_card[1],
                is_head=group_and_card[2],
            ),
            alternating_server_client,
        )
        for connection, result in results:
            if output_file:
                with output_file.open("a+") as f:
                    f.write(f"Results for {connection} in run {run}: {result}\n")
            connection_to_result[connection] = result

    return connection_to_result

def set_single_host_ib_card_ip( connection: CommandRunner) :
    
    ip_prefix = None
    for index,card in enumerate(MLX_CARDS):
        ip_index = index + 64
        if ip_prefix == None:
            ip_prefix = MLX_CARDS_SUBNET[str(card.pcie_device_description)]
        card_ip = ip_prefix_to_ipaddress(ip_prefix,ip_index)
        mask = ipaddress.ip_network(ip_prefix).netmask
        app_path = os.path.abspath(os.path.dirname(__file__))
        #set card ip
        card_name = str(card.pcie_device_description)
        ifconfig_path = os.path.join(app_path,"set_mlx_ipaddress.sh")
        command = f"bash {ifconfig_path} {card_name} {card_ip} {mask}"
        #card_name = str(card.pcie_device_description)
        #command = f"ibdev2netdev |grep {card_name} |awk '{print$5}'|xargs -I {} bash -c 'ifconfig {} {card_ip} netmask {mask} up'"
        #print(connection,command,ip_index)
        res = connection.run_command(command)
        #print(res)
        
    #关闭之前的残留指令
    shutdown_test(connection, f"ib_write_b[w] ")
    shutdown_test(connection, f"ib_write_la[t] ")
    
    return ip_prefix
def run_single_host_p2p(
    run: int,
    full_connections: Sequence[FullConnection],
    output_file: Optional[Path] = None,
) -> Dict[str, Dict[str, Tuple[float, float]]]:
    first_half_cards = MLX_CARDS[: len(MLX_CARDS) // 2]
    second_half_cards = MLX_CARDS[len(MLX_CARDS) // 2 :]

    #ip_prefix = None
    #设置测试网卡IP地址
    for connection in full_connections:
        shutdown_test(connection.ssh_connection, f"ib_write_b[w] ")
        shutdown_test(connection.ssh_connection, f"ib_write_la[t] ")
    #    ip_prefix = set_single_host_ib_card_ip(connection.ssh_connection)
    servers = [
        (connection.ssh_connection, connection.internal_ip, False,  driver,gpu_idx)
        for gpu_idx, driver in enumerate(first_half_cards)
        for connection in full_connections
    ]
    #print("----------------------------------------------03")
    clients = [
        (connection.ssh_connection, connection.internal_ip, True,  driver,gpu_idx)
        for gpu_idx, driver in enumerate(second_half_cards)
        for connection in full_connections
    ]
    #print("----------------------------------------------04")
    alternating_server_client = [item for pair in zip(servers, clients) for item in pair]
    max_workers = len(alternating_server_client)
    
    #print(alternating_server_client)
    #for item in alternating_server_client:
    #    print(item)
    connection_to_result = {connection.ssh_connection.ip: dict() for connection in full_connections}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        run_results = executor.map(
            lambda group_and_card: run_single_rail_test(
                connection=group_and_card[0],
                other_ip=group_and_card[1],
                is_head=group_and_card[2],
                gpu_idx_and_card=group_and_card[3],
                card_index=group_and_card[4],
                same_host=True,
            ),
            alternating_server_client,
        )
        for connection, card, result in run_results:
            #if output_file:
            #    with output_file.open("a+") as f:
            #        f.write(f"Results for {connection} {card} in run {run}: {result}\n")
            connection_to_result[connection.ip][card] = result

    print(f"Finished running run {run} with {connection_to_result}")

    return connection_to_result


def run_p2p_ib_tests(
    connections: Sequence[CommandRunner],
    output_file: str = None,
    single_host: bool = False,
    num_iterations: int = 8,
) -> Dict[str, Dict[str, int]]:
    test = "p2p_ib" if not single_host else "host_p2p_ib"
    ip_to_runs_passed: Dict[str, int] = {connection.ip: 0 for connection in connections}

    full_connections =[]
    internal_index = 2
    for c in connections:
        full_connections.append(FullConnection(ssh_connection=c,internal_ip="127.0.0.1",internal_index=internal_index))
        internal_index = internal_index + 1
    
    last_results = None
    for run_count in range(num_iterations):
        try:
            local_rng = random.Random()
            local_rng.seed(run_count)
            run_count += 1
            if not single_host:
                #对节点进行随机排序
                mixed_nodes = local_rng.sample(full_connections, len(full_connections))
                connection_to_result = run_single_p2p(run_count, mixed_nodes, output_file)
            else:
                connection_to_result = run_single_host_p2p(run_count, full_connections, output_file)
            good_hosts = find_good_hosts(connection_to_result)
            for host in good_hosts:
                if host not in ip_to_runs_passed:
                    print(f"Host {host} not in ip_to_runs_passed")
                    raise ValueError(f"Host {host} not in ip_to_runs_passed")
                ip_to_runs_passed[host] += 1
            last_results = connection_to_result
            bad_hosts = [connection.ip for connection in connections if connection.ip not in good_hosts]
            bad_hosts_results = {ip: last_results.get(ip, (BW_ERROR_VALUE, LAT_ERROR_VALUE)) for ip in bad_hosts}
            print(f"p2p_hosts {bad_hosts} with results: {bad_hosts_results}")
            print(
                f"{test} after {run_count} iterations results: {sorted(ip_to_runs_passed.items(), key = lambda item: item[1])}"
            )
        
        finally:
            for connection in connections:
                shutdown_test(connection, "ib_writ[e]_")
        # Wait a little after the tests to ensure everything can be cleaned up correctly
        time.sleep(5)

    print(f"From last run all p2p_hosts results: {last_results}\n")
    print(f"Final p2p_host results: {sorted(ip_to_runs_passed.items(), key = lambda item: item[1])}")

   
    ip_to_metrics = {
        ip: {"passes": passes, "count": num_iterations, "ratio": passes / num_iterations}
        for ip, passes in ip_to_runs_passed.items()
    }
    return ip_to_metrics
