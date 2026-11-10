from unittest.mock import Mock, patch

from backend.binance_data import BinanceClient, BINANCE_HEADERS
from backend.config import settings
from backend.models import Candle, Signal, Tap, Zone
from backend import alerts


def test_binance_client_uses_spot_api_and_browser_headers():
    client = BinanceClient()
    response = Mock()
    response.json.return_value = [[1700000000000, "1", "3", "0.5", "2", "10"]]
    with patch.object(client.s, "get", return_value=response) as get:
        candles = client.klines("BTCUSDT", "1m", 1)
    assert client.base == "https://api.binance.com"
    assert candles == [Candle(1700000000000, 1.0, 3.0, 0.5, 2.0, 10.0)]
    args, kwargs = get.call_args
    assert args[0] == "https://api.binance.com/api/v3/klines"
    assert kwargs["headers"] == BINANCE_HEADERS
    assert kwargs["params"]["symbol"] == "BTCUSDT"


def test_exchange_info_filters_usdt_spot_pairs():
    client = BinanceClient()
    with patch.object(client, "get", return_value={"symbols": [
        {"symbol": "BTCUSDT", "baseAsset": "BTC", "quoteAsset": "USDT", "status": "TRADING", "isSpotTradingAllowed": True},
        {"symbol": "ETHUSDT", "baseAsset": "ETH", "quoteAsset": "USDT", "status": "TRADING", "isSpotTradingAllowed": False},
        {"symbol": "SOLBTC", "baseAsset": "SOL", "quoteAsset": "BTC", "status": "TRADING", "isSpotTradingAllowed": True},
    ]}) as get:
        pairs = client._tradable_usdt_spot_pairs()
    get.assert_called_once_with("/api/v3/exchangeInfo")
    assert pairs == {"BTCUSDT": "BTC"}


def test_polling_is_fixed_at_60_seconds():
    assert settings.poll_seconds == 60


def test_alert_uses_brevo_rest_api(monkeypatch):
    monkeypatch.setenv("BREVO_API_KEY", "test-api-key")
    monkeypatch.setenv("ALERT_FROM", "verified@example.com")
    monkeypatch.setenv("ALERT_TO", "recipient@example.com")
    signal = Signal(
        symbol="BTCUSDT", execution_tf="3m", direction="bullish",
        zone=Zone("1m", 101.0, 99.0, 8.0, 1, 0, 0),
        tap_number=3, tap=Tap(2, 1700000000000, 100.0, 35.0),
    )
    response = Mock()
    with patch.object(alerts.requests, "post", return_value=response) as post:
        assert alerts.send(signal) is True
    post.assert_called_once()
    args, kwargs = post.call_args
    assert args[0] == "https://api.brevo.com/v3/smtp/email"
    assert kwargs["headers"]["api-key"] == "test-api-key"
    assert kwargs["json"]["to"] == [{"email": "recipient@example.com"}]
    assert kwargs["json"]["sender"] == {"email": "verified@example.com"}
    response.raise_for_status.assert_called_once()
