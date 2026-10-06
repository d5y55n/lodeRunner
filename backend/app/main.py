from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.website.api import router as analysis_router
from app.website.config import PROJECT
from app.website.live_api import router as live_router
from app.website.symbols import router as symbols_router, registry
from app.website.manual import router as manual_router
from app.website.events import router as events_router

from app.api.market_routes import router as market_router

@asynccontextmanager
async def lifespan(app):
    yield
    from app.website import events
    if events._monitor is not None:
        events._monitor.stop()
    registry.close()
    from app.website.live_api import dashboard
    if dashboard.cache_info().currsize:
        dashboard().stop()
        dashboard.cache_clear()


app = FastAPI(title="SR Probability Trading Platform", version="0.1.0", lifespan=lifespan)
app.include_router(market_router)
app.include_router(analysis_router)
app.include_router(live_router)
app.include_router(symbols_router)
app.include_router(manual_router)
app.include_router(events_router)
app.mount('/assets', StaticFiles(directory=PROJECT/'frontend/analysis'), name='analysis-assets')


@app.get('/', include_in_schema=False)
def website():
    return FileResponse(PROJECT/'frontend/analysis/index.html')


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

