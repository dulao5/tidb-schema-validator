FROM python:3.11-slim

WORKDIR /data

COPY tidb-schema-validator.py /app/


RUN pip install --no-cache-dir argparse

ENTRYPOINT ["python", "/app/tidb-schema-validator.py"]