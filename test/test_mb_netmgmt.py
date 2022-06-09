from threading import Thread
import paramiko
import pytest
from mb_netmgmt import mb, ssh
from mb_netmgmt.__main__ import create_server


@pytest.mark.parametrize("protocol", ["http", "snmp", "telnet", "netconf"])
def test_create_imposter(protocol):
    with mb([{"protocol": protocol, "port": 8080}]):
        pass


def test_ssh():
    ssh.Handler.handle_request = lambda *args: None
    port = 2222
    server = create_server(ssh, port, None)
    Thread(target=server.serve_forever).start()
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy)
    client.connect("localhost", port)
    client.close()
    server.shutdown()
