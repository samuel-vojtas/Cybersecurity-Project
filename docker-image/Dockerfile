FROM fedora:latest

RUN dnf install -y nebula iputils net-tools vim nc telnet iproute python3-pip
RUN dnf clean all
RUN pip install pyyaml

CMD ["/bin/bash"]
