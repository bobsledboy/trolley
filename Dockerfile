FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql supervisor \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY bot/ bot/
COPY db/ db/
COPY scraper/ scraper/

COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENV PGDATA=/var/lib/postgresql/data
ENV DATABASE_URL=postgresql://trolley:trolley@localhost:5432/trolley
VOLUME /var/lib/postgresql/data

ENTRYPOINT ["/entrypoint.sh"]
