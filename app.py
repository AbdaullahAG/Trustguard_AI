"""
TrustGuard AI — Flask Application
==================================
Backend with policy analysis, PDF export, history, and rate limiting.
"""

from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
from agents import trustguard_pipeline, fetch_policy_from_url
import json, os, hashlib, logging, io, time
from datetime import datetime
from collections import defaultdict
from functools import wraps
from fpdf import FPDF

# ── App setup ─────────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("trustguard")

HISTORY_FILE = "policy_history.json"

# ── Simple in-memory rate limiter ─────────────────────────────────────────────
_rate_store: dict[str, list[float]] = defaultdict(list)
RATE_LIMIT = 5        # max requests
RATE_WINDOW = 60      # per 60 seconds


def rate_limited(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        ip = request.remote_addr or "unknown"
        now = time.time()
        _rate_store[ip] = [t for t in _rate_store[ip] if now - t < RATE_WINDOW]
        if len(_rate_store[ip]) >= RATE_LIMIT:
            return jsonify({"error": "Rate limit exceeded. Please wait a minute."}), 429
        _rate_store[ip].append(now)
        return f(*args, **kwargs)
    return wrapper


# ── History helpers (Policy Change Tracker) ───────────────────────────────────

def load_history() -> dict:
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}


def save_history(data: dict):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def check_policy_changed(site_name: str, new_text: str) -> dict:
    """Return change info if the policy text differs from last saved version."""
    history = load_history()
    key = site_name.lower().replace(" ", "_")
    new_hash = hashlib.sha256(new_text[:6000].encode()).hexdigest()

    if key in history:
        old = history[key]
        if old["hash"] != new_hash:
            history[key] = {
                "hash": new_hash,
                "date": datetime.now().isoformat(),
                "prev_date": old["date"],
                "text_preview": new_text[:300],
                "change_count": old.get("change_count", 0) + 1,
            }
            save_history(history)
            return {
                "changed": True,
                "last_checked": old["date"],
                "change_count": history[key]["change_count"],
                "message": f"⚠️ Policy changed since {old['date'][:10]}!",
            }
        return {
            "changed": False,
            "last_checked": old["date"],
            "change_count": old.get("change_count", 0),
            "message": "✅ Policy unchanged since last check.",
        }

    # First time
    history[key] = {
        "hash": new_hash,
        "date": datetime.now().isoformat(),
        "text_preview": new_text[:300],
        "change_count": 0,
    }
    save_history(history)
    return {"changed": False, "last_checked": None, "change_count": 0,
            "message": "🆕 First time analyzing this site — baseline saved."}


# ── PDF Report Generator ─────────────────────────────────────────────────────

def generate_pdf_report(data: dict) -> bytes:
    """Generate a professional PDF report from analysis results."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", "B", 22)
    pdf.cell(0, 12, "TrustGuard AI - Privacy Analysis Report", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(4)

    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, f"Site: {data.get('site', 'Unknown')}  |  Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
             new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(6)

    analysis = data.get("risk_analysis", {})
    comparison = data.get("benchmark_comparison", {})
    dark = data.get("dark_patterns", {})
    readability = data.get("readability", {})
    rights = data.get("user_rights", {})

    # Risk Score
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, f"Risk Score: {analysis.get('risk_score', 'N/A')}/100 - {analysis.get('risk_level', 'N/A')}",
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 6, analysis.get("verdict", ""))
    pdf.ln(4)

    # Recommendation
    rec = comparison.get("recommendation", "N/A")
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, f"Recommendation: {rec}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # Compliance
    _section_header(pdf, "Compliance Status")
    for law in ["gdpr", "ccpa", "pdpa", "pipeda", "lgpd", "dpdpa"]:
        status = analysis.get(f"{law}_compliance", "N/A")
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 7, f"  {law.upper()}: {status}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # Red Flags
    _section_header(pdf, "Red Flags")
    for flag in analysis.get("red_flags", []):
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 7, f"  [{flag.get('severity', '').upper()}] {flag.get('title', '')}",
                 new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 5, f"    {flag.get('implication', '')}")
        pdf.ln(1)
    pdf.ln(3)

    # Dark Patterns
    _section_header(pdf, f"Dark Patterns (Score: {dark.get('dark_pattern_score', 'N/A')}/100)")
    for pat in dark.get("patterns", [])[:8]:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 7, f"  [{pat.get('severity', '').upper()}] {pat.get('title', '')}",
                 new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 5, f"    {pat.get('explanation', '')}")
        pdf.ln(1)
    pdf.ln(3)

    # Readability
    _section_header(pdf, "Readability Analysis")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, f"  Flesch Reading Ease: {readability.get('flesch_reading_ease', 'N/A')}",
             new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, f"  Grade Level: {readability.get('flesch_grade_level', 'N/A')}",
             new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, f"  Readability Grade: {readability.get('readability_grade', 'N/A')}",
             new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, f"  Word Count: {readability.get('word_count', 'N/A')}",
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    # User Rights
    _section_header(pdf, f"User Rights (Score: {rights.get('rights_score', 'N/A')}/100)")
    for r in rights.get("rights", []):
        status_icon = "+" if r.get("status") == "granted" else ("~" if r.get("status") == "partial" else "-")
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 7, f"  [{status_icon}] {r.get('right', '')} - {r.get('status', '')} ({r.get('ease_of_use', '')})",
                 new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    # Benchmark
    _section_header(pdf, "Benchmark Comparison")
    for c in comparison.get("comparison", []):
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 7, f"  vs {c.get('service', '')}: {c.get('benchmark_score', '')}/100 - {c.get('verdict', '')}",
                 new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("Helvetica", "I", 10)
    pdf.multi_cell(0, 6, comparison.get("ranking_statement", ""))

    # Footer
    pdf.ln(10)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 6, "Generated by TrustGuard AI - Multi-Agent Privacy Policy Analyzer",
             new_x="LMARGIN", new_y="NEXT", align="C")

    return pdf.output()


def _section_header(pdf, title):
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(108, 99, 255)
    pdf.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
@rate_limited
def analyze():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request body."}), 400

    url       = data.get("url", "").strip()
    text      = data.get("text", "").strip()
    site_name = data.get("site_name", "Unknown Site").strip()

    # Get policy text
    if url:
        try:
            text = fetch_policy_from_url(url)
            if not site_name or site_name == "Unknown Site":
                from urllib.parse import urlparse
                site_name = urlparse(url).netloc.replace("www.", "").split(".")[0].capitalize()
        except requests.exceptions.Timeout:
            return jsonify({"error": "The URL took too long to respond. Please try again."}), 408
        except requests.exceptions.ConnectionError:
            return jsonify({"error": "Could not connect to the URL. Please check the link."}), 400
        except Exception as e:
            log.error(f"URL fetch error: {e}")
            return jsonify({"error": f"Could not fetch URL: {str(e)}"}), 400

    if not text or len(text) < 50:
        return jsonify({"error": "Please provide a policy text or valid URL (min 50 chars)."}), 400

    # Change tracker
    change_info = check_policy_changed(site_name, text)

    # Run pipeline
    try:
        result = trustguard_pipeline(text, site_name)
        result["change_info"] = change_info
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 422
    except Exception as e:
        log.error(f"Pipeline error: {e}", exc_info=True)
        return jsonify({"error": "Analysis failed. Please try again."}), 500


@app.route("/export-pdf", methods=["POST"])
def export_pdf():
    """Generate and download a PDF report from cached analysis data."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No analysis data provided."}), 400

    try:
        pdf_bytes = generate_pdf_report(data)
        site = data.get("site", "report").replace(" ", "_")
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"TrustGuard_{site}_{datetime.now().strftime('%Y%m%d')}.pdf",
        )
    except Exception as e:
        log.error(f"PDF generation error: {e}", exc_info=True)
        return jsonify({"error": "Failed to generate PDF."}), 500


@app.route("/history", methods=["GET"])
def history():
    return jsonify(load_history())


@app.route("/history/<site>", methods=["GET"])
def site_history(site):
    h = load_history()
    key = site.lower().replace(" ", "_")
    if key in h:
        return jsonify({key: h[key]})
    return jsonify({"error": "Site not found in history."}), 404


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True, port=5000)