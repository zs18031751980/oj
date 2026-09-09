# Keep Debian Bookworm: it provides the Java 17 toolchain required by the judge.
FROM public.ecr.aws/docker/library/python:3.13-slim-bookworm

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        g++ \
        nodejs \
        openjdk-17-jdk \
        golang-go \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN python3 -m pip install --no-cache-dir -r requirements.txt

COPY . .

ENV HOST=0.0.0.0
EXPOSE 8080

CMD ["python3", "main.py"]
