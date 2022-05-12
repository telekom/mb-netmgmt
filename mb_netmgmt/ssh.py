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

import os
import re
from socketserver import BaseRequestHandler, TCPServer

import paramiko

from mb_netmgmt.__main__ import Protocol

Server = TCPServer
stopped = False
message_id_regex = ' message-id="([^"]*)"'


class ParamikoServer(paramiko.ServerInterface):
    def get_allowed_auths(*args):
        return "password,publickey"

    def check_auth_password(*args):
        return paramiko.AUTH_SUCCESSFUL

    def check_auth_publickey(*args):
        return paramiko.AUTH_SUCCESSFUL

    def check_channel_request(*args):
        return paramiko.OPEN_SUCCEEDED

    def check_channel_pty_request(*args):
        return True

    def check_channel_shell_request(*args):
        return True

    def check_channel_subsystem_request(*args):
        return True


class Handler(BaseRequestHandler, Protocol):
    message_terminator = b"\n"

    def handle(self):
        self.callback_url = self.server.callback_url
        t = paramiko.Transport(self.request)
        t.add_server_key(paramiko.DSSKey.generate())
        t.add_server_key(paramiko.ECDSAKey.generate())
        t.add_server_key(paramiko.RSAKey.generate(4096))
        t.start_server(server=ParamikoServer())
        self.channel = t.accept()
        self.open_upstream()
        self.handle_request({"command": ""}, "")
        while not stopped:
            request, request_id = self.read_request()
            self.handle_request(request, request_id)

    def send_upstream(self, request, request_id):
        self.upstream_channel.sendall(
            replace_message_id(request["command"], request_id)
        )

    def read_request(self):
        request = self.read_message(self.channel)
        return (
            {"command": replace_message_id(request.decode(), "")},
            get_message_id(request.decode()),
        )

    def respond(self, response, request_id):
        response = replace_message_id(response["response"], request_id)
        self.channel.sendall(response)

    def open_upstream(self):
        if "NETCONF_HOSTNAME" not in os.environ:
            return
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy)
        client.connect(
            os.environ["NETCONF_HOSTNAME"],
            830,
            os.environ["NETCONF_USERNAME"],
            os.environ["NETCONF_PASSWORD"],
        )
        transport: paramiko.Transport = client._transport
        self.upstream_channel = transport.open_session()
        self.upstream_channel.invoke_subsystem("netconf")

    def read_proxy_response(self):
        return {"response": self.read_message(self.upstream_channel).decode()}

    def read_message(self, channel):
        message = b""
        while self.message_terminator not in message and not stopped:
            message += channel.recv(1024)
        return message


def get_message_id(rpc):
    try:
        return re.findall(message_id_regex, rpc)[0]
    except IndexError:
        return None


def replace_message_id(rpc, message_id):
    return re.sub(message_id_regex, f' message-id="{message_id}"', rpc)
