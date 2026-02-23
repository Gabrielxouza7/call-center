FROM rockylinux:9

RUN dnf install -y python3-pip && \
    pip3 install twisted

WORKDIR /app

COPY server.py client.py /app/

CMD ["python3", "server.py"]