FROM python:3.12-bookworm
LABEL authors="Vic Ding"

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install /app/

ENTRYPOINT ["tail", "-f", "/dev/null"]