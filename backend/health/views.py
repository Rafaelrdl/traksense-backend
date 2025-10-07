"""
Health Views - Endpoint básico de health check

Endpoint simples para monitoramento (Kubernetes, Docker, load balancers).

Response:
--------
{"status": "ok"}

USO:
---
Kubernetes liveness/readiness probe:
  livenessProbe:
    httpGet:
      path: /health
      port: 8000
    initialDelaySeconds: 10
    periodSeconds: 5

Docker healthcheck:
  HEALTHCHECK CMD curl -f http://localhost:8000/health || exit 1

TODO (Fase 2):
-------------
- Adicionar checks de DB (connection.cursor().execute('SELECT 1'))
- Adicionar checks de Redis (redis.ping())
- Adicionar checks de EMQX (HTTP API)
- Retornar detalhes (db_ok, redis_ok, emqx_ok)

Autor: TrakSense Team
Data: 2025-10-07
"""
from django.http import JsonResponse


def health(request):
    """Health check básico (HTTP 200 + JSON)."""
    return JsonResponse({"status": "ok"})
