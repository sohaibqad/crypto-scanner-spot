import datetime as dt
import os
import requests
from .config import settings

BREVO_EMAIL_URL = "https://api.brevo.com/v3/smtp/email"

_TF_MS = {
    "3m": 3 * 60 * 1000,
    "5m": 5 * 60 * 1000,
    "15m": 15 * 60 * 1000,
    "30m": 30 * 60 * 1000,
    "1h": 60 * 60 * 1000,
    "2h": 2 * 60 * 60 * 1000,
    "3h": 3 * 60 * 60 * 1000,
    "4h": 4 * 60 * 60 * 1000,
}


def _utc(ms):
    return dt.datetime.fromtimestamp(ms / 1000, tz=dt.timezone.utc).isoformat(sep=" ")


def _confirmed_time_ms(tap_ms, execution_tf):
    """A pivot becomes confirmed after pivot_right subsequent candles close."""
    interval = _TF_MS[execution_tf.lower()]
    return tap_ms + (settings.pivot_right + 1) * interval


def text(s):
    z = s.zone
    tap_time_ms = s.tap.time
    return (
        "🚨 GOLDEN POCKET + RSI DIVERGENCE ALERT\n\n"
        f"Symbol: {s.symbol}\n"
        f"Execution TF: {s.execution_tf.upper()}\n"
        f"Direction: {s.direction.title()} Divergence\n\n"
        f"GP Source: {z.source_tf.upper()}\n"
        f"GP Strength: {z.strength:.0f}/10\n"
        f"GP Zone: {z.lower:.8f} – {z.upper:.8f}\n\n"
        f"Confirmed Tap: {s.tap_number}\n"
        f"Tap Price: {s.tap.price:.8f}\n"
        f"Tap Time (UTC): {_utc(tap_time_ms)}\n"
        f"Confirmed Time (UTC): {_utc(_confirmed_time_ms(tap_time_ms, s.execution_tf))}\n\n"
        "Price is interacting with the GP zone while the confirmed divergence sequence is active.\n\n"
        "Open TradingView and manually verify."
    )


def send(s):
    body = text(s)
    api_key = os.environ.get("BREVO_API_KEY", "").strip()
    recipient = os.environ.get("ALERT_TO", settings.alert_to).strip()
    sender = os.environ.get("ALERT_FROM", settings.alert_from).strip()

    if not api_key or not recipient or not sender:
        print("Brevo email not sent: set BREVO_API_KEY, ALERT_FROM, and ALERT_TO.")
        print("\n" + body + "\n")
        return False

    payload = {
        "sender": {"email": sender},
        "to": [{"email": recipient}],
        "subject": f"GP + {s.direction} divergence | {s.symbol} | {s.execution_tf.upper()}",
        "textContent": body,
    }
    response = requests.post(
        BREVO_EMAIL_URL,
        headers={
            "api-key": api_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=20,
    )
    response.raise_for_status()
    print(f"Brevo accepted alert email for {s.symbol} to {recipient}.")
    return True
