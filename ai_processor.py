import requests, os, json, re

OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

DEFAULT_MODEL = "openrouter/free"

# NOTE: OpenRouter's free-model catalog changes weekly — model IDs get retired
# without notice ("No endpoints found for X" = that slug is dead). "openrouter/free"
# is a router that always points at whatever free model is currently live, so it's
# used as the default and as the final fallback below. The other entries are
# current as of this writing; if one 404s, check
# https://openrouter.ai/models?max_price=0 for live replacements.
AVAILABLE_MODELS = [
    {"id": "openrouter/free",                       "name": "Auto (Free Router) — Recommended"},
    {"id": "openai/gpt-oss-20b:free",                "name": "GPT-OSS 20B (Free)"},
    {"id": "meta-llama/llama-3.3-70b-instruct:free", "name": "Llama 3.3 70B (Free)"},
    {"id": "deepseek/deepseek-r1-distill:free",      "name": "DeepSeek R1 Distill (Free)"},
    {"id": "google/gemma-3-12b-it:free",             "name": "Google Gemma 3 12B (Free)"},
]

FALLBACK_MODEL = "openrouter/free"


def call_ai(prompt, model=DEFAULT_MODEL):
    try:
        r = requests.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://company-research-agent.onrender.com",
                "X-Title": "Company Research Agent"
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
                "max_tokens": 1500
            },
            timeout=30
        )
        data = r.json()
        print(f"OpenRouter response keys: {list(data.keys())}")

        if "error" in data:
            print(f"OpenRouter error: {data['error']}")
            if model != FALLBACK_MODEL:
                print(f"Falling back to {FALLBACK_MODEL}...")
                return call_ai(prompt, FALLBACK_MODEL)
            return ""

        choices = data.get("choices") or []
        if not choices:
            print(f"Empty choices. Full response: {data}")
            return ""

        return choices[0]["message"]["content"].strip()

    except Exception as e:
        print(f"AI call exception: {e}")
        return ""


def analyze_company(crawled_text, search_text, company_name, website, model=DEFAULT_MODEL):
    prompt = f"""You are a business intelligence analyst. Analyze the following information about {company_name} ({website}) and extract structured insights.

CRAWLED WEBSITE TEXT:
{crawled_text[:3000]}

SEARCH RESULTS:
{search_text[:1500]}

Return ONLY a valid raw JSON object with exactly these fields:
{{
  "company_name": "full official company name",
  "website": "official website URL",
  "phone": "phone number or N/A",
  "address": "full address or N/A",
  "summary": "2-3 sentence company overview",
  "products_services": "concise description of main products and services",
  "pain_points": "3 specific AI-generated pain points this company likely faces, as a single paragraph",
  "industry": "the industry this company operates in"
}}

RULES:
- Only use info explicitly found in the provided text for phone and address. Never fabricate contact details.
- For summary, products_services, and pain_points always generate thoughtful content based on what you know.
- Return ONLY raw JSON. No markdown, no backticks, no explanation."""

    raw = call_ai(prompt, model)
    raw = re.sub(r"^```(?:json)?", "", raw).rstrip("```").strip()
    try:
        return json.loads(raw)
    except:
        return {
            "company_name": company_name,
            "website": website,
            "phone": "N/A",
            "address": "N/A",
            "summary": raw[:300] if raw else "Unable to generate summary.",
            "products_services": "N/A",
            "pain_points": "N/A",
            "industry": "N/A"
        }


def analyze_competitors(competitors_raw, company_name, model=DEFAULT_MODEL):
    if not competitors_raw:
        return []
    names = [f"- {c['name']} ({c['website']})" for c in competitors_raw]
    prompt = f"""Given these potential competitors of {company_name}:
{chr(10).join(names)}

Return ONLY a JSON array of the 4 most relevant competitors in this format:
[{{"name": "Company Name", "website": "https://website.com"}}, ...]

No markdown, no backticks, no explanation."""

    raw = call_ai(prompt, model)
    raw = re.sub(r"^```(?:json)?", "", raw).rstrip("```").strip()
    try:
        result = json.loads(raw)
        return result if isinstance(result, list) else competitors_raw[:4]
    except:
        return competitors_raw[:4]