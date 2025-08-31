import requests
import pandas as pd
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ========================
# CONFIG
# ========================
# Email setup
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

SENDER_EMAIL = "drsaritachopra@gmail.com"
SENDER_PASS = "syfu poue nntf ggfg"  # Gmail App Password
RECEIVER_EMAIL = "praveencdli@gmail.com"

# Keywords to filter corporate actions
FILTER_KEYWORDS = [
    "dividend", "bonus", "split", "buyback",
    "rights issue", "merger", "acquisition",
    "board meeting", "financial result"
]

# ========================
# FETCH NSE Announcements
# ========================
def fetch_nse_announcements():
    url = "https://www.nseindia.com/api/corporate-announcements"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=15)
    data = r.json()

    announcements = []
    for item in data.get("data", []):
        text = item.get("sm_description", "").lower()
        if any(keyword in text for keyword in FILTER_KEYWORDS):
            announcements.append({
                "exchange": "NSE",
                "company": item.get("symbol"),
                "date": item.get("sm_date"),
                "announcement": item.get("sm_description")
            })
    return announcements

# ========================
# FETCH BSE Announcements
# ========================
def fetch_bse_announcements():
    url = "https://api.bseindia.com/BseIndiaAPI/api/AnnGetData/w"
    params = {"strCat": "Company_Ann", "strPrevDate": "", "strScrip": "", "strSearch": ""}
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, params=params, headers=headers, timeout=15)
    data = r.json()

    announcements = []
    for item in data.get("Table", []):
        text = item.get("HEADING", "").lower()
        if any(keyword in text for keyword in FILTER_KEYWORDS):
            announcements.append({
                "exchange": "BSE",
                "company": item.get("SCRIP_CD"),
                "date": item.get("NEWS_DT"),
                "announcement": item.get("HEADING")
            })
    return announcements

# ========================
# EMAIL ALERT
# ========================
def send_email_alert(announcements):
    if not announcements:
        return

    body = ""
    for ann in announcements:
        body += f"[{ann['exchange']}] {ann['company']} ({ann['date']}): {ann['announcement']}\n\n"

    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL
    msg["Subject"] = f"Corporate Announcements Alert - {datetime.now().strftime('%d-%m-%Y')}"

    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASS)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())

    print("📩 Email sent with latest announcements!")

# ========================
# MAIN
# ========================
def main():
    nse_data = fetch_nse_announcements()
    bse_data = fetch_bse_announcements()

    all_announcements = nse_data + bse_data

    if all_announcements:
        df = pd.DataFrame(all_announcements)
        df.to_csv("announcements_today.csv", index=False)
