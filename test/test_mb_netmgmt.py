import pytest
from mb_netmgmt import mb


@pytest.mark.parametrize("protocol", ["http", "snmp", "telnet", "netconf"])
def test_create_imposter(protocol):
    with mb([{"protocol": protocol, "port": 8080}]):
        pass
