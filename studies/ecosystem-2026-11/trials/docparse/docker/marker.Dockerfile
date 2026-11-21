FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu marker-pdf && pip list 2>/dev/null | grep -iE "^marker|^surya|^torch " > /versions.txt
RUN python -c "from marker.models import create_model_dict; create_model_dict()"
# Marker 2.2.0 also downloads a font on first use; fetch it at build time so runs work offline.
RUN python -c "from marker.util import download_font; download_font()"
