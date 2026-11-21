FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends universal-ctags cscope global cflow clang make && rm -rf /var/lib/apt/lists/* \
 && (ctags --version | head -1; cscope -V 2>&1; global --version | head -1; cflow --version | head -1; clang --version | head -1) > /versions.txt
