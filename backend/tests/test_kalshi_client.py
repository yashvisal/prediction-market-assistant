from types import SimpleNamespace

import pytest
import requests

from app.services.kalshi.client import KalshiClient


def _client() -> KalshiClient:
    client = object.__new__(KalshiClient)
    client._settings = SimpleNamespace(history_window_days=30)
    client._base_url = "https://demo-api.kalshi.co/trade-api/v2"
    client._base_path = "/trade-api/v2"
    client._read_rate_limiter = SimpleNamespace(acquire=lambda: None)
    return client


def _rate_limited_error() -> requests.HTTPError:
    response = requests.Response()
    response.status_code = 429
    response.url = "https://demo-api.kalshi.co/trade-api/v2/markets/TEST/candlesticks"
    return requests.HTTPError(response=response)


def test_get_market_bundle_falls_back_on_rate_limit(monkeypatch: pytest.MonkeyPatch):
    client = _client()
    market = {"ticker": "TEST-1"}

    def _raise_rate_limit(*, market, history_window_days):
        raise _rate_limited_error()

    monkeypatch.setattr(client, "get_market_candlesticks", _raise_rate_limit)

    bundle = client.get_market_bundle(market)

    assert bundle.raw_market == market
    assert bundle.candlesticks == []
    assert bundle.history_source == "rate_limited"


def test_get_market_bundle_reraises_non_rate_limit(monkeypatch: pytest.MonkeyPatch):
    client = _client()
    market = {"ticker": "TEST-1"}
    response = requests.Response()
    response.status_code = 500

    def _raise_server_error(*, market, history_window_days):
        raise requests.HTTPError(response=response)

    monkeypatch.setattr(client, "get_market_candlesticks", _raise_server_error)

    with pytest.raises(requests.HTTPError):
        client.get_market_bundle(market)


def test_request_retries_rate_limits(monkeypatch: pytest.MonkeyPatch):
    client = _client()
    calls: list[int] = []

    rate_limited = requests.Response()
    rate_limited.status_code = 429
    rate_limited.url = "https://demo-api.kalshi.co/trade-api/v2/markets"
    rate_limited.headers["Retry-After"] = "0"

    success = requests.Response()
    success.status_code = 200
    success._content = b'{"markets": []}'

    def _request(method, url, params, headers, timeout):
        calls.append(1)
        return rate_limited if len(calls) == 1 else success

    client._session = SimpleNamespace(request=_request)
    monkeypatch.setattr("app.services.kalshi.client.time.sleep", lambda _seconds: None)

    payload = client._request("GET", "/markets")

    assert payload == {"markets": []}
    assert len(calls) == 2
