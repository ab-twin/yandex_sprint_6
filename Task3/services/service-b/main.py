# service-b/main.py
from fastapi import FastAPI

from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import ALWAYS_ON
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME

# 1. Настройка OpenTelemetry
resource = Resource.create({
    SERVICE_NAME: "service-b"
})

trace_provider = TracerProvider(
    resource=resource,
    sampler=ALWAYS_ON
)

exporter = OTLPSpanExporter()
span_processor = BatchSpanProcessor(exporter)
trace_provider.add_span_processor(span_processor)
trace.set_tracer_provider(trace_provider)

# 2. Создание приложения
app = FastAPI()

# 3. Инструментация
FastAPIInstrumentor.instrument_app(app)

@app.get("/")
async def root():
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("service-b-root"):
        return {"message": "Hello from Service B!"}