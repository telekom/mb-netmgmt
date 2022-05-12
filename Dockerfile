FROM bbyars/mountebank
USER root
RUN apk add scapy py3-requests py3-pip py3-paramiko
RUN pip install mb-netmgmt
WORKDIR /usr/lib/python3.9/site-packages/mb_netmgmt
