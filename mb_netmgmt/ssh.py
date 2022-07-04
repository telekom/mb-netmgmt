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

import paramiko

from mb_netmgmt.__main__ import Protocol

stopped = False


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
    message_terminators = [b"\n"]
    default_port = 22

    def handle(self):
        self.callback_url = self.server.callback_url
        transport = start_server(self.request)
        self.channel = transport.accept()
        self.open_upstream()
        self.handle_prompt()
        while not stopped:
            request, request_id = self.read_request()
            self.handle_request(request, request_id)

    def send_upstream(self, request, request_id):
        self.upstream_channel.sendall(request["command"])

    def read_request(self):
        request = self.read_message(self.channel)
        return {"command": request.decode()}, None

    def respond(self, response, request_id):
        response = response["response"]
        self.channel.sendall(response)

    def open_upstream(self):
        to = self.get_to()
        if not to:
            return
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy)
        client.connect(
            to.hostname, to.port or self.default_port, to.username, to.password
        )
        transport: paramiko.Transport = client._transport
        self.upstream_channel = transport.open_session()

    def handle_prompt(self):
        self.handle_request({"command": ""}, "")

    def read_proxy_response(self):
        return {"response": self.read_message(self.upstream_channel).decode()}

    def read_message(self, channel):
        message = b""
        end_of_message = False
        while not end_of_message and not stopped:
            message += channel.recv(1024)
            for terminator in self.message_terminators:
                if terminator in message:
                    end_of_message = True
        return message


def start_server(request):
    t = paramiko.Transport(request)
    t.add_server_key(paramiko.DSSKey.generate())
    t.add_server_key(paramiko.ECDSAKey.generate())
    t.add_server_key(paramiko.RSAKey.generate(4096))
    t.start_server(server=ParamikoServer())
    return t
