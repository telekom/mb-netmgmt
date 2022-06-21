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
    with mb(imposter(protocol, None)):
        pass


def test_ssh():
    with mb(imposter("ssh", [prompt_stub()]), "debug"):
        client = connect_ssh()
        chan = client.invoke_shell()
        out = chan.recv(1024)
        assert out == prompt


def test_ssh_proxy():
    with mb(
        imposter(
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
    original_open_upstream = netconf.Handler.open_upstream
    original_post_request = netconf.Handler.post_request
    netconf.Handler.open_upstream = lambda handler: None
    netconf.Handler.post_request = mock_post_request
    server = create_server(netconf, port, None)
    Thread(target=server.serve_forever).start()
    with ncclient.manager.connect(
        host="localhost", port=port, password="", hostkey_verify=False
    ) as m:
        assert m.session_id == "1"
        assert "urn:ietf:params:netconf:base:1.0" in m.server_capabilities
        m.get_config("running")
    netconf.stopped = True
    server.shutdown()
    netconf.stopped = False
    netconf.Handler.open_upstream = original_open_upstream
    netconf.Handler.post_request = original_post_request


def mock_post_request(handler, request):
    command = request["command"]
    if "<nc:hello" in command:
        return {"response": {"response": "<hello/>]]>]]>"}}
    return {
        "response": {
            "response": '<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id=""/>]]>]]>'
        }
    }


def test_netconf_upstream():
    from mb_netmgmt.netconf import Handler

    global port
    port = 8831
    Handler.handle = lambda handler: None
    Handler.get_to = lambda handler: urlparse(f"netconf://localhost:{port}")
    handler = Handler(None, None, None)
    expected_proxy_response = (
        '<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id=""/>'
        + MSG_DELIM.decode()
    )
    with mb(
        imposter(
            "netconf",
            [
                {
                    "predicates": [
                        {
                            "endsWith": {
                                "command": "<nc:get-config>running</nc:get-config></nc:rpc>]]>]]>"
                            }
                        }
                    ],
                    "responses": [
                        {"is": {"response": expected_proxy_response}},
                    ],
                },
                {
                    "responses": [
                        {"is": {"response": "<hello/>" + MSG_DELIM.decode()}},
                    ]
                },
            ],
        ),
        "debug",
    ):
        handler.open_upstream()
        handler.send_upstream(
            {
                "command": '<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42"><get-config>running</get-config></rpc>'
                + MSG_DELIM.decode()
            },
            42,
        )
        proxy_response = handler.read_proxy_response()
        assert proxy_response["response"] == expected_proxy_response


def imposter(protocol, stubs):
    return [{"protocol": protocol, "port": port, "stubs": stubs}]


def create_proxy_response(message_id):
    return {
        "response": f'<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="{message_id}"/>'
        + MSG_DELIM.decode()
    }
