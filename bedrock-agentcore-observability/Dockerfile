FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

# All environment variables in one layer
ENV UV_SYSTEM_PYTHON=1 UV_COMPILE_BYTECODE=1 PYTHONUNBUFFERED=1 \
    AWS_REGION=us-east-1 AWS_DEFAULT_REGION=us-east-1 \
    DOCKER_CONTAINER=1 \
    # OTEL Configuration
    ADOT_IP="3.230.142.205" \
    OTEL_EXPORTER_OTLP_TRACES_ENDPOINT="http://3.230.142.205:4318/v1/traces" \
    OTEL_EXPORTER_OTLP_LOGS_ENDPOINT="http://3.230.142.205:4318/v1/logs" \
    OTEL_EXPORTER_OTLP_METRICS_ENDPOINT="http://3.230.142.205:4318/v1/metrics" \
    OTEL_EXPORTER_OTLP_PROTOCOL="http/protobuf" \
    OTEL_SERVICE_NAME="simple-agent-datadog-obs" \
    OTEL_RESOURCE_ATTRIBUTES="service.name=simple-agent-datadog-obs,service.version=1.0.0,deployment.environment=production" \
    OTEL_TRACES_EXPORTER="otlp" \
    OTEL_LOGS_EXPORTER="otlp" \
    OTEL_METRICS_EXPORTER="otlp" \
    # Datadog Configuration (API keys should be set at runtime)
    DD_SITE="datadoghq.com" \
    DD_LLMOBS_ML_APP="sample-amazon-cloudwatch-generative-ai-observability"



COPY requirements.txt requirements.txt




RUN uv pip install -r requirements.txt && \
    uv pip install aws-opentelemetry-distro>=0.10.1


EXPOSE 8080 8000

# Copy entire project

COPY . .


# Use the full module path

CMD ["opentelemetry-instrument", "python", "agent-with-OTLP.py"]
