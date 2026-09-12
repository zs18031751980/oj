FROM public.ecr.aws/docker/library/python:3.13-slim-bookworm
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 APP_ENV=production
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && groupadd --gid 10001 letcoding \
    && useradd --uid 10001 --gid 10001 --no-create-home letcoding \
    && mkdir -p /var/lib/letcoding/uploads \
    && chown 10001:10001 /var/lib/letcoding/uploads
COPY . .
ENV UPLOAD_DIR=/var/lib/letcoding/uploads
USER 10001:10001
EXPOSE 8080
CMD ["gunicorn", "--config", "gunicorn.conf.py", "app_factory:create_app()"]
