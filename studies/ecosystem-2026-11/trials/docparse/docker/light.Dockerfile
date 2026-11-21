FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends poppler-utils && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir pymupdf4llm "markitdown[pdf]" && pip list 2>/dev/null | grep -iE "pymupdf|markitdown|pdfminer" > /versions.txt
