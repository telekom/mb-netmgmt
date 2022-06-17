import os
from threading import Thread
from urllib.parse import urlparse

import ncclient.manager
import paramiko
import pytest
from mb_netmgmt import mb, netconf, ssh
from mb_netmgmt.__main__ import create_server
from ncclient.transport.ssh import MSG_DELIM

port = 8080
prompt = b"prompt"


@pytest.mark.parametrize("protocol", ["http", "snmp", "telnet", "netconf"])
def test_create_imposter(protocol):
    with mb(imposters(protocol, None)):
        pass


def test_ssh():
    with mb(imposters("ssh", [prompt_stub()]), "debug"):
        client = connect_ssh()
        chan = client.invoke_shell()
        out = chan.recv(1024)
        assert out == prompt


def test_ssh_proxy():
    with mb(
        imposters(
            "ssh",
            [
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
        )
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
    netconf.Handler.post_request = mock_post_request
    server = create_server(netconf, port, None)
    Thread(target=server.serve_forever).start()
    with ncclient.manager.connect(
        host="localhost", port=port, password="", hostkey_verify=False
    ) as m:
        m.get_config("running")
    ssh.stopped = True
    server.shutdown()


def mock_post_request(handler, request):
    command = request["command"]
    if "<nc:hello" in command:
        return {"response": {"response": "<hello/>]]>]]>"}}
    return {
        "response": {
            "response": '<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id=""/>]]>]]>'
        }
    }


def imposters(protocol, stubs):
    return [{"protocol": protocol, "port": port, "stubs": stubs}]
