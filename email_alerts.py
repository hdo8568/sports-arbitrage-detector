#email_alerts.py

import os
import smtplib
from email.mime.text import MIMEText
from odds_calculator import OddsCalculator
import config  # loads .env if present

# Email settings come from the environment (or .env). See .env.example.
EMAIL_USER = os.environ.get("EMAIL_USER")
EMAIL_PASS = os.environ.get("EMAIL_PASS")
EMAIL_TO = os.environ.get("EMAIL_TO") or EMAIL_USER


def build_email_body(arbitrage_bets):
    body = ""

    for bet in arbitrage_bets:
        body += f"{bet['home_team']} vs {bet['away_team']}\n"
        body += f"Profit: {bet['profit_percentage']}%\n"
        body += f"Best Odds: {bet['best_odds']}\n"
        body += f"Bookmakers: {bet['bookmakers']}\n"

        bookmakers = bet['bookmakers']
        odds = bet['best_odds']
        for side in ["home", "away"]:
            dec = float(odds[side])
            american = OddsCalculator.decimal_to_american(dec)
            body += f"{bookmakers[side]}: {dec} (Decimal) / {american} (American)\n"

        # Suggested stakes so both sides pay out the same amount
        stakes = bet.get("suggested_stakes")
        if stakes:
            body += f"Suggested stakes (total ${stakes['total_stake']:.2f}):\n"
            body += f"  {bet['home_team']} at {bookmakers['home']}: ${stakes['home']:.2f}\n"
            body += f"  {bet['away_team']} at {bookmakers['away']}: ${stakes['away']:.2f}\n"
            body += f"  Payout either way: ${stakes['payout']:.2f} (profit ${stakes['profit']:.2f})\n"

        body += "-" * 30 + "\n"

    return body


def send_arbitrage_email(arbitrage_bets):
    if not arbitrage_bets:
        return  # Nothing to send

    if not EMAIL_USER or not EMAIL_PASS:
        print("❌ EMAIL_USER / EMAIL_PASS not set, skipping email. See .env.example.")
        return

    subject = f"🚨 {len(arbitrage_bets)} Arbitrage Opportunities Found"
    body = build_email_body(arbitrage_bets)

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_USER
    msg["To"] = EMAIL_TO

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)
            print("✅ Email sent successfully.")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
