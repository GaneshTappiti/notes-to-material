## Monitoring & Telemetry

### Prometheus Metrics
Backend exposes `/metrics` with request counters & latency. Example scrape config:
```yaml
- job_name: studyforge-backend
  static_configs:
    - targets: ['backend:8000']
```

### Sentry Integration (suggested)
Add dependency `sentry-sdk[fastapi]` then:
```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
sentry_sdk.init(dsn=os.getenv('SENTRY_DSN'), integrations=[FastApiIntegration()])
```

### Grafana Dashboard Skeleton
Create a dashboard with panels:
1. `rate(sf_requests_total[5m])` by path
2. `histogram_quantile(0.95, sum(rate(sf_request_latency_seconds_bucket[5m])) by (le, path))`
3. Error rate: `sum(rate(sf_requests_total{status!="200"}[5m])) / sum(rate(sf_requests_total[5m]))`

### Cost & Budgets
Implement a simple rate limiter for Gemini calls via token bucket (future). Track counts in Redis or in-memory and export gauge `sf_gemini_calls_total`.

Daily budget script (pseudo):
```bash
#!/usr/bin/env bash
limit=${DAILY_CALL_LIMIT:-1000}
calls=$(curl -s http://backend:8000/metrics | grep sf_gemini_calls_total | awk '{print $2}')
if [ "$calls" -gt "$limit" ]; then
  echo "Daily Gemini call budget exceeded: $calls > $limit" | mail -s "Budget Alert" team@example.com
fi
```

### Environment Variables Reference
| Name | Purpose |
|------|---------|
| JWT_SECRET | Sign JWT tokens |
| JWT_EXPIRE_SECONDS | Token lifetime |
| GOOGLE_API_KEY | Gemini API key |
| DATABASE_URL | External DB override |
| ECHO_SQL | Set to 1 for SQL echo |
| SENTRY_DSN | Sentry DSN |
| DAILY_CALL_LIMIT | Optional call budget |
