FROM bbyars/mountebank
USER root
RUN apk add --repository=http://dl-cdn.alpinelinux.org/alpine/edge/testing \
    py3-ncclient \
    py3-paramiko \
    py3-pip \
    py3-requests \
    py3-yaml \
    scapy
RUN pip install mb-netmgmt
WORKDIR /usr/lib/python3.9/site-packages/mb_netmgmt
