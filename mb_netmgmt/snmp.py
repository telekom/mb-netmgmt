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

import binascii
from base64 import b64decode, b64encode
from socket import SOCK_DGRAM, socket
from socketserver import DatagramRequestHandler, ThreadingUDPServer, UDPServer

from scapy.asn1.asn1 import ASN1_Class_UNIVERSAL
from scapy.layers.snmp import SNMP, SNMPbulk, SNMPresponse, SNMPvarbind

from mb_netmgmt.__main__ import Protocol

Server = ThreadingUDPServer


class Handler(DatagramRequestHandler, Protocol):
    def handle(self):
        self.callback_url = self.server.callback_url
        request, request_id = self.read_request()
        self.handle_request(request, request_id)

    def handle_request(self, request, request_id):
        mb_response = self.post_request(request)
        if "response" not in mb_response:
            self.open_upstream(mb_response["proxy"]["to"])
            self.send_upstream(request, request_id)
        response = self.get_response(mb_response)
        self.respond(response, request_id)

    def respond(self, response, request_id):
        response_varbindlist = self.translate_json_to_network_response(response)
        snmp_response = SNMP(
            PDU=SNMPresponse(
                id=request_id,
                varbindlist=response_varbindlist,
            )
        )
        self.wfile.write(bytes(snmp_response))

    def open_upstream(self, to):
        self.upstream_socket = socket(type=SOCK_DGRAM)
        self.upstream_socket.connect((to, 161))

    def read_proxy_response(self):
        bytes_response = self.upstream_socket.recv(UDPServer.max_packet_size)
        snmp_response = SNMP(bytes_response)
        result = dict()
        for varbind in snmp_response.PDU.varbindlist:
            result[varbind.oid.val] = {
                "val": decode(varbind.value.val),
                "tag": str(varbind.value.tag),
            }

        return result

    def send_upstream(self, request, request_id):
        oids = request["oids"]
        pdu_type = type(self.snmp_request.PDU)
        kwargs = dict()
        if pdu_type == SNMPbulk:
            kwargs["max_repetitions"] = 10
        request = SNMP(
            version="v2c",
            community=self.snmp_request.community,
            PDU=pdu_type(
                id=self.snmp_request.PDU.id,
                varbindlist=[SNMPvarbind(oid=oid) for oid in oids],
                **kwargs,
            ),
        )
        self.upstream_socket.send(bytes(request))

    def read_request(self):
        self.snmp_request = SNMP(self.rfile.read())
        pdu_id = self.snmp_request.PDU.id.val
        json_request = {
            "oids": [varbind.oid.val for varbind in self.snmp_request.PDU.varbindlist]
        }
        return json_request, pdu_id

    def translate_request_to_json(self, varbind):
        return {"oid": varbind.oid.val}

    def translate_json_to_network_response(self, json):
        result = list()
        for oid, response in json.items():
            if oid.startswith("_"):
                continue
            value = response["val"]
            try:
                value = b64decode(value, validate=True)
            except (binascii.Error, TypeError):
                pass
            asn1_class = ASN1_Class_UNIVERSAL.__dict__[response["tag"]]
            result += SNMPvarbind(oid=oid, value=asn1_class.asn1_object(value))
        return result


def decode(value):
    try:
        return value.decode()
    except AttributeError:
        return value
    except UnicodeDecodeError:
        return b64encode(value).decode()
