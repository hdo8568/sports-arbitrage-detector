import smtplib
from email.mime.text import MIMEText

# 🔒 Placeholder values – replace with real ones later
EMAIL_USER = "your_email@gmail.com"
EMAIL_PASS = "your_app_password"
EMAIL_TO = "recipient_email@gmail.com"

def send_arbitrage_email(arbitrage_bets):
    if not arbitrage_bets:
        return  # Nothing to send

    subject = f"🚨 {len(arbitrage_bets)} Arbitrage Opportunities Found"
    body = ""

    for bet in arbitrage_bets:
        body += f"{bet['home_team']} vs {bet['away_team']}\n"
        body += f"Profit: {bet['profit_percentage']}%\n"
        body += f"Best Odds: {bet['best_odds']}\n"
        body += f"Bookmakers: {bet['bookmakers']}\n"
        body += "-" * 30 + "\n"

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
