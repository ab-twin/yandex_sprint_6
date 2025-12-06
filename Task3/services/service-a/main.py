# service-a/main.py
from fastapi import FastAPI
import requests

from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import ALWAYS_ON
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME

# 1. Сначала настройка OpenTelemetry
resource = Resource.create({
    SERVICE_NAME: "service-a"
})

# 2. Создаем провайдер с ресурсом
trace_provider = TracerProvider(
    resource=resource,
    sampler=ALWAYS_ON
)

# 3. Создаем экспортер
# Он автоматически возьмет OTEL_EXPORTER_OTLP_ENDPOINT из env переменных
exporter = OTLPSpanExporter()

# 4. Создаем и добавляем процессор
span_processor = BatchSpanProcessor(exporter)
trace_provider.add_span_processor(span_processor)

# 5. Устанавливаем глобальный провайдер
trace.set_tracer_provider(trace_provider)

# 6. ТОЛЬКО ПОСЛЕ этого создаем приложение
app = FastAPI()

# 7. Инструментируем приложение
FastAPIInstrumentor.instrument_app(app)
RequestsInstrumentor().instrument()

@app.get("/")
async def call_service_b():
    # Получаем tracer
    tracer = trace.get_tracer(__name__)
    
    # Создаем span
    with tracer.start_as_current_span("call-service-b") as span:
        # Добавляем атрибуты
        span.set_attribute("http.method", "GET")
        span.set_attribute("http.url", "http://service-b:8080/")
        
        try:
            # Делаем запрос
            resp = requests.get("http://service-b:8080/")
            resp.raise_for_status()
            
            span.set_attribute("http.status_code", resp.status_code)
            
            return {
                "service-a": "ok", 
                "from-service-b": resp.json()
            }
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.Status(trace.StatusCode.ERROR))
            return {"error": str(e)}