import os
from threading import Thread

import ncclient.manager
import paramiko
import pytest
from mb_netmgmt import mb, netconf, ssh
from mb_netmgmt.__main__ import create_server

port = 8080
prompt = b"prompt"


@pytest.mark.parametrize("protocol", ["http", "snmp", "telnet", "netconf"])
def test_create_imposter(protocol):
    with mb([{"protocol": protocol, "port": port}]):
        pass


def test_ssh():
    with mb([{"protocol": "ssh", "port": port, "stubs": [prompt_stub()]}], "debug"):
        client = connect_ssh()
        chan = client.invoke_shell()
        out = chan.recv(1024)
        assert out == prompt


def test_ssh_proxy():
    with mb(
        [
            {
                "protocol": "ssh",
                "port": port,
                "stubs": [
                    prompt_stub(),
                    {
                        "responses": [
                            {
                                "proxy": {
                                    "to": f"ssh://{os.environ['NETCONF_USERNAME']}:{os.environ['NETCONF_PASSWORD']}@localhost"
                                }
                            },
                        ]
                    },
                ],
            }
        ]
    ):
        client = connect_ssh()
        chan = client.invoke_shell()
        out = chan.recv(1024)
        assert out == prompt


def prompt_stub():
    return {"responses": [{"is": {"response": prompt}}]}


def test_create_ssh_server():
    server = create_server(ssh, port, None)
    Thread(target=server.serve_forever).start()
    connect_ssh().close()
    server.shutdown()


def connect_ssh():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy)
    client.connect("localhost", port)
    return client


def test_create_netconf_server():
    port = 8830
    netconf.Handler.open_upstream = lambda handler: None
    netconf.Handler.post_request = lambda *args: {
        "response": {"response": "<hello/>]]>]]>"}
    }
    server = create_server(netconf, port, None)
    Thread(target=server.serve_forever).start()
    ncclient.manager.connect(host="localhost", port=port, hostkey_verify=False)
    ssh.stopped = True
    server.shutdown()
