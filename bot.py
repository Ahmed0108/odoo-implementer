"""
Odoo Jobs Telegram Bot — Redis Edition
========================================
بيحفظ الوظائف المشوفة في Redis عشان متتكررش حتى لو البوت اتعمل restart
"""
 
import os
import time
import hashlib
import logging
import requests
from datetime import datetime
from bs4 import BeautifulSoup
import feedparser
import redis
 
# ─── إعدادات ─────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN          = os.environ.get("TELEGRAM_TOKEN", "8341918328:AAEzbSoZ9gXR4kQowFJnaxHZp-DKG8YBbTU")
TELEGRAM_CHAT_ID        = os.environ.get("TELEGRAM_CHAT_ID", "1275130214")
CHECK_INTERVAL_MINUTES  = int(os.environ.get("CHECK_INTERVAL", "15"))
REDIS_URL               = os.environ.get("REDIS_URL", "redis://localhost:6379")
 
SEARCH_KEYWORDS = [
    "odoo implementer",
    "odoo implementation",
    "fresh odoo",
    "odoo consultant",
    "odoo developer",
    "odoo erp",
    "odoo functional",
    "odoo technical",
    "odoo specialist",
    "odoo analyst",
    "odoo support",
    "odoo trainer",
    "odoo engineer",
]
 
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    handlers=[logging.StreamHandler()],
)
log = logging.getLogger(__name__)
 
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}
 
# ─── Redis ────────────────────────────────────────────────────────────────────
 
def get_redis():
    try:
        r = redis.from_url(REDIS_URL, decode_responses=True, socket_timeout=5)
        r.ping()
        log.info("✅ Redis متصل")
        return r
    except Exception as e:
        log.error(f"❌ Redis فشل: {e}")
        return None
 
def is_seen(r, jid: str) -> bool:
    if r is None:
        return False
    try:
        return r.sismember("seen_jobs", jid)
    except:
        return False
 
def mark_seen(r, jid: str):
    if r is None:
        return
    try:
        r.sadd("seen_jobs", jid)
        # نحتفظ بالوظائف لمدة 30 يوم بس
        r.expire("seen_jobs", 60 * 60 * 24 * 30)
    except:
        pass
 
# ─── أدوات مساعدة ─────────────────────────────────────────────────────────────
 
def job_id(title: str, url: str) -> str:
    return hashlib.md5(f"{title.lower().strip()}{url.strip()}".encode()).hexdigest()
 
def is_relevant(title: str) -> bool:
    return any(kw in title.lower() for kw in SEARCH_KEYWORDS)
 
def safe_get(url: str, timeout=20, extra_headers=None):
    h = {**HEADERS, **(extra_headers or {})}
    try:
        r = requests.get(url, headers=h, timeout=timeout)
        r.raise_for_status()
        return r
    except Exception as e:
        log.warning(f"GET failed [{url[:60]}] → {e}")
        return None
 
def make_job(title, company, location, url, source):
    return {"title": title, "company": company or "غير محدد",
            "location": location or "غير محدد", "url": url, "source": source}
 
# ─── إرسال تيليجرام ───────────────────────────────────────────────────────────
 
def send_telegram(text: str):
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": text,
                  "parse_mode": "HTML", "disable_web_page_preview": False},
            timeout=15,
        )
        r.raise_for_status()
        log.info("✅ رسالة اتبعتت")
    except Exception as e:
        log.error(f"Telegram error: {e}")
 
def fmt_msg(j):
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    return (
        f"🟢 <b>وظيفة Odoo جديدة!</b>\n\n"
        f"💼 <b>{j['title']}</b>\n"
        f"🏢 {j['company']}\n"
        f"📍 {j['location']}\n"
        f"🌐 {j['source']}\n"
        f"🕐 {now}\n\n"
        f"🔗 <a href='{j['url']}'>اضغط هنا للتقديم</a>"
    )
 
# ══════════════════════════════════════════════════════════════════════════════
#  Scrapers
# ══════════════════════════════════════════════════════════════════════════════
 
def scrape_wuzzuf():
    jobs = []
    for q in ["odoo+implementer", "odoo+implementation", "odoo+consultant", "odoo+developer"]:
        r = safe_get(f"https://wuzzuf.net/search/jobs/?q={q}&a=hpb")
        if not r: continue
        for card in BeautifulSoup(r.text, "html.parser").select("div[data-id]"):
            t = card.select_one("h2 a")
            if not t: continue
            title = t.get_text(strip=True)
            href  = t.get("href","")
            link  = ("https://wuzzuf.net"+href) if href.startswith("/") else href
            co    = card.select_one("a[data-id='company-name']")
            loc   = card.select_one("span[class*='location']")
            if is_relevant(title):
                jobs.append(make_job(title, co.get_text(strip=True) if co else "",
                                     loc.get_text(strip=True) if loc else "Egypt", link, "Wuzzuf 🇪🇬"))
    return jobs
 
def scrape_bayt():
    jobs = []
    for url in [
        "https://www.bayt.com/en/egypt/jobs/odoo-implementer-jobs/",
        "https://www.bayt.com/en/saudi-arabia/jobs/odoo-implementer-jobs/",
        "https://www.bayt.com/en/uae/jobs/odoo-implementer-jobs/",
        "https://www.bayt.com/en/international/jobs/odoo-implementer-jobs/",
        "https://www.bayt.com/en/international/jobs/odoo-consultant-jobs/",
    ]:
        r = safe_get(url)
        if not r: continue
        for item in BeautifulSoup(r.text, "html.parser").select("li[data-job-id]"):
            t = item.select_one("h2 a")
            if not t: continue
            title = t.get_text(strip=True)
            co    = item.select_one("span[itemprop='name']")
            loc   = item.select_one("span.jb-loc")
            if is_relevant(title):
                jobs.append(make_job(title,
                    co.get_text(strip=True) if co else "",
                    loc.get_text(strip=True) if loc else "",
                    "https://www.bayt.com" + t.get("href",""), "Bayt 🌍"))
    return jobs
 
def scrape_naukrigulf():
    jobs = []
    for url in [
        "https://www.naukrigulf.com/odoo-implementer-jobs",
        "https://www.naukrigulf.com/odoo-implementation-consultant-jobs",
        "https://www.naukrigulf.com/odoo-developer-jobs",
    ]:
        r = safe_get(url)
        if not r: continue
        for card in BeautifulSoup(r.text, "html.parser").select("div.ni-job-tuple"):
            t = card.select_one("a.desig-txt")
            if not t: continue
            title = t.get_text(strip=True)
            href  = t.get("href","")
            link  = href if href.startswith("http") else "https://www.naukrigulf.com"+href
            co    = card.select_one("a.org-name-txt")
            loc   = card.select_one("span.ni-job-loc")
            if is_relevant(title):
                jobs.append(make_job(title,
                    co.get_text(strip=True) if co else "",
                    loc.get_text(strip=True) if loc else "", link, "NaukriGulf 🇦🇪"))
    return jobs
 
def scrape_gulftalent():
    jobs = []
    for url in [
        "https://www.gulftalent.com/jobs/odoo-implementer-jobs",
        "https://www.gulftalent.com/jobs/odoo-consultant-jobs",
    ]:
        r = safe_get(url)
        if not r: continue
        for card in BeautifulSoup(r.text, "html.parser").select("div.job_listing"):
            t = card.select_one("h3 a")
            if not t: continue
            title = t.get_text(strip=True)
            href  = t.get("href","")
            link  = href if href.startswith("http") else "https://www.gulftalent.com"+href
            co    = card.select_one("div.company_name")
            loc   = card.select_one("div.location")
            if is_relevant(title):
                jobs.append(make_job(title,
                    co.get_text(strip=True) if co else "",
                    loc.get_text(strip=True) if loc else "", link, "GulfTalent 🇦🇪"))
    return jobs
 
def scrape_forasna():
    jobs = []
    r = safe_get("https://www.forasna.com/jobs/search?q=odoo")
    if not r: return jobs
    for card in BeautifulSoup(r.text, "html.parser").select("div.job-card, article.job"):
        t = card.select_one("h2 a, h3 a")
        if not t: continue
        title = t.get_text(strip=True)
        href  = t.get("href","")
        link  = href if href.startswith("http") else "https://www.forasna.com"+href
        if is_relevant(title):
            jobs.append(make_job(title, "", "", link, "Forasna 🇪🇬"))
    return jobs
 
def scrape_akhtaboot():
    jobs = []
    r = safe_get("https://www.akhtaboot.com/en/search-jobs?keyword=odoo+implementer&order_by=newest")
    if not r: return jobs
    for card in BeautifulSoup(r.text, "html.parser").select("div.job_list_item"):
        t = card.select_one("h2 a")
        if not t: continue
        title = t.get_text(strip=True)
        href  = t.get("href","")
        link  = href if href.startswith("http") else "https://www.akhtaboot.com"+href
        co    = card.select_one("span.company_name")
        loc   = card.select_one("span.location_name")
        if is_relevant(title):
            jobs.append(make_job(title,
                co.get_text(strip=True) if co else "",
                loc.get_text(strip=True) if loc else "", link, "Akhtaboot 🇯🇴"))
    return jobs
 
def scrape_indeed():
    jobs = []
    for feed_url in [
        "https://www.indeed.com/rss?q=odoo+implementer&sort=date",
        "https://www.indeed.com/rss?q=odoo+implementation+consultant&sort=date",
        "https://eg.indeed.com/rss?q=odoo+implementer&sort=date",
        "https://sa.indeed.com/rss?q=odoo+implementer&sort=date",
        "https://ae.indeed.com/rss?q=odoo+implementer&sort=date",
    ]:
        try:
            for e in feedparser.parse(feed_url).entries:
                title = e.get("title","")
                if is_relevant(title):
                    jobs.append(make_job(title,"","",e.get("link",""),"Indeed 🌍"))
        except Exception as ex:
            log.warning(f"Indeed: {ex}")
    return jobs
 
def scrape_linkedin():
    jobs = []
    for q in ["odoo+implementer","odoo+implementation+consultant","odoo+functional+consultant","odoo+developer"]:
        r = safe_get(f"https://www.linkedin.com/jobs/search/?keywords={q}&f_TPR=r86400&sortBy=DD", timeout=25)
        if not r: continue
        for card in BeautifulSoup(r.text, "html.parser").select("div.base-card"):
            t = card.select_one("h3.base-search-card__title")
            a = card.select_one("a.base-card__full-link")
            if not t or not a: continue
            title = t.get_text(strip=True)
            co    = card.select_one("h4.base-search-card__subtitle a")
            loc   = card.select_one("span.job-search-card__location")
            if is_relevant(title):
                jobs.append(make_job(title,
                    co.get_text(strip=True) if co else "",
                    loc.get_text(strip=True) if loc else "",
                    a["href"].split("?")[0], "LinkedIn 💼"))
    return jobs
 
def scrape_glassdoor():
    jobs = []
    r = safe_get("https://www.glassdoor.com/Job/jobs.htm?sc.keyword=odoo+implementer&sortBy=date_desc")
    if not r: return jobs
    for li in BeautifulSoup(r.text, "html.parser").select("li.react-job-listing"):
        t = li.select_one("a.jobLink span")
        a = li.select_one("a.jobLink")
        if not t or not a: continue
        title = t.get_text(strip=True)
        co    = li.select_one("div.jobHeader a")
        loc   = li.select_one("span.loc")
        if is_relevant(title):
            jobs.append(make_job(title,
                co.get_text(strip=True) if co else "",
                loc.get_text(strip=True) if loc else "",
                "https://www.glassdoor.com"+a.get("href",""), "Glassdoor 🔍"))
    return jobs
 
def scrape_simplyhired():
    jobs = []
    r = safe_get("https://www.simplyhired.com/search?q=odoo+implementer&sort=date")
    if not r: return jobs
    for card in BeautifulSoup(r.text, "html.parser").select("article.SerpJob"):
        t = card.select_one("h3.jobposting-title a")
        if not t: continue
        title = t.get_text(strip=True)
        co    = card.select_one("span[data-testid='companyName']")
        loc   = card.select_one("span[data-testid='searchSerpJobLocation']")
        if is_relevant(title):
            jobs.append(make_job(title,
                co.get_text(strip=True) if co else "",
                loc.get_text(strip=True) if loc else "",
                "https://www.simplyhired.com"+t.get("href",""), "SimplyHired 🌐"))
    return jobs
 
def scrape_remoteok():
    jobs = []
    try:
        r = requests.get("https://remoteok.com/api", headers=HEADERS, timeout=20)
        for item in r.json():
            if not isinstance(item, dict): continue
            title = item.get("position","")
            if is_relevant(title):
                jobs.append(make_job(title,
                    item.get("company",""), item.get("location","Remote"),
                    item.get("url",""), "RemoteOK 🌍"))
    except Exception as e:
        log.warning(f"RemoteOK: {e}")
    return jobs
 
def scrape_remotive():
    jobs = []
    try:
        r = requests.get("https://remotive.com/api/remote-jobs?search=odoo", headers=HEADERS, timeout=20)
        for item in r.json().get("jobs",[]):
            title = item.get("title","")
            if is_relevant(title):
                jobs.append(make_job(title,
                    item.get("company_name",""),
                    item.get("candidate_required_location","Remote"),
                    item.get("url",""), "Remotive 🌍"))
    except Exception as e:
        log.warning(f"Remotive: {e}")
    return jobs
 
def scrape_upwork():
    jobs = []
    for feed_url in [
        "https://www.upwork.com/ab/feed/jobs/rss?q=odoo+implementer&sort=recency",
        "https://www.upwork.com/ab/feed/jobs/rss?q=odoo+implementation&sort=recency",
    ]:
        try:
            for e in feedparser.parse(feed_url).entries:
                title = e.get("title","")
                if is_relevant(title):
                    jobs.append(make_job(title,"","Remote",e.get("link",""),"Upwork 💼"))
        except Exception as ex:
            log.warning(f"Upwork: {ex}")
    return jobs
 
def scrape_weworkremotely():
    jobs = []
    try:
        for e in feedparser.parse("https://weworkremotely.com/remote-jobs.rss").entries:
            title = e.get("title","")
            if is_relevant(title):
                jobs.append(make_job(title,"","Remote",e.get("link",""),"WeWorkRemotely 🌍"))
    except Exception as ex:
        log.warning(f"WWR: {ex}")
    return jobs
 
def scrape_odoo_official():
    jobs = []
    r = safe_get("https://www.odoo.com/jobs")
    if not r: return jobs
    for card in BeautifulSoup(r.text, "html.parser").select("div.o_job_company"):
        t = card.select_one("h5, h4, h3")
        a = card.select_one("a")
        if not t or not a: continue
        title = t.get_text(strip=True)
        href  = a.get("href","")
        link  = href if href.startswith("http") else "https://www.odoo.com"+href
        if is_relevant(title):
            jobs.append(make_job(title,"Odoo S.A.","Belgium/Remote",link,"Odoo Official 🟣"))
    return jobs
 
def scrape_reddit():
    jobs = []
    for sub in ["jobs","remotework","odoo","ERP"]:
        try:
            r = requests.get(
                f"https://www.reddit.com/r/{sub}/search.json?q=odoo+implementer&sort=new&restrict_sr=1",
                headers={**HEADERS, "User-Agent": "OdooJobBot/1.0"}, timeout=20)
            for p in r.json().get("data",{}).get("children",[]):
                d = p.get("data",{})
                title = d.get("title","")
                if is_relevant(title):
                    jobs.append(make_job(title, f"r/{sub}","",
                        "https://reddit.com"+d.get("permalink",""), "Reddit 🔴"))
        except Exception as ex:
            log.warning(f"Reddit: {ex}")
    return jobs
 
def scrape_telegram_channels():
    jobs = []
    for channel in ["OdooJobs","erp_jobs","jobs_egypt","OdooImplementer"]:
        r = safe_get(f"https://t.me/s/{channel}")
        if not r: continue
        for msg in BeautifulSoup(r.text, "html.parser").select("div.tgme_widget_message_text"):
            text = msg.get_text(strip=True)
            if is_relevant(text) and any(w in text.lower() for w in ["hiring","job","vacancy","وظيفة","مطلوب"]):
                title = text[:100] + "..." if len(text) > 100 else text
                jobs.append(make_job(title,"","",f"https://t.me/{channel}",f"Telegram @{channel} 📢"))
    return jobs
 
# ══════════════════════════════════════════════════════════════════════════════
#  الحلقة الرئيسية
# ══════════════════════════════════════════════════════════════════════════════
 
ALL_SCRAPERS = [
    ("Wuzzuf 🇪🇬",        scrape_wuzzuf),
    ("Bayt 🌍",            scrape_bayt),
    ("NaukriGulf 🇦🇪",     scrape_naukrigulf),
    ("GulfTalent 🇦🇪",     scrape_gulftalent),
    ("Forasna 🇪🇬",        scrape_forasna),
    ("Akhtaboot 🇯🇴",      scrape_akhtaboot),
    ("Indeed 🌍",          scrape_indeed),
    ("LinkedIn 💼",        scrape_linkedin),
    ("Glassdoor 🔍",       scrape_glassdoor),
    ("SimplyHired 🌐",     scrape_simplyhired),
    ("RemoteOK 🌍",        scrape_remoteok),
    ("Remotive 🌍",        scrape_remotive),
    ("Upwork 💼",          scrape_upwork),
    ("WeWorkRemotely 🌍",  scrape_weworkremotely),
    ("Odoo Official 🟣",   scrape_odoo_official),
    ("Reddit 🔴",          scrape_reddit),
    ("Telegram 📢",        scrape_telegram_channels),
]
 
 
def run_once(r):
    log.info(f"🔍 بدأ البحث — {len(ALL_SCRAPERS)} مصدر...")
    new_count = 0
    for name, scraper in ALL_SCRAPERS:
        try:
            jobs = scraper()
            if jobs: log.info(f"  {name}: {len(jobs)} نتيجة")
            for job in jobs:
                jid = job_id(job["title"], job["url"])
                if not is_seen(r, jid):
                    mark_seen(r, jid)
                    send_telegram(fmt_msg(job))
                    new_count += 1
                    time.sleep(1.5)
        except Exception as e:
            log.error(f"{name} error: {e}")
    log.info(f"✅ انتهى — وظائف جديدة: {new_count}")
 
 
def main():
    if "YOUR_BOT_TOKEN" in TELEGRAM_TOKEN:
        log.error("❌ ضبط TELEGRAM_TOKEN في Railway Variables")
        return
 
    r = get_redis()
 
    log.info("🤖 بوت Odoo Jobs اشتغل مع Redis!")
    send_telegram(
        "🤖 <b>بوت Odoo Jobs</b> اشتغل! 🚀\n\n"
        f"✅ Redis متصل — مش هيكرر وظيفة أبداً!\n"
        f"⏱ هيتشيك كل <b>{CHECK_INTERVAL_MINUTES} دقيقة</b>\n"
        f"📡 بيراقب <b>{len(ALL_SCRAPERS)} مصدر</b>"
    )
 
    while True:
        run_once(r)
        log.info(f"💤 استنى {CHECK_INTERVAL_MINUTES} دقيقة...")
        time.sleep(CHECK_INTERVAL_MINUTES * 60)
 
 
if __name__ == "__main__":
    main()
 
