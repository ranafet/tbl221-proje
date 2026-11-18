FROM docker.io/library/python:3.13-slim

LABEL org.opencontainers.image.title="TBL221 monitor test suite" \
      org.opencontainers.image.description="Unit and smoke tests for the TBL221 Linux resource monitor" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.licenses="BSD-3-Clause"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    QT_QPA_PLATFORM=offscreen

WORKDIR /workspace

RUN python3 -m pip install --no-cache-dir --disable-pip-version-check "PySide6>=6.8,<7.0"

COPY --chown=65532:65532 . .

USER 65532:65532

RUN ["/bin/sh", "packaging/container/test.sh"]

CMD ["/bin/sh", "packaging/container/test.sh"]
