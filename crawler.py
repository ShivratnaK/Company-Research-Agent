import requests, re, time
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from rapidfuzz import fuzz

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

TARGET_PAGES = ["about", "contact", "services", "products", "solutions", "pricing", "team", "company", "who-we-are"]
IGNORE_PATTERNS = ["login", "signup", "register", "signin", "auth", "cart", "checkout", "account", "password", "reset", "#", "javascript:", "mailto:", "tel:"]


def fetch(url, delay=1.0):
    try:
        time.sleep(delay)
        r = requests.get(url, headers=HEADERS, timeout=12)
        return r if r.status_code == 200 else None
    except:
        return None


def clean_text(html, limit=3000):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "svg", "iframe", "form", "aside", "cookie"]):
        tag.decompose()
    text = re.sub(r"\s+", " ", soup.get_text(separator=" ")).strip()
    return text[:limit]


def is_ignored(url):
    path = urlparse(url).path.lower()
    return any(p in path for p in IGNORE_PATTERNS)


def get_all_links(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    domain = urlparse(base_url).netloc
    links = []
    seen = set()
    for a in soup.find_all("a", href=True):
        full = urljoin(base_url, a["href"])
        parsed = urlparse(full)
        path = parsed.path.lower().rstrip("/")
        if parsed.netloc != domain: continue
        if path in seen: continue
        if is_ignored(full): continue
        seen.add(path)
        score = max(fuzz.partial_ratio(kw, path) for kw in TARGET_PAGES)
        links.append((score, full))
    links.sort(reverse=True)
    return [url for score, url in links if score >= 50][:6]


def crawl(base_url):
    base = base_url.rstrip("/")
    pages = {}
    visited = set()

    # 1. Try sitemap first
    for sitemap_path in ["/sitemap.xml", "/sitemap_index.xml"]:
        r = fetch(base + sitemap_path)
        if r:
            try:
                soup = BeautifulSoup(r.text, "xml")
                locs = [l.text for l in soup.find_all("loc") if urlparse(l.text).netloc == urlparse(base).netloc]
                ranked = sorted(locs, key=lambda u: max(fuzz.partial_ratio(kw, urlparse(u).path.lower()) for kw in TARGET_PAGES), reverse=True)
                for url in ranked[:5]:
                    if url not in visited:
                        pr = fetch(url)
                        if pr:
                            pages[url] = clean_text(pr.text)
                            visited.add(url)
            except:
                pass
            break

    # 2. Homepage always
    home = fetch(base)
    if home:
        pages[base] = clean_text(home.text, limit=2000)
        visited.add(base)
        # 3. Discover relevant internal links
        for link in get_all_links(home.text, base):
            if link not in visited and len(pages) < 8:
                r = fetch(link)
                if r:
                    pages[link] = clean_text(r.text)
                    visited.add(link)

    # 4. Direct path fallback
    if len(pages) <= 1:
        for path in ["/about", "/about-us", "/contact", "/services", "/products", "/solutions"]:
            url = base + path
            if url not in visited:
                r = fetch(url)
                if r:
                    pages[url] = clean_text(r.text)
                    visited.add(url)

    combined = " | ".join(pages.values())
    return combined[:6000], list(pages.keys())
