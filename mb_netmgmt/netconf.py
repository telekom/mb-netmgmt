# This file is part of the project mb-netmgmt
#
# (C) 2022 Deutsche Telekom AG
#
# Deutsche Telekom AG and all other contributors / copyright
# owners license this file to you under the terms of the GPL-2.0:
#
# mb-netmgmt is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# mb-netmgmt is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with mb-netmgmt. If not, see <https://www.gnu.org/licenses/

from socketserver import BaseRequestHandler
from socketserver import TCPServer as Server

from lxml import etree
from ncclient.devices.default import DefaultDeviceHandler
from ncclient.manager import connect
from ncclient.transport.parser import DefaultXMLParser
from ncclient.transport.session import (
    HelloHandler,
    NetconfBase,
    SessionListener,
    qualify,
    sub_ele,
    to_ele
)
from ncclient.transport.ssh import MSG_DELIM, PORT_NETCONF_DEFAULT, SSHSession

from mb_netmgmt.__main__ import Protocol
from mb_netmgmt.ssh import accept

stopped = False


class Handler(BaseRequestHandler, Protocol):
    def setup(self):
        session = SSHSession(DefaultDeviceHandler())
        session.add_listener(Listener(super().handle_request))
        self.parser = DefaultXMLParser(session)
        self.session = session

    def handle(self):
        self.callback_url = self.server.callback_url
        self.channel = accept(self.request)
        self.open_upstream()
        self.session._connected = True
        self.handle_prompt()
        self.session._channel = self.channel
        self.session.run()

    def open_upstream(self):
        to = self.get_to()
        if not to:
            return
        self.manager = connect(
            host=to.hostname,
            port=to.port or PORT_NETCONF_DEFAULT,
            username=to.username,
            password=to.password,
            hostkey_verify=False,
            timeout=60,
        )

    def handle_prompt(self):
        hello = to_ele(
            HelloHandler.build(DefaultDeviceHandler._BASE_CAPABILITIES, None)
        )

        # A server sending the <hello> element MUST include a <session-id>
        # element containing the session ID for this NETCONF session.
        # https://datatracker.ietf.org/doc/html/rfc6241#section-8.1
        session_id = sub_ele(hello, "session-id")
        session_id.text = "1"

        self.channel.sendall(to_xml(hello) + MSG_DELIM.decode())

        def init_cb(id, capabilities):
            if "urn:ietf:params:netconf:base:1.1" in capabilities:
                self.session._base = NetconfBase.BASE_11

        self.session.add_listener(HelloHandler(init_cb, None))

    def read_proxy_response(self):
        return {"rpc-reply": unwrap_proxy_response(self.rpc_reply._root)}

    def send_upstream(self, request, request_id):
        self.rpc_reply = self.manager.rpc(to_ele(request["rpc"]))

    def respond(self, response, request_id):
        message = wrap_reply(response["rpc-reply"], request_id)
        self.session.send(message)


class Listener(SessionListener):
    def __init__(self, handle_request):
        self.handle_request = handle_request

    def callback(self, root, raw):
        tag, attrs = root
        if (tag == qualify("hello")) or (tag == "hello"):
            return
        ele = etree.fromstring(raw.encode())
        request = {"rpc": to_xml(ele[0])}
        self.handle_request(request, attrs["message-id"])


def wrap_reply(rpc_reply, message_id):
    return f'<nc:rpc-reply xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="{message_id}">{rpc_reply}</nc:rpc-reply>'


def unwrap_proxy_response(root):
    try:
        return to_xml(root[0])
    except IndexError:
        return root.text


def to_xml(ele):
    return etree.tostring(ele, pretty_print=True).decode().strip()
