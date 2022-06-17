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

from queue import Queue

from ncclient.manager import connect
from ncclient.transport import SessionListener
from ncclient.transport.ssh import END_DELIM, MSG_DELIM, PORT_NETCONF_DEFAULT

from mb_netmgmt.ssh import Handler as SshHandler
from mb_netmgmt.ssh import Server


class Handler(SshHandler):
    message_terminators = [MSG_DELIM, END_DELIM]
    default_port = 830

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
        )
        session = self.manager._session
        listener = Listener()
        self.queue = listener.queue
        session.add_listener(listener)
        self.upstream_channel = session._channel

    def handle_prompt(self):
        pass

    def read_proxy_response(self):
        return {"response": self.queue.get() + MSG_DELIM.decode()}


class Listener(SessionListener):
    def __init__(self):
        self.queue = Queue()

    def callback(self, root, raw):
        self.queue.put(raw)
