# 從 ai-general-framework 根目錄建置；先審閱 build context 與 dockerignore。
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /workspace
COPY . /workspace
USER 10001:10001
CMD ["python", "scripts/agf.py", "doctor"]
