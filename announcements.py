import requests
import pandas as pd
from datetime import datetime, time as dtime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import schedule
import time

# ========================
# CONFIG
# ========================
# Email setup
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "drsaritachopra@gmail.com"
SENDER_PASS = "syfu poue nntf ggfg"  # Gmail App Password
RECEIVER_EMAIL = "praveencdli@gmail.com"


FILTER_KEYWORDS = [
    "dividend", "bonus", "split", "buyback",
    "rights issue", "merger", "acquisition",
    "board meeting", "financial result"
]

last_sent = set()   # to avoid duplicate alerts

# ========================
# FETCH NSE Announcements
# ========================
def fetch_nse_announcements():
    try:
        url = "https://www.nseindia.com/api/corporate-announcements"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=15)
        data = r.json()
    except Exception as e:
        print("❌ NSE fetch error:", e)
        return []

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
    try:
        url = "https://api.bseindia.com/BseIndiaAPI/api/AnnGetData/w"
        params = {"strCat": "Company_Ann", "strPrevDate": "", "strScrip": "", "strSearch": ""}
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, params=params, headers=headers, timeout=15)
        data = r.json()
    except Exception as e:
        print("❌ BSE fetch error:", e)
        return []

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
def send_email_alert(announcements, subject_note=""):
    if not announcements:
        return

    body = ""
    for ann in announcements:
        body += f"[{ann['exchange']}] {ann['company']} ({ann['date']}): {ann['announcement']}\n\n"

    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL
    msg["Subject"] = f"Corporate Announcements Alert {subject_note} - {datetime.now().strftime('%d-%m-%Y')}"

    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASS)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())

    print("📩 Email sent:", subject_note)

# ========================
# JOB FUNCTIONS
# ========================
def daily_job():
    print("⏰ Running 7AM summary check at", datetime.now().strftime("%H:%M:%S"))
    nse_data = fetch_nse_announcements()
    bse_data = fetch_bse_announcements()
    all_announcements = nse_data + bse_data

    if all_announcements:
        df = pd.DataFrame(all_announcements)
        df.to_csv("announcements_today.csv", index=False)
        send_email_alert(all_announcements, subject_note="(Daily Summary)")
    else:
        print("No important announcements found today.")

def realtime_job():
    global last_sent
    now = datetime.now().time()
    market_start = dtime(9, 15)
    market_end = dtime(15, 30)

    if not (market_start <= now <= market_end):
        return  # skip outside market hours

    print("🔄 Checking live announcements at", datetime.now().strftime("%H:%M:%S"))
    nse_data = fetch_nse_announcements()
    bse_data = fetch_bse_announcements()
    all_announcements = nse_data + bse_data

    # Deduplicate alerts (send only new ones)
    new_alerts = []
    for ann in all_announcements:
        key = (ann["exchange"], ann["company"], ann["date"], ann["announcement"])
        if key not in last_sent:
            last_sent.add(key)
            new_alerts.append(ann)

    if new_alerts:
        send_email_alert(new_alerts, subject_note="(Live Update)")

# ========================
# MAIN
# ========================
def main():
    # Schedule daily summary at 7AM
    schedule.every().day.at("07:00").do(daily_job)

    # Schedule real-time every 5 minutes
    schedule.every(5).minutes.do(realtime_job)

    print("✅ Scheduler started: 7AM daily summary + live market alerts (every 5 min)")
    while True:
        schedule.run_pending()
        time.sleep(30)

if __name__ == "__main__":
    main()

