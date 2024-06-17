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
RUN pip install scapy@git+https://github.com/secdev/scapy@8039989d856a807d7a794a9065588d1e0af64dab
WORKDIR /usr/lib/python3.11/site-packages
COPY . /usr/lib/python3.11/site-packages/mb_netmgmt
RUN pip install /usr/lib/python3.11/site-packages/mb_netmgmt
WORKDIR /usr/lib/python3.11/site-packages/mb_netmgmt
