from fastapi import APIRouter, Depends

from app.market.data_service import HistoricalMarketDataService
from app.market.models import BinanceKlinesQuery, KlineDownloadResult


router = APIRouter(prefix="/market", tags=["market"])


def get_market_data_service() -> HistoricalMarketDataService:
    return HistoricalMarketDataService()


@router.get("/binance/klines", response_model=KlineDownloadResult)
def get_binance_klines(
    query: BinanceKlinesQuery = Depends(),
    service: HistoricalMarketDataService = Depends(get_market_data_service),
) -> KlineDownloadResult:
    return service.download_klines(query)

