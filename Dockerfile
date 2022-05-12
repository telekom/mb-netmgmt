FROM bbyars/mountebank
USER root
RUN apk add scapy py3-requests py3-pip py3-paramiko
RUN pip install mb-netmgmt
ADD https://raw.githubusercontent.com/telekom/mb-netmgmt/main/protocols.json .
