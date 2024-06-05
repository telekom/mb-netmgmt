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

import re
import time
from socketserver import StreamRequestHandler
from socketserver import ThreadingTCPServer as Server

from Exscript.protocols import Telnet

from mb_netmgmt.__main__ import Protocol


class Handler(StreamRequestHandler, Protocol):
    def handle(self):
        self.callback_url = self.server.callback_url
        self.handle_username_prompt()
        self.username = extract_username(self.rfile.readline())
        self.handle_username()
        self.read_password()
        self.command_prompt = b"#"
        try:
            self.telnet.send(self.password)
            self.command_prompt = self.telnet.expect_prompt()[1].string.encode()
            self.telnet.app_authenticated = True
        except AttributeError:
            pass
        self.wfile.write(self.command_prompt)
        request = None
        self.stopped = False
        while not self.stopped:
            request, request_id = self.read_request()
            if not request:
                return
            self.handle_command(request, request_id)

    def handle_command(self, command, request_id):
        return self.handle_request({"command": command.decode()}, request_id)

    def send_upstream(self, request, request_id):
        self.telnet.send(request["command"])

    def read_request(self):
        return self.rfile.readline(), None

    def respond(self, response, request_id):
        self.wfile.write(response["response"].encode())
        if response["response"].encode() in [b"exit\r\n\r", b"quit\r\n\r"]:
            self.stopped = True

    def read_proxy_response(self):
        _, match = self.telnet.expect_prompt()
        return {"response": match.string}

    def handle_username_prompt(self):
        username_prompt = b"Username: "
        to = self.get_to()
        if to:
            t = Telnet(debug=4)
            t.connect(to.hostname)
            result = t.expect(t.get_username_prompt())
            username_prompt = (t.response[:-1] + result[1].string).encode()
            self.telnet = t
        self.wfile.write(username_prompt)

    def read_password(self):
        self.password = self.rfile.readline()
        while not self.password:
            time.sleep(1)
            self.password = self.rfile.readline()

    def handle_username(self):
        try:
            t = self.telnet
            t.send(self.username)
            result = t.expect(t.get_password_prompt())
            password_prompt = result[1].string.encode()
            self.wfile.write(password_prompt)
        except AttributeError:
            self.handle_request({"command": self.username.decode()}, None)


def extract_username(byte_string):
    return re.match(b".*?([-0-9a-zA-Z_].*\n)", byte_string).group(1)
