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

"""Network Management Protocols for Mountebank"""
__version__ = "0.0.5"

import os
import subprocess
import time
from contextlib import contextmanager

import requests
import yaml


@contextmanager
def mb(imposters):
    with subprocess.Popen("mb", cwd=os.path.dirname(__file__)) as mb:
        try:
            put_imposters("localhost", imposters)
            yield mb
        finally:
            mb.terminate()


def put_imposters(host, imposters):
    while True:
        try:
            response = requests.put(
                f"http://{host}:2525/imposters",
                json={"imposters": imposters},
            )
            break
        except requests.ConnectionError:
            time.sleep(1)
    try:
        response.raise_for_status()
    except requests.HTTPError as e:
        raise RuntimeError(e.response.json()["errors"])


def dump_imposters(host, name):
    response = requests.get(
        f"http://{host}:2525/imposters",
        {"replayable": True, "removeProxies": True},
    )
    yaml.safe_dump(response.json(), open(f"{name}.yaml", "w"))


def load_imposters(host, name):
    put_imposters(
        host,
        yaml.safe_load(open(f"{name}.yaml").read())["imposters"],
    )
