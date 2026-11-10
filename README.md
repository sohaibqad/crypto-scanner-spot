# Crypto Scanner V8

Read-only Binance Spot scanner implementing the agreed GP + RSI divergence rules.

GP sources:
- 12M, 6M, 3M, 1M: all qualifying strengths
- 1W, 1D: 10/10 only
- no 4H GP

Execution/divergence:
3M, 5M, 15M, 30M, 1H, 2H, 3H, 4H.
No 1M divergence.

Divergence requires 3 confirmed taps before an alert. Tap 3 or any later tap can alert when it interacts with a qualifying GP. Bearish price must make successive higher/equal highs while RSI makes lower highs; bullish is the mirror. GP interaction allows 0.4% penetration on the appropriate side.

The GP math follows the supplied Pine source: ADR10 is a 10-period SMA of source candle range; midpoint is low + range*0.559; fixed zone height is ADR10*3%/2; minimum candle size is 60% ADR10; strength is 4-10; overlapping zones are merged.

Install:
python -m pip install -r backend\requirements.txt

Full replay:
python -m backend.replay --symbol SOLUSDT --limit 1000

Live scanner — automatically monitors all eight execution timeframes:
python -m backend.scanner

Tests:
python -m pytest -q

This release is read-only and does not place trades.


## Important: 3H execution timeframe
Binance Spot does not accept `3h` as a native kline interval. The scanner therefore constructs 3-hour candles from 1-hour Binance candles internally. You still see and scan `3H` as an execution timeframe; you do not need to change the strategy.

### Alert timestamp format
Every live alert includes `Tap Time (UTC)` and `Confirmed Time (UTC)` using an explicit UTC ISO-style timestamp with `+00:00`. The confirmation is the tap at which the minimum 3-tap divergence requirement becomes satisfied.

### GP source-strength rule (final)
- 1M, 3M, 6M, 12M: **all qualifying GP zones are included; GP strength does not filter them out.**
- 1W: **10/10 only.**
- 1D: **10/10 only.**
- There is no 4H GP source.
The calculated strength remains visible as metadata in alerts/output, but monthly GP eligibility does not depend on it.


## Golden Pocket implementation update

The GP engine now treats the user's manually selected TradingView source
timeframes as separate machine-readable buckets:

- 1M: native Binance monthly candles
- 3M: calendar-aligned aggregation of 1M candles
- 6M: calendar-aligned aggregation of 1M candles
- 12M: calendar-aligned aggregation of 1M candles
- 1W: native weekly candles, 10/10 only
- 1D: native daily candles, 10/10 only

The current, still-forming 3M/6M/12M candle is retained. Historical
higher-timeframe groups must be complete. This is important for live scanning:
in August, for example, the current 12M TradingView candle is not complete yet,
but it still exists and must be represented.

The GP engine does not use the display colors from the screenshots. The
timeframe identity is carried as `Zone.source_tf`.


## Live top-30 universe and email

The live scanner now refreshes the universe every polling cycle from CoinGecko's
market-cap ranking, then intersects that ranking with Binance USDT Spot pairs. Stablecoins are excluded. The resulting top 30 are scanned in
parallel across all eight execution timeframes.

Email alerts use the Brevo REST API over HTTPS:
- Endpoint: https://api.brevo.com/v3/smtp/email
- Required environment variables: `BREVO_API_KEY`, `ALERT_FROM`, and `ALERT_TO`
- `ALERT_FROM` must be a sender address verified in your Brevo account.
- `ALERT_TO` defaults to `spectrifier@gmail.com`.

Example `.env`:
BREVO_API_KEY=your-brevo-api-key
ALERT_FROM=your-verified-sender@example.com
ALERT_TO=spectrifier@gmail.com

The scanner polls every 60 seconds. Keep API keys and `.env` out of GitHub.

The scanner sends when the existing strategy produces a new qualifying
3-tap-or-later signal. The live loop analyzes only closed execution candles,
so pivot confirmation occurs after the configured pivot-right bars. The email
contains both Tap Time (UTC) and Confirmed Time (UTC).

## 24/7 VPS deployment

This release includes a Dockerfile and a `scanner` service in docker-compose.
On a Linux VPS:

1. Copy the project to the VPS.
2. Create `.env` with your Brevo API key and verified sender address.
3. Run `docker compose up -d --build`.
4. Check `docker compose logs -f scanner`.

The scanner container uses `restart: unless-stopped`, so it restarts after a
process crash and after a VPS reboot.


## Deployment
See `DEPLOY_RENDER.md` for 24/7 Render background-worker deployment.


## Binance Spot and Brevo updates

- Market data is fetched from Binance Spot (`https://api.binance.com`) using `/api/v3/exchangeInfo` and `/api/v3/klines`.
- Binance API requests include a browser-style User-Agent and `Accept: application/json` headers.
- The live scanner polls every 60 seconds.
- Alert email is sent through Brevo's HTTPS API (`https://api.brevo.com/v3/smtp/email`). Configure `BREVO_API_KEY`, `ALERT_FROM` (a verified Brevo sender), and `ALERT_TO` in your environment. Never commit API keys or `.env` files.
- The top-30 market-cap universe now requires a matching Binance USDT Spot pair; stablecoins remain excluded.
