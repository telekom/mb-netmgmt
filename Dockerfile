FROM bbyars/mountebank
USER root
RUN apk add \
    py3-lxml \
    py3-paramiko \
    py3-pip \
    py3-requests \
    scapy \
    # dependencies for ruamel.yaml:
    gcc \
    musl-dev \
    python3-dev
RUN pip install mb-netmgmt
WORKDIR /usr/lib/python3.10/site-packages/mb_netmgmt
