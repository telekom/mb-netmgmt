FROM node:16-alpine
RUN npm install -g mountebank
ENTRYPOINT ["mb"]
RUN apk add \
    git \
    py3-lxml \
    py3-paramiko \
    py3-pip \
    py3-requests \
    # dependencies for ruamel.yaml:
    gcc \
    musl-dev \
    python3-dev
RUN pip install scapy@git+https://github.com/christian-sahlmann/scapy@christian-sahlmann/ber-decoding-3900
RUN pip install mb-netmgmt
WORKDIR /usr/lib/python3.11/site-packages/mb_netmgmt
