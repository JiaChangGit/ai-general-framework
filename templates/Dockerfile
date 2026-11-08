# 僅供 doctor 示範。從框架根目錄建置，需保留相鄰的 Dockerfile.dockerignore；
# 移動或改名 Dockerfile 時，也要以相同檔名後接 .dockerignore 搬移忽略檔。
# 建置前仍須檢查所有允許進入 context 的檔案，不要把私人資料送給 builder。
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /workspace
COPY agf/*.py /workspace/agf/
COPY scripts/agf.py /workspace/scripts/agf.py
USER 10001:10001
CMD ["python", "scripts/agf.py", "doctor"]
