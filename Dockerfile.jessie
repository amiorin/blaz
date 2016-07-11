FROM debian:jessie

RUN apt-get update && \
    apt-get install -y python3-setuptools && \
    easy_install3 pip

COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --upgrade -r /tmp/requirements.txt && \
    rm -rf /tmp/requirements.txt

COPY entrypoint.py /usr/local/bin/entrypoint.py
ENTRYPOINT ["/usr/local/bin/entrypoint.py"]
CMD ["bash"]
