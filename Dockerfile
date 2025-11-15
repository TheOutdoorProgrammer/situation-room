FROM python:bookworm

RUN apt-get update && apt-get install -y supervisor
RUN mkdir -p /var/log/supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Copy requirements and install dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

COPY . /app/

WORKDIR /app

# OpenTelemetry environment configuration
# Override these at runtime to configure OTLP exporter
ENV OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
ENV OTEL_EXPORTER_OTLP_PROTOCOL=http
ENV OTEL_TRACES_ENABLED=true
ENV OTEL_CONSOLE_EXPORTER=false
ENV ENVIRONMENT=production

ENTRYPOINT ["/usr/bin/supervisord"]