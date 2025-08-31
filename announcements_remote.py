# announcements_remote.py
# This file is meant to be placed in your GitHub repo (Raw URL).
# It provides a simple API: get_announcements(filter_keywords=None)
# Return: list of dicts {exchange, company, date, announcement}

import requests

USER_AGENT = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def _nse_fetch():
    out = []
    try:
        s = requests.Session()
        s.get("https://www.nseindia.com", headers=USER_AGENT, timeout=10)  # warmup cookies
        url = "https://www.nseindia.com/api/corporate-announcements?index=equities"
        r = s.get(url, headers=USER_AGENT, timeout=12)
        r.raise_for_status()
        payload = r.json()
        rows = payload.get("rows") or payload.get("data") or []
        for item in rows:
            # pick a text field robustly
            text = (item.get("subject") or item.get("headline") or item.get("sm_desc") or item.get("sm_description") or "").strip()
            sym  = (item.get("symbol") or item.get("scrip") or "").strip()
            dt   = (item.get("dissemDT") or item.get("dt") or item.get("sm_date") or "")
            if text:
                out.append({"exchange":"NSE", "company": sym, "date": dt, "announcement": text})
    except Exception as e:
        # return empty list on error; service will log
        return []
    return out

def _bse_fetch():
    out = []
    try:
        url = "https://api.bseindia.com/BseIndiaAPI/api/AnnGetData/w"
        params = {"strCat": "Company_Ann", "strPrevDate": "", "strScrip": "", "strSearch": ""}
        r = requests.get(url, params=params, headers=USER_AGENT, timeout=12)
        r.raise_for_status()
        payload = r.json()
        table = payload.get("Table") or []
        for item in table:
            txt = (item.get("HEADING") or item.get("NEWS_SUB") or "").strip()
            scrip = item.get("SCRIP_CD") or ""
            dt = item.get("NEWS_DT") or ""
            if txt:
                out.append({"exchange":"BSE", "company": scrip, "date": dt, "announcement": txt})
    except Exception:
        return []
    return out

def get_announcements(filter_keywords=None):
    """
    Return list of announcement dicts filtered by keywords (case-insensitive).
    filter_keywords: list of keywords; if None, a default set is used.
    """
    if filter_keywords is None:
        filter_keywords = [
            "dividend", "bonus", "split", "buyback",
            "rights", "merger", "demerger", "record date",
            "board meeting", "results", "profit", "allotment"
        ]
    fk = [k.lower() for k in filter_keywords]

    results = _nse_fetch() + _bse_fetch()
    filtered = []
    for r in results:
        txt = (r.get("announcement") or "").lower()
        if any(k in txt for k in fk):
            filtered.append(r)
    return filtered

# Optional quick test function when run as script:
if __name__ == "__main__":
    anns = get_announcements()
    print("Found:", len(anns))
    for a in anns[:10]:
        print(a)
