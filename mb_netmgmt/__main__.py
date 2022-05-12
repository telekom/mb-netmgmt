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

import importlib
import json
import sys

import requests


def create_server(protocol, port, callback_url):
    server_address = ("0.0.0.0", port)
    server = protocol.Server(server_address, protocol.Handler, bind_and_activate=False)
    server.callback_url = callback_url
    server.allow_reuse_address = True
    server.server_bind()
    server.server_activate()
    return server


class Protocol:
    def handle_request(self, request, request_id):
        mb_response = self.post_request(request)
        if "response" not in mb_response:
            self.send_upstream(request, request_id)
        response = self.get_response(mb_response)
        self.respond(response, request_id)

    def get_response(self, mb_response):
        try:
            return mb_response["response"]
        except KeyError:
            proxy_response = self.read_proxy_response()
            response = requests.post(
                mb_response["callbackURL"], json={"proxyResponse": proxy_response}
            )
            response.raise_for_status()
            return response.json()

    def send_upstream(self, request, request_id):
        raise NotImplementedError

    def read_proxy_response(self):
        raise NotImplementedError

    def respond(self, response, request_id):
        raise NotImplementedError

    def post_request(self, request):
        response = requests.post(
            self.callback_url,
            json={"request": request},
        )
        response.raise_for_status()
        return response.json()


if __name__ == "__main__":
    protocol_name = sys.argv[1]
    protocol = importlib.import_module(f"mb_netmgmt.{protocol_name}")

    args = json.loads(sys.argv[2])
    port = args["port"]
    callback_url = args["callbackURLTemplate"].replace(":port", str(port))

    server = create_server(protocol, port, callback_url)
    print(protocol_name, flush=True)
    server.serve_forever()
