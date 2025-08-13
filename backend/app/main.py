"""Minimal FastAPI application skeleton.

This pared‑down version only mounts the uploads router (see api/uploads.py) as
requested. Additional domain routers / business logic can be added later.

Run (locally):
    uvicorn app.main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import uploads, jobs, results, questions, exports, generate, embeddings, retrieval, auth
from fastapi import Depends
from .services.auth import require_role
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time
from .models import create_db
from collections import defaultdict, deque
import threading
import math, os
try:  # optional redis for distributed rate limiting
    import redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None

app = FastAPI(title="StudyForge Backend", version="0.0.1")

# Structured logging (loguru)
try:  # pragma: no cover
    from loguru import logger
    logger.add("storage/app.log", rotation="5 MB", retention="7 days", enqueue=True, serialize=False)
except Exception:  # fallback noop logger
    class _Dummy:
        def info(self,*a,**k): pass
        def warning(self,*a,**k): pass
        def error(self,*a,**k): pass
    logger = _Dummy()  # type: ignore

# Allow everything for quick local iteration – tighten later.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount only the uploads router under /api
app.include_router(auth.router, prefix="/api")
app.include_router(uploads.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")
app.include_router(results.router, prefix="/api")
app.include_router(questions.router, prefix="/api")
app.include_router(exports.router, prefix="/api")
app.include_router(generate.router, prefix="/api")
app.include_router(embeddings.router, prefix="/api")
app.include_router(retrieval.router, prefix="/api")

@app.on_event("startup")
def _startup():  # pragma: no cover - simple init
    create_db()


@app.get("/health")
async def health():
    return {"status": "ok"}


REQUEST_COUNT = Counter('sf_requests_total','Total HTTP requests',['method','path','status'])
REQUEST_LATENCY = Histogram('sf_request_latency_seconds','Request latency',['method','path'])

@app.middleware("http")
async def _metrics_mw(request, call_next):  # pragma: no cover simple metrics
    start = time.time()
    response = await call_next(request)
    path = request.url.path
    REQUEST_COUNT.labels(request.method, path, response.status_code).inc()
    REQUEST_LATENCY.labels(request.method, path).observe(time.time()-start)
    return response

# Basic in-memory rate limiter (per IP+path) – replace with Redis in prod
_RATE_LOCK = threading.Lock()
_WINDOW_SECONDS = 60
_MAX_REQUESTS = int(os.getenv('RATE_LIMIT_PER_MIN', '300'))
_REQUEST_LOG: dict[tuple[str,str], deque[float]] = defaultdict(lambda: deque())
_REDIS_RATE = None
_REDIS_URL = os.getenv('REDIS_URL')
if _REDIS_URL and redis:  # pragma: no cover - integration path
    try:
        _REDIS_RATE = redis.from_url(_REDIS_URL)
    except Exception:
        _REDIS_RATE = None

@app.middleware("http")
async def _rate_limit_mw(request, call_next):  # pragma: no cover - perf side-effect
    if _MAX_REQUESTS <= 0:
        return await call_next(request)
    ident = (request.client.host if request.client else 'anon', request.url.path)
    now = time.time()
    if _REDIS_RATE:
        key = f"ratelimit:{ident[0]}:{ident[1]}:{int(now//_WINDOW_SECONDS)}"
        try:
            pipe = _REDIS_RATE.pipeline()
            pipe.incr(key, 1)
            pipe.expire(key, _WINDOW_SECONDS)
            count, _ = pipe.execute()
            if int(count) > _MAX_REQUESTS:
                from fastapi.responses import JSONResponse
                return JSONResponse(status_code=429, content={"error":"rate_limited","retry_after": 60})
        except Exception:
            pass  # fallback to in-memory
    else:
        with _RATE_LOCK:
            dq = _REQUEST_LOG[ident]
            cutoff = now - _WINDOW_SECONDS
            while dq and dq[0] < cutoff:
                dq.popleft()
            if len(dq) >= _MAX_REQUESTS:
                from fastapi.responses import JSONResponse
                retry = math.ceil(dq[0] + _WINDOW_SECONDS - now)
                return JSONResponse(status_code=429, content={"error":"rate_limited","retry_after": retry})
            dq.append(now)
    return await call_next(request)

@app.middleware("http")
async def _logging_mw(request, call_next):  # pragma: no cover
    rid = request.headers.get('X-Request-ID') or __import__('uuid').uuid4().hex
    start = time.time()
    logger.info({"type":"request","id":rid,"method":request.method,"path":request.url.path})
    try:
        resp = await call_next(request)
        dur = (time.time()-start)*1000
        resp.headers['X-Request-ID'] = rid
        logger.info({"type":"response","id":rid,"status":resp.status_code,"ms":round(dur,2)})
        return resp
    except Exception as e:
        logger.error({"type":"error","id":rid,"error":str(e)})
        raise

@app.get('/metrics')
def metrics():  # plaintext Prometheus exposition
    data = generate_latest()
    from fastapi.responses import Response
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)
