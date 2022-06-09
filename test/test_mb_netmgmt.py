from threading import Thread
import paramiko
import pytest
from mb_netmgmt import mb, ssh
from mb_netmgmt.__main__ import create_server

port = 8080


@pytest.mark.parametrize("protocol", ["http", "snmp", "telnet", "netconf"])
def test_create_imposter(protocol):
    with mb([{"protocol": protocol, "port": port}]):
        pass


def test_ssh():
    with mb([{"protocol": "ssh", "port": port}]):
        connect_ssh()


def test_create_ssh_server():
    ssh.Handler.handle_request = lambda *args: None
    server = create_server(ssh, port, None)
    Thread(target=server.serve_forever).start()
    connect_ssh()
    server.shutdown()


def connect_ssh():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy)
    client.connect("localhost", port)
    client.close()
