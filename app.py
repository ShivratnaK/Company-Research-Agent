from flask import Flask, request, jsonify, send_file, render_template
import os, json
from crawler import crawl
from searcher import find_official_website, search_company_info, find_competitors
from ai_processor import analyze_company, analyze_competitors, AVAILABLE_MODELS, DEFAULT_MODEL
from pdf_generator import generate_pdf
from discord_bot import send_report

app = Flask(__name__)

# In-memory discord config (no DB required)
discord_config = {"bot_token": "", "channel_id": ""}


def is_url(text):
    return text.strip().startswith("http://") or text.strip().startswith("https://") or "." in text.split("/")[0]


def normalize_url(url):
    url = url.strip()
    if not url.startswith("http"):
        url = "https://" + url
    return url


@app.route("/")
def index():
    return render_template("index.html", models=AVAILABLE_MODELS, default_model=DEFAULT_MODEL)


@app.route("/api/models")
def get_models():
    return jsonify(AVAILABLE_MODELS)


@app.route("/api/research", methods=["POST"])
def research():
    body = request.get_json() or {}
    query = body.get("query", "").strip()
    model = body.get("model", DEFAULT_MODEL)

    if not query:
        return jsonify({"error": "Please enter a company name or URL"}), 400

    steps = []

    try:
        # Step 1: Find website
        if is_url(query):
            website = normalize_url(query)
            company_name = query.replace("https://", "").replace("http://", "").split("/")[0].replace("www.", "").split(".")[0].title()
            steps.append({"step": "website_found", "message": f"Using provided URL: {website}"})
        else:
            steps.append({"step": "searching", "message": f"Finding official website for {query}..."})
            website = find_official_website(query)
            company_name = query
            if not website:
                return jsonify({"error": f"Could not find official website for '{query}'. Try entering the URL directly."}), 404
            steps.append({"step": "website_found", "message": f"Found website: {website}"})

        # Step 2: Crawl website
        steps.append({"step": "crawling", "message": "Crawling website pages..."})
        crawled_text, pages_visited = crawl(website)
        steps.append({"step": "crawled", "message": f"Crawled {len(pages_visited)} pages"})

        # Step 3: Search for more info
        steps.append({"step": "searching_info", "message": "Gathering additional information..."})
        search_text = search_company_info(company_name, website)

        # Step 4: AI analysis
        steps.append({"step": "analyzing", "message": "Running AI analysis..."})
        company_data = analyze_company(crawled_text, search_text, company_name, website, model)

        # Step 5: Find competitors
        steps.append({"step": "competitors", "message": "Identifying competitors..."})
        raw_competitors = find_competitors(company_name, company_data.get("industry", ""))
        competitors = analyze_competitors(raw_competitors, company_name, model)

        result = {
            "company": company_data,
            "competitors": competitors,
            "pages_visited": pages_visited,
            "steps": steps
        }

        # Auto-send to Discord if configured
        if discord_config.get("bot_token") and discord_config.get("channel_id"):
            try:
                pdf_buf = generate_pdf(company_data, competitors)
                send_report(
                    discord_config["bot_token"],
                    discord_config["channel_id"],
                    body.get("applicant_name", "Unknown"),
                    body.get("applicant_email", "Unknown"),
                    company_data.get("company_name", company_name),
                    company_data.get("website", website),
                    pdf_buf
                )
            except:
                pass

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/pdf", methods=["POST"])
def download_pdf():
    body = request.get_json() or {}
    company = body.get("company", {})
    competitors = body.get("competitors", [])
    if not company:
        return jsonify({"error": "No company data"}), 400
    try:
        pdf_buffer = generate_pdf(company, competitors)
        name = company.get("company_name", "report").replace(" ", "_")
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=f"{name}_research_report.pdf",
            mimetype="application/pdf"
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/discord/config", methods=["POST"])
def save_discord_config():
    body = request.get_json() or {}
    discord_config["bot_token"]  = body.get("bot_token", "").strip()
    discord_config["channel_id"] = body.get("channel_id", "").strip()
    return jsonify({"message": "Discord configuration saved successfully"})


@app.route("/api/discord/test", methods=["POST"])
def test_discord():
    if not discord_config.get("bot_token") or not discord_config.get("channel_id"):
        return jsonify({"error": "Discord not configured"}), 400
    import io
    dummy_pdf = generate_pdf({"company_name": "Test Company", "website": "https://test.com",
        "phone": "N/A", "address": "N/A", "summary": "This is a test message from Company Research Agent.",
        "products_services": "Test", "pain_points": "Test", "industry": "Test"}, [])
    ok, msg = send_report(discord_config["bot_token"], discord_config["channel_id"],
        "Test User", "test@test.com", "Test Company", "https://test.com", dummy_pdf)
    if ok:
        return jsonify({"message": msg})
    return jsonify({"error": msg}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=False)
