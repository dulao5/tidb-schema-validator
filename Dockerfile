FROM python:3.11-slim

WORKDIR /app

COPY tidb-schema-validator.py /app/

# 可选：复制 test 目录或其它依赖文件
# COPY test/ /app/test/

RUN pip install --no-cache-dir argparse

ENTRYPOINT ["python", "/app/tidb-schema-validator.py"]