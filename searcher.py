import requests, os, re

SERPER_KEY = os.getenv("SERPER_API_KEY", "")
SERPER_URL = "https://google.serper.dev/search"


def search(query, num=5):
    try:
        r = requests.post(
            SERPER_URL,
            headers={"X-API-KEY": SERPER_KEY, "Content-Type": "application/json"},
            json={"q": query, "num": num},
            timeout=10
        )
        data = r.json()
        print(f"Serper status: {r.status_code}, results: {len(data.get('organic', []))}")
        results = []
        for item in data.get("organic", []):
            results.append({
                "title": item.get("title", ""),
                "link":  item.get("link", ""),
                "snippet": item.get("snippet", "")
            })
        return results
    except Exception as e:
        print(f"Serper error: {e}")
        return []


def find_official_website(company_name):
    # Try multiple search queries for robustness
    queries = [
        f"{company_name} official website",
        f"{company_name} homepage",
        f'site:{company_name.lower().replace(" ","")}.com',
    ]
    name_clean = company_name.lower().replace(" ", "").replace("-", "")

    for query in queries:
        results = search(query, num=5)
        # First pass: look for domain that matches company name
        for r in results:
            link = r.get("link", "")
            if not link: continue
            domain = link.replace("https://", "").replace("http://", "").split("/")[0].replace("www.", "")
            domain_clean = domain.split(".")[0].lower().replace("-", "")
            if name_clean in domain_clean or domain_clean in name_clean:
                base = link.split("/")[0] + "//" + link.replace("https://", "").replace("http://", "").split("/")[0]
                print(f"Found website: {base}")
                return base
        # Second pass: just return first result if we got any
        if results:
            first = results[0].get("link", "")
            if first:
                parsed = first.split("/")
                base = parsed[0] + "//" + parsed[2] if len(parsed) >= 3 else first
                print(f"Using first result: {base}")
                return base

    # Last resort: construct from company name
    guessed = f"https://www.{name_clean}.com"
    print(f"Guessing URL: {guessed}")
    return guessed


def search_company_info(company_name, website):
    snippets = []
    queries = [
        f"{company_name} company overview products services",
        f"{company_name} contact address phone number",
        f"{company_name} about us"
    ]
    for q in queries:
        results = search(q, num=3)
        for r in results:
            if r.get("snippet"):
                snippets.append(r["snippet"])
    return " ".join(snippets)[:3000]


def find_competitors(company_name, industry_hint=""):
    query = f"top competitors of {company_name} alternatives {industry_hint}".strip()
    results = search(query, num=8)
    competitors = []
    seen_domains = set()
    name_clean = company_name.lower().replace(" ", "")

    for r in results:
        link = r.get("link", "")
        title = r.get("title", "")
        if not link: continue
        domain = link.replace("https://", "").replace("http://", "").split("/")[0].replace("www.", "")
        domain_root = domain.split(".")[0].lower()
        if domain in seen_domains: continue
        if domain_root == name_clean or name_clean in domain_root: continue
        seen_domains.add(domain)
        name = title.split("-")[0].split("|")[0].strip()
        base_url = link.split("/")[0] + "//" + link.replace("https://", "").replace("http://", "").split("/")[0]
        competitors.append({"name": name, "website": base_url})
        if len(competitors) >= 5: break
    return competitors
