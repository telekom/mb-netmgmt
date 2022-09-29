FROM bbyars/mountebank
USER root
RUN apk add \
    py3-lxml \
    py3-paramiko \
    py3-pip \
    py3-requests \
    py3-yaml \
    scapy
RUN pip install mb-netmgmt
WORKDIR /usr/lib/python3.10/site-packages/mb_netmgmt
