FROM amiorin/alpine-blaz

COPY . /tmp/blaz
RUN pip2 install /tmp/blaz && \
    pip3 install /tmp/blaz && \
    rm -rf /tmp/blaz
