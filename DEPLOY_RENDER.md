# Deploy the scanner 24/7 on Render

This package is configured as a persistent Docker background worker, not a Vercel serverless function. It polls the market-cap universe and Binance USDT Spot pairs continuously. The Render worker plan is paid; select an always-on worker plan.

## Before deployment
- Keep `.env` and Brevo API key out of GitHub. The `.gitignore` excludes `.env`.
- This app sends mail through the Brevo REST API over HTTPS. Use a Brevo API key and a sender address verified in your Brevo account. Never paste the API key into source control or ChatGPT.
- The receiver is preset to `spectrifier@gmail.com`. `ALERT_FROM` must be a verified sender address in Brevo.

## Steps
1. Extract this ZIP to a normal folder.
2. Create a **private** GitHub repository and upload the extracted project files (including `render.yaml`, `Dockerfile`, `backend/`, and `tests/`). Do not upload `.env` or any password. GitHub Desktop is the easiest way to publish a local folder.
3. In Render, choose **New + → Blueprint** and connect that GitHub repository. Render should detect `render.yaml` and create a background worker.
4. In the worker's Environment settings, set `BREVO_API_KEY` to your Brevo API key and `ALERT_FROM` to a sender address verified in Brevo. Keep `ALERT_TO` as `spectrifier@gmail.com`.
5. Deploy, then open **Logs**. Confirm you see `V8 LIVE SPOT SCANNER — TOP 30 MARKET-CAP COINS`, `Email recipient: spectrifier@gmail.com`, and `Monitoring:` with symbols.
6. Leave the worker running. It will continue after your PC is off, as long as the Render service remains active and paid.

## Important behavior
- The scan loop polls every 60 seconds, but signals are based on closed candles and confirmed pivots; alerts are not guaranteed exactly 60 seconds after a price touch.
- The current code keeps the `seen` alert-deduplication set in memory. It is reset if the worker restarts.
- The worker depends on CoinGecko and Binance API availability/rate limits.
- This is an alert-only scanner; it does not place trades.
