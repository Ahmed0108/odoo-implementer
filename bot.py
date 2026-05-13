"""
Odoo Jobs Telegram Bot — MAXIMUM COVERAGE Edition
===================================================
يغطي: مواقع التوظيف + سوشيال ميديا + RSS + APIs
المواقع: 20+ موقع توظيف | LinkedIn | Twitter/X | Facebook Groups | Telegram Channels
"""

import os
import time
import hashlib
import logging
import requests
from datetime import datetime
from bs4 import BeautifulSoup
import feedparser

# ─── إعدادات ─────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_TOKEN", "8341918328:AAEzbSoZ9gXR4kQowFJnaxHZp-DKG8YBbTU")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "1275130214")
CHECK_INTERVAL_MINUTES = int(os.environ.get("CHECK_INTERVAL", "20"))

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

seen_jobs: set = set()

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
#  مواقع التوظيف — الشرق الأوسط وأفريقيا
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
    urls = [
        "https://www.bayt.com/en/egypt/jobs/odoo-implementer-jobs/",
        "https://www.bayt.com/en/saudi-arabia/jobs/odoo-implementer-jobs/",
        "https://www.bayt.com/en/uae/jobs/odoo-implementer-jobs/",
        "https://www.bayt.com/en/international/jobs/odoo-implementer-jobs/",
        "https://www.bayt.com/en/international/jobs/odoo-consultant-jobs/",
    ]
    for url in urls:
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
    urls = [
        "https://www.naukrigulf.com/odoo-implementer-jobs",
        "https://www.naukrigulf.com/odoo-implementation-consultant-jobs",
        "https://www.naukrigulf.com/odoo-developer-jobs",
        "https://www.naukrigulf.com/odoo-consultant-jobs",
    ]
    for url in urls:
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
    urls = [
        "https://www.gulftalent.com/jobs/odoo-implementer-jobs",
        "https://www.gulftalent.com/jobs/odoo-consultant-jobs",
    ]
    for url in urls:
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

def scrape_tanqeeb():
    jobs = []
    r = safe_get("https://tanqeeb.com/jobs?q=odoo+implementer&sort=newest")
    if not r: return jobs
    for card in BeautifulSoup(r.text, "html.parser").select("div.job-item"):
        t = card.select_one("h3 a, h2 a")
        if not t: continue
        title = t.get_text(strip=True)
        href  = t.get("href","")
        link  = href if href.startswith("http") else "https://tanqeeb.com"+href
        co    = card.select_one("span.company")
        loc   = card.select_one("span.location")
        if is_relevant(title):
            jobs.append(make_job(title,
                co.get_text(strip=True) if co else "",
                loc.get_text(strip=True) if loc else "", link, "Tanqeeb 🌍"))
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

def scrape_jobzella():
    jobs = []
    r = safe_get("https://www.jobzella.com/search/jobs/1/all/odoo-implementer")
    if not r: return jobs
    for card in BeautifulSoup(r.text, "html.parser").select("div.job-item"):
        t = card.select_one("h3 a")
        if not t: continue
        title = t.get_text(strip=True)
        href  = t.get("href","")
        link  = href if href.startswith("http") else "https://www.jobzella.com"+href
        if is_relevant(title):
            jobs.append(make_job(title, "", "", link, "Jobzella 🇪🇬"))
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

# ══════════════════════════════════════════════════════════════════════════════
#  مواقع التوظيف — عالمي
# ══════════════════════════════════════════════════════════════════════════════

def scrape_indeed():
    jobs = []
    feeds = [
        "https://www.indeed.com/rss?q=odoo+implementer&sort=date",
        "https://www.indeed.com/rss?q=odoo+implementation+consultant&sort=date",
        "https://www.indeed.com/rss?q=odoo+developer&sort=date",
        "https://eg.indeed.com/rss?q=odoo+implementer&sort=date",
        "https://sa.indeed.com/rss?q=odoo+implementer&sort=date",
        "https://ae.indeed.com/rss?q=odoo+implementer&sort=date",
    ]
    for feed_url in feeds:
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
    queries = [
        "odoo+implementer", "odoo+implementation+consultant",
        "odoo+erp+implementer", "odoo+functional+consultant",
        "odoo+developer", "odoo+technical+consultant",
    ]
    for q in queries:
        r = safe_get(
            f"https://www.linkedin.com/jobs/search/?keywords={q}"
            f"&f_TPR=r86400&sortBy=DD", timeout=25)
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
    for q in ["odoo+implementer", "odoo+consultant"]:
        r = safe_get(
            f"https://www.glassdoor.com/Job/jobs.htm?"
            f"sc.keyword={q}&sortBy=date_desc")
        if not r: continue
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
    for q in ["odoo+implementer", "odoo+implementation+consultant"]:
        r = safe_get(f"https://www.simplyhired.com/search?q={q}&sort=date")
        if not r: continue
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

def scrape_ziprecruiter():
    jobs = []
    r = safe_get("https://www.ziprecruiter.com/candidate/search?search=odoo+implementer&sort=date_posted_desc")
    if not r: return jobs
    for card in BeautifulSoup(r.text, "html.parser").select("article.job_result"):
        t = card.select_one("h2 a")
        if not t: continue
        title = t.get_text(strip=True)
        co    = card.select_one("a.job_result_company_name")
        loc   = card.select_one("li.location_name")
        if is_relevant(title):
            jobs.append(make_job(title,
                co.get_text(strip=True) if co else "",
                loc.get_text(strip=True) if loc else "",
                t.get("href",""), "ZipRecruiter 🇺🇸"))
    return jobs

def scrape_monster():
    jobs = []
    r = safe_get("https://www.monster.com/jobs/search?q=odoo-implementer&sort=created_desc")
    if not r: return jobs
    for card in BeautifulSoup(r.text, "html.parser").select("div.job-search-result-content"):
        t = card.select_one("h3.title a")
        if not t: continue
        title = t.get_text(strip=True)
        co    = card.select_one("span.company")
        loc   = card.select_one("span.location")
        if is_relevant(title):
            jobs.append(make_job(title,
                co.get_text(strip=True) if co else "",
                loc.get_text(strip=True) if loc else "",
                t.get("href",""), "Monster 🌐"))
    return jobs

def scrape_careerbuilder():
    jobs = []
    r = safe_get("https://www.careerbuilder.com/jobs?keywords=odoo+implementer&sort=date_asc")
    if not r: return jobs
    for card in BeautifulSoup(r.text, "html.parser").select("li.data-results-content-parent"):
        t = card.select_one("div.data-results-title a")
        if not t: continue
        title = t.get_text(strip=True)
        co    = card.select_one("div.data-details span:first-child")
        loc   = card.select_one("span[class*='location']")
        if is_relevant(title):
            jobs.append(make_job(title,
                co.get_text(strip=True) if co else "",
                loc.get_text(strip=True) if loc else "",
                t.get("href",""), "CareerBuilder 🇺🇸"))
    return jobs

def scrape_dice():
    """موقع تقني متخصص"""
    jobs = []
    r = safe_get("https://www.dice.com/jobs?q=odoo+implementer&datePosted=ONE_DAY&sort=updated_date_desc")
    if not r: return jobs
    for card in BeautifulSoup(r.text, "html.parser").select("div.card"):
        t = card.select_one("a.card-title-link")
        if not t: continue
        title = t.get_text(strip=True)
        co    = card.select_one("a.company-name")
        loc   = card.select_one("span.location")
        if is_relevant(title):
            href = t.get("href","")
            link = href if href.startswith("http") else "https://www.dice.com"+href
            jobs.append(make_job(title,
                co.get_text(strip=True) if co else "",
                loc.get_text(strip=True) if loc else "", link, "Dice 💻"))
    return jobs

def scrape_remoteok():
    """وظائف Remote"""
    jobs = []
    try:
        r = requests.get("https://remoteok.com/api", headers=HEADERS, timeout=20)
        data = r.json()
        for item in data:
            if not isinstance(item, dict): continue
            title = item.get("position","")
            if is_relevant(title):
                jobs.append(make_job(title,
                    item.get("company",""),
                    item.get("location","Remote"),
                    item.get("url",""), "RemoteOK 🌍"))
    except Exception as e:
        log.warning(f"RemoteOK: {e}")
    return jobs

def scrape_weworkremotely():
    """وظائف Remote"""
    jobs = []
    feeds = [
        "https://weworkremotely.com/remote-jobs.rss",
        "https://weworkremotely.com/categories/remote-programming-jobs.rss",
    ]
    for feed_url in feeds:
        try:
            for e in feedparser.parse(feed_url).entries:
                title = e.get("title","")
                if is_relevant(title):
                    jobs.append(make_job(title,"","Remote",e.get("link",""),"WeWorkRemotely 🌍"))
        except Exception as ex:
            log.warning(f"WWR: {ex}")
    return jobs

def scrape_remotive():
    """وظائف Remote"""
    jobs = []
    try:
        r = requests.get(
            "https://remotive.com/api/remote-jobs?search=odoo",
            headers=HEADERS, timeout=20)
        data = r.json().get("jobs",[])
        for item in data:
            title = item.get("title","")
            if is_relevant(title):
                jobs.append(make_job(title,
                    item.get("company_name",""),
                    item.get("candidate_required_location","Remote"),
                    item.get("url",""), "Remotive 🌍"))
    except Exception as e:
        log.warning(f"Remotive: {e}")
    return jobs

# ══════════════════════════════════════════════════════════════════════════════
#  مواقع تقنية متخصصة
# ══════════════════════════════════════════════════════════════════════════════

def scrape_stackoverflow_jobs():
    """Stack Overflow Jobs RSS"""
    jobs = []
    try:
        feed = feedparser.parse("https://stackoverflow.com/jobs/feed?q=odoo&sort=newest")
        for e in feed.entries:
            title = e.get("title","")
            if is_relevant(title):
                jobs.append(make_job(title,
                    e.get("author",""),
                    e.get("location",""),
                    e.get("link",""), "StackOverflow Jobs 💻"))
    except Exception as ex:
        log.warning(f"SO Jobs: {ex}")
    return jobs

def scrape_github_jobs():
    """GitHub Jobs RSS (via alternative feeds)"""
    jobs = []
    try:
        feed = feedparser.parse("https://jobs.github.com/positions.json?description=odoo+implementer&utf8=✓")
        for e in feed.entries:
            title = e.get("title","")
            if is_relevant(title):
                jobs.append(make_job(title,"","",e.get("link",""),"GitHub Jobs 💻"))
    except Exception as ex:
        log.warning(f"GitHub Jobs: {ex}")
    return jobs

def scrape_freelancer():
    """Freelancer.com projects"""
    jobs = []
    try:
        r = requests.get(
            "https://www.freelancer.com/api/projects/0.1/projects/active/"
            "?query=odoo+implementer&sort_field=time_updated&compact=true",
            headers=HEADERS, timeout=20)
        data = r.json().get("result",{}).get("projects",[])
        for item in data:
            title = item.get("title","")
            if is_relevant(title):
                pid = item.get("id","")
                jobs.append(make_job(title,
                    "Freelancer Client","Remote",
                    f"https://www.freelancer.com/projects/{pid}", "Freelancer 💼"))
    except Exception as e:
        log.warning(f"Freelancer: {e}")
    return jobs

def scrape_upwork():
    """Upwork RSS feed"""
    jobs = []
    feeds = [
        "https://www.upwork.com/ab/feed/jobs/rss?q=odoo+implementer&sort=recency",
        "https://www.upwork.com/ab/feed/jobs/rss?q=odoo+implementation&sort=recency",
    ]
    for feed_url in feeds:
        try:
            for e in feedparser.parse(feed_url).entries:
                title = e.get("title","")
                if is_relevant(title):
                    jobs.append(make_job(title,"","Remote",e.get("link",""),"Upwork 💼"))
        except Exception as ex:
            log.warning(f"Upwork: {ex}")
    return jobs

# ══════════════════════════════════════════════════════════════════════════════
#  سوشيال ميديا & منصات تانية
# ══════════════════════════════════════════════════════════════════════════════

def scrape_twitter_nitter():
    """Twitter/X عبر Nitter (بديل مفتوح المصدر)"""
    jobs = []
    queries = [
        "odoo implementer hiring",
        "odoo implementation job",
        "odoo developer vacancy",
        "وظيفة odoo",
    ]
    nitter_instances = [
        "https://nitter.net",
        "https://nitter.privacydev.net",
    ]
    for query in queries:
        for nitter in nitter_instances:
            r = safe_get(f"{nitter}/search?q={query.replace(' ','+')}&f=tweets")
            if not r: continue
            for tweet in BeautifulSoup(r.text, "html.parser").select("div.tweet-content"):
                text = tweet.get_text(strip=True)
                if is_relevant(text) and any(w in text.lower() for w in ["hiring","job","vacancy","وظيفة","مطلوب"]):
                    link_el = tweet.select_one("a")
                    link = nitter + link_el["href"] if link_el else nitter
                    title = text[:80] + "..." if len(text) > 80 else text
                    jobs.append(make_job(title,"","",link,"Twitter/X 🐦"))
            break  # نجح nitter instance
    return jobs

def scrape_telegram_channels():
    """
    قنوات تيليجرام للوظائف عبر RSS/preview
    ملاحظة: بيقرأ preview العام للقنوات
    """
    jobs = []
    channels = [
        "EgyptJobsOdoo",
        "OdooJobs",
        "OdooImplementer",
        "erp_jobs",
        "jobs_egypt",
        "وظائف_odoo",
    ]
    for channel in channels:
        r = safe_get(f"https://t.me/s/{channel}")
        if not r: continue
        for msg in BeautifulSoup(r.text, "html.parser").select("div.tgme_widget_message_text"):
            text = msg.get_text(strip=True)
            if is_relevant(text) and any(w in text.lower() for w in
                    ["hiring","job","vacancy","وظيفة","مطلوب","implementer"]):
                title = text[:100] + "..." if len(text) > 100 else text
                jobs.append(make_job(title,"Telegram Channel","",
                    f"https://t.me/{channel}", f"Telegram: @{channel} 📢"))
    return jobs

def scrape_reddit():
    """Reddit — r/jobs, r/remotework, r/odoo"""
    jobs = []
    subs = ["jobs", "remotework", "odoo", "ERP"]
    for sub in subs:
        try:
            r = requests.get(
                f"https://www.reddit.com/r/{sub}/search.json"
                f"?q=odoo+implementer&sort=new&restrict_sr=1",
                headers={**HEADERS, "User-Agent": "OdooJobBot/1.0"},
                timeout=20)
            posts = r.json().get("data",{}).get("children",[])
            for p in posts:
                d = p.get("data",{})
                title = d.get("title","")
                if is_relevant(title) or any(w in title.lower() for w in ["hiring","job","odoo"]):
                    jobs.append(make_job(title,
                        f"r/{sub}","",
                        "https://reddit.com"+d.get("permalink",""),
                        "Reddit 🔴"))
        except Exception as ex:
            log.warning(f"Reddit: {ex}")
    return jobs

def scrape_facebook_groups():
    """
    Facebook Groups — عبر صفحات عامة (Public Pages RSS)
    ملاحظة: محدود بدون API Key
    """
    jobs = []
    # Facebook public job pages RSS
    pages = [
        "https://www.facebook.com/feeds/page.php?id=OdooJobsEgypt&format=rss20",
    ]
    for page_rss in pages:
        try:
            for e in feedparser.parse(page_rss).entries:
                title = e.get("title","")
                if is_relevant(title):
                    jobs.append(make_job(title,"","",e.get("link",""),"Facebook 📘"))
        except Exception:
            pass
    return jobs

# ══════════════════════════════════════════════════════════════════════════════
#  مواقع ERP متخصصة
# ══════════════════════════════════════════════════════════════════════════════

def scrape_erp_jobs_specific():
    """مواقع متخصصة في وظائف ERP و Odoo"""
    jobs = []

    # Odoo Community Jobs
    r = safe_get("https://www.odoo.com/jobs")
    if r:
        for card in BeautifulSoup(r.text, "html.parser").select("div.o_job_company"):
            t = card.select_one("h5, h4, h3")
            a = card.select_one("a")
            if not t or not a: continue
            title = t.get_text(strip=True)
            href  = a.get("href","")
            link  = href if href.startswith("http") else "https://www.odoo.com"+href
            if is_relevant(title):
                jobs.append(make_job(title,"Odoo S.A.","Belgium/Remote",link,"Odoo Official 🟣"))

    # ERP Jobs Board
    r = safe_get("https://erpjobs.co.uk/?s=odoo+implementer")
    if r:
        for card in BeautifulSoup(r.text, "html.parser").select("article"):
            t = card.select_one("h2 a, h3 a")
            if not t: continue
            title = t.get_text(strip=True)
            if is_relevant(title):
                jobs.append(make_job(title,"","",t.get("href",""),"ERPJobs 🇬🇧"))

    return jobs

def scrape_jobgether():
    jobs = []
    r = safe_get("https://jobgether.com/offers?q=odoo+implementer&sort=date")
    if not r: return jobs
    for card in BeautifulSoup(r.text, "html.parser").select("div.offer-card"):
        t = card.select_one("h3 a, h2 a")
        if not t: continue
        title = t.get_text(strip=True)
        href  = t.get("href","")
        link  = href if href.startswith("http") else "https://jobgether.com"+href
        if is_relevant(title):
            jobs.append(make_job(title,"","",link,"Jobgether 🌐"))
    return jobs

def scrape_otta():
    jobs = []
    try:
        r = requests.get(
            "https://app.otta.com/api/jobs?query=odoo+implementer&limit=20",
            headers=HEADERS, timeout=20)
        for item in r.json().get("results",[]):
            title = item.get("title","")
            if is_relevant(title):
                jobs.append(make_job(title,
                    item.get("company",{}).get("name",""),
                    item.get("location",""),
                    f"https://app.otta.com/jobs/{item.get('externalId','')}",
                    "Otta 🌐"))
    except Exception as e:
        log.warning(f"Otta: {e}")
    return jobs

def scrape_wellfound():
    """Wellfound (AngelList) — Startups"""
    jobs = []
    r = safe_get("https://wellfound.com/jobs?q=odoo+implementer")
    if not r: return jobs
    for card in BeautifulSoup(r.text, "html.parser").select("div[class*='JobListingCard']"):
        t = card.select_one("h3, h4")
        a = card.select_one("a[href*='/jobs/']")
        if not t or not a: continue
        title = t.get_text(strip=True)
        if is_relevant(title):
            href = a.get("href","")
            link = href if href.startswith("http") else "https://wellfound.com"+href
            jobs.append(make_job(title,"","",link,"Wellfound 🚀"))
    return jobs

def scrape_rozee():
    """Pakistan + Middle East"""
    jobs = []
    r = safe_get("https://www.rozee.pk/job/jsearch/q/odoo-implementer")
    if not r: return jobs
    for card in BeautifulSoup(r.text, "html.parser").select("div.job-listing"):
        t = card.select_one("h3 a")
        if not t: continue
        title = t.get_text(strip=True)
        href  = t.get("href","")
        link  = href if href.startswith("http") else "https://www.rozee.pk"+href
        if is_relevant(title):
            jobs.append(make_job(title,"","",link,"Rozee.pk 🇵🇰"))
    return jobs

def scrape_linkedin_rss():
    """LinkedIn RSS feeds للبحث"""
    jobs = []
    keywords = ["odoo+implementer", "odoo+implementation+consultant", "odoo+erp+developer"]
    geo_ids  = ["", "&geoId=101356761", "&geoId=104093752"]  # Global, Egypt, UAE
    for kw in keywords:
        for geo in geo_ids:
            try:
                feed = feedparser.parse(
                    f"https://www.linkedin.com/jobs/search/?keywords={kw}"
                    f"{geo}&f_TPR=r86400&sortBy=DD&format=rss")
                for e in feed.entries:
                    title = e.get("title","")
                    if is_relevant(title):
                        jobs.append(make_job(title,"","",e.get("link",""),"LinkedIn RSS 💼"))
            except Exception:
                pass
    return jobs

# ══════════════════════════════════════════════════════════════════════════════
#  الحلقة الرئيسية
# ══════════════════════════════════════════════════════════════════════════════

ALL_SCRAPERS = [
    # مصر والشرق الأوسط
    ("🇪🇬 Wuzzuf",          scrape_wuzzuf),
    ("🌍 Bayt",              scrape_bayt),
    ("🇦🇪 NaukriGulf",       scrape_naukrigulf),
    ("🇦🇪 GulfTalent",       scrape_gulftalent),
    ("🌍 Tanqeeb",           scrape_tanqeeb),
    ("🇪🇬 Forasna",          scrape_forasna),
    ("🇪🇬 Jobzella",         scrape_jobzella),
    ("🇯🇴 Akhtaboot",        scrape_akhtaboot),
    ("🇵🇰 Rozee",            scrape_rozee),
    # عالمي
    ("🌍 Indeed",            scrape_indeed),
    ("💼 LinkedIn",          scrape_linkedin),
    ("💼 LinkedIn RSS",      scrape_linkedin_rss),
    ("🔍 Glassdoor",         scrape_glassdoor),
    ("🌐 SimplyHired",       scrape_simplyhired),
    ("🇺🇸 ZipRecruiter",     scrape_ziprecruiter),
    ("🌐 Monster",           scrape_monster),
    ("🇺🇸 CareerBuilder",    scrape_careerbuilder),
    # تقني
    ("💻 Dice",              scrape_dice),
    ("💻 StackOverflow",     scrape_stackoverflow_jobs),
    ("💻 GitHub Jobs",       scrape_github_jobs),
    # Remote
    ("🌍 RemoteOK",          scrape_remoteok),
    ("🌍 WeWorkRemotely",    scrape_weworkremotely),
    ("🌍 Remotive",          scrape_remotive),
    # Freelance
    ("💼 Upwork",            scrape_upwork),
    ("💼 Freelancer",        scrape_freelancer),
    # Odoo متخصص
    ("🟣 Odoo Official",     scrape_erp_jobs_specific),
    ("🚀 Wellfound",         scrape_wellfound),
    ("🌐 Jobgether",         scrape_jobgether),
    ("🌐 Otta",              scrape_otta),
    # سوشيال ميديا
    ("🐦 Twitter/X",         scrape_twitter_nitter),
    ("📢 Telegram Channels", scrape_telegram_channels),
    ("🔴 Reddit",            scrape_reddit),
    ("📘 Facebook",          scrape_facebook_groups),
]


def run_once():
    global seen_jobs
    log.info(f"🔍 بدأ البحث — {len(ALL_SCRAPERS)} مصدر...")
    new_count = 0

    for name, scraper in ALL_SCRAPERS:
        try:
            jobs = scraper()
            found = len(jobs)
            if found:
                log.info(f"  {name}: {found} نتيجة")
            for job in jobs:
                jid = job_id(job["title"], job["url"])
                if jid not in seen_jobs:
                    seen_jobs.add(jid)
                    send_telegram(fmt_msg(job))
                    new_count += 1
                    time.sleep(1.5)
        except Exception as e:
            log.error(f"{name} error: {e}")

    log.info(f"✅ انتهى — وظائف جديدة: {new_count}")


def main():
    if "YOUR_BOT_TOKEN" in TELEGRAM_TOKEN:
        log.error("❌ ضبط TELEGRAM_TOKEN في Railway Environment Variables")
        return

    log.info(f"🤖 بوت Odoo Jobs اشتغل! — {len(ALL_SCRAPERS)} مصدر")
    send_telegram(
        "🤖 <b>بوت Odoo Jobs</b> اشتغل! 🚀\n\n"
        f"⏱ هيتشيك كل <b>{CHECK_INTERVAL_MINUTES} دقيقة</b>\n"
        f"📡 بيراقب <b>{len(ALL_SCRAPERS)} مصدر</b>:\n\n"
        "🇪🇬 Wuzzuf · Forasna · Jobzella\n"
        "🌍 Indeed · Bayt · NaukriGulf · GulfTalent · Akhtaboot\n"
        "💼 LinkedIn · Glassdoor · SimplyHired · Monster\n"
        "🌐 ZipRecruiter · CareerBuilder · Dice · RemoteOK\n"
        "💼 Upwork · Freelancer · WeWorkRemotely · Remotive\n"
        "🟣 Odoo Official · Wellfound · Otta · Jobgether\n"
        "📱 Twitter/X · Telegram · Reddit · Facebook"
    )

    while True:
        run_once()
        log.info(f"💤 استنى {CHECK_INTERVAL_MINUTES} دقيقة...")
        time.sleep(CHECK_INTERVAL_MINUTES * 60)


if __name__ == "__main__":
    main()
