"""
TrustGuard AI — Multi-Agent Privacy Policy Analyzer
====================================================
6 specialized AI agents + retry logic + in-memory caching. 
"""

from openai import AzureOpenAI
from dotenv import load_dotenv
import os
import json
import re
import hashlib
import logging
import time
import requests
from bs4 import BeautifulSoup
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL", 86400))  # default 24 h

load_dotenv()
log = logging.getLogger("trustguard")

client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_ENDPOINT"),
    api_key=os.getenv("AZURE_API_KEY"),
    api_version="2025-03-01-preview",
)
DEPLOYMENT = os.getenv("DEPLOYMENT_NAME", "gpt-5.4")

BENCHMARKS = {
    "TikTok": {
        "risk_score": 82,
        "issues": [
            "sells voice data",
            "shares with governments",
            "retains data after deletion"]},
    "Facebook": {
        "risk_score": 78,
        "issues": [
            "tracks off-platform",
            "sells to advertisers",
            "vague retention"]},
    "WhatsApp": {
        "risk_score": 65,
        "issues": [
            "shares metadata with Meta",
            "phone number required"]},
    "Google": {
        "risk_score": 70,
        "issues": [
            "cross-service tracking",
            "ad profiling",
            "location history"]},
    "Apple": {
        "risk_score": 35,
        "issues": ["limited third-party sharing"]},
    "Instagram": {
        "risk_score": 76,
        "issues": [
            "behavioral tracking",
            "cross-platform profiling"]},
    "X (Twitter)": {
        "risk_score": 72,
        "issues": [
            "ad profiling",
            "third-party data sharing",
            "vague retention"]},
    "Snapchat": {
        "risk_score": 68,
        "issues": [
            "location tracking",
            "content scanning",
            "ad targeting"]},
}

# ── In-memory analysis cache with TTL ────────────────────────────────────────
# NOTE: per-process only — fine for single-worker / hackathon demo.
# For multi-worker production use Redis or a shared store.
_cache: dict = {}   # key → {"result": ..., "ts": float}


def _cache_key(text: str) -> str:
    return hashlib.sha256(text[:6000].encode()).hexdigest()


def _cache_get(key: str):
    entry = _cache.get(key)
    if entry and (time.time() - entry["ts"]) < CACHE_TTL_SECONDS:
        return entry["result"]
    if key in _cache:
        del _cache[key]   # expired — evict
    return None


def _cache_set(key: str, result: dict):
    _cache[key] = {"result": result, "ts": time.time()}


def cache_clear():
    """Utility — call to wipe all cached entries (e.g. from tests)."""
    _cache.clear()


# ═══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def fetch_policy_from_url(url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36 TrustGuardAI/2.0",
        "Accept-Language": "en-US,en;q=0.9",
    }
    resp = requests.get(url, headers=headers, timeout=20, allow_redirects=True)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer",
                    "header", "aside", "iframe", "noscript"]):
        tag.decompose()
    text = soup.get_text(separator="\n", strip=True)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text[:12000]


def _smart_chunk(text: str, max_chars: int = 5000) -> list:
    if len(text) <= max_chars:
        return [text]
    chunks, current = [], ""
    for para in text.split("\n\n"):
        if len(current) + len(para) + 2 > max_chars and current:
            chunks.append(current.strip())
            current = current[-500:] + "\n\n" + para
        else:
            current = current + "\n\n" + para if current else para
    if current.strip():
        chunks.append(current.strip())
    return chunks or [text[:max_chars]]


def _call(system: str, user: str, temp: float = 0.1, retries: int = 3) -> dict:
    """LLM call with exponential-backoff retry and JSON extraction."""
    last_err = None
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model=DEPLOYMENT,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=temp,
            )
            raw = response.choices[0].message.content
            clean = raw.replace("```json", "").replace("```", "").strip()
            match = re.search(r'\{[\s\S]*\}', clean)
            return json.loads(match.group() if match else clean)
        except json.JSONDecodeError as e:
            last_err = ValueError(
                f"AI returned invalid JSON (attempt {attempt+1}): {e}")
            log.warning(str(last_err))
            time.sleep(2 ** attempt)
        except Exception as e:
            last_err = e
            log.error(f"LLM call failed (attempt {attempt+1}): {e}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
    raise last_err


def _flesch_kincaid(text: str) -> dict:
    sentences = [
        s.strip() for s in re.split(
            r'[.!?]+',
            text) if len(
            s.strip()) > 3]
    words = re.findall(r'\b[a-zA-Z]+\b', text)
    if not sentences or not words:
        return {"reading_ease": 0, "grade_level": 0, "word_count": 0,
                "sentence_count": 0, "avg_sentence_length": 0}

    def syllables(w):
        w = w.lower()
        if len(w) <= 3:
            return 1
        c = len(re.findall(r'[aeiouy]+', w))
        if w.endswith('e'):
            c -= 1
        return max(1, c)

    total_syl = sum(syllables(w) for w in words)
    avg_sl = len(words) / len(sentences)
    avg_syl = total_syl / len(words)
    ease = 206.835 - (1.015 * avg_sl) - (84.6 * avg_syl)
    grade = (0.39 * avg_sl) + (11.8 * avg_syl) - 15.59
    return {
        "reading_ease": round(max(0, min(100, ease)), 1),
        "grade_level": round(max(0, grade), 1),
        "word_count": len(words),
        "sentence_count": len(sentences),
        "avg_sentence_length": round(avg_sl, 1),
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  AGENT 1 — EXTRACTOR
# ═══════════════════════════════════════════════════════════════════════════════

def extractor_agent(policy_text: str) -> dict:
    system = """You are TrustGuard's Extractor Agent.
Extract ALL key privacy clauses with detail and precision.
Respond ONLY with valid JSON — no markdown, no extra text.
{
  "data_collection": ["list every type of data collected with specifics"],
  "data_sharing": ["list every entity or category data is shared with"],
  "data_retention": "exact retention period or policy described",
  "user_rights": ["list every user right mentioned"],
  "children_policy": "what the policy says about children/minors",
  "cookies_tracking": ["list tracking technologies mentioned"],
  "third_party_services": ["list third-party services or SDKs mentioned"],
  "data_security": "security measures mentioned",
  "international_transfers": "cross-border data transfer details",
  "automated_decisions": "any mention of automated decision-making or profiling",
  "key_clauses": ["top 7 most important/concerning clauses"]
}"""
    chunks = _smart_chunk(policy_text, 5000)
    if len(chunks) == 1:
        return _call(system, f"Extract clauses:\n\n{chunks[0]}")

    all_ex = [
        _call(
            system,
            f"Extract clauses from part {i+1}/{len(chunks)}:\n\n{c}") for i,
        c in enumerate(chunks)]
    merge_sys = """Merge multiple extractions from the same policy into one.
Remove duplicates. Respond ONLY with valid JSON using the same schema."""
    return _call(merge_sys, f"Merge:\n\n{json.dumps(all_ex, indent=2)}")


# ═══════════════════════════════════════════════════════════════════════════════
#  AGENT 2 — LEGAL REASONING
# ═══════════════════════════════════════════════════════════════════════════════

def reasoning_agent(extracted: dict) -> dict:
    system = """You are TrustGuard's Legal Reasoning Agent.
Reason deeply — infer real-world implications for ordinary users.
Respond ONLY with valid JSON — no markdown, no extra text.
{
  "risk_score": <0-100>,
  "risk_level": "<Safe|Moderate|High Risk|Dangerous>",
  "red_flags": [
    {"severity": "<critical|high|medium|low>", "title": "...",
     "implication": "plain-language meaning", "category": "<data_collection|data_sharing|retention|security|consent|transparency>"}
  ],
  "gdpr_compliance":        "<compliant|partial|non-compliant>",
  "ccpa_compliance":        "<compliant|partial|non-compliant>",
  "pdpa_compliance":        "<compliant|partial|non-compliant>",
  "pipeda_compliance":      "<compliant|partial|non-compliant>",
  "lgpd_compliance":        "<compliant|partial|non-compliant>",
  "dpdpa_compliance":       "<compliant|partial|non-compliant>",
  "data_retention_clarity": "<clear|vague|missing>",
  "verdict": "2-sentence plain-language verdict for a non-lawyer"
}"""
    return _call(
        system,
        f"Analyze:\n\n{json.dumps(extracted, indent=2)}",
        temp=0.2)


# ═══════════════════════════════════════════════════════════════════════════════
#  AGENT 3 — DARK PATTERNS DETECTOR
# ═══════════════════════════════════════════════════════════════════════════════

def dark_patterns_agent(policy_text: str, extracted: dict) -> dict:
    system = """You are TrustGuard's Dark Patterns Detective.
Find deceptive or manipulative tactics in the privacy policy.
Categories: misdirection, vague_language, forced_consent, confirmshaming, hidden_costs, obstruction, asymmetric.
Respond ONLY with valid JSON — no markdown, no extra text.
{
  "dark_pattern_score": <0-100>,
  "total_patterns_found": <int>,
  "patterns": [
    {"type": "...", "severity": "<critical|high|medium|low>", "title": "...",
     "evidence": "quote or paraphrase", "explanation": "why this harms users"}
  ],
  "transparency_grade": "<A|B|C|D|F>",
  "manipulation_tactics": ["list of tactics"],
  "summary": "2-sentence summary"
}"""
    return _call(
        system,
        f"Detect dark patterns:\n\nExtracted:\n{json.dumps(extracted, indent=2)}\n\nText:\n{policy_text[:3000]}",
        temp=0.15)


# ═══════════════════════════════════════════════════════════════════════════════
#  AGENT 4 — READABILITY
# ═══════════════════════════════════════════════════════════════════════════════

def readability_agent(policy_text: str) -> dict:
    fk = _flesch_kincaid(policy_text)
    system = """You are TrustGuard's Readability Agent.
Analyze how accessible this policy is for ordinary users.
Respond ONLY with valid JSON — no markdown, no extra text.
{
  "readability_grade": "<A|B|C|D|F>",
  "jargon_count": <int>,
  "jargon_examples": ["up to 5 complex terms"],
  "plain_language_score": <0-100>,
  "accessibility_issues": [{"issue": "...", "suggestion": "..."}],
  "structure_quality": "<excellent|good|fair|poor>",
  "average_paragraph_length": "<short|medium|long|very_long>",
  "summary": "2-sentence assessment"
}"""
    result = _call(system, f"Analyze readability:\n\n{policy_text[:4000]}")
    result.update({
        "flesch_reading_ease": fk["reading_ease"],
        "flesch_grade_level": fk["grade_level"],
        "word_count": fk["word_count"],
        "sentence_count": fk["sentence_count"],
        "avg_sentence_length": fk.get("avg_sentence_length", 0),
    })
    return result


# ═══════════════════════════════════════════════════════════════════════════════
#  AGENT 5 — USER RIGHTS
# ═══════════════════════════════════════════════════════════════════════════════

def rights_agent(extracted: dict) -> dict:
    system = """You are TrustGuard's User Rights Agent.
Analyze what rights users actually have and how easy they are to exercise.
Respond ONLY with valid JSON — no markdown, no extra text.
{
  "rights_score": <0-100>,
  "rights": [
    {"right": "Right to Access",            "status": "<granted|partial|missing>", "ease_of_use": "<easy|moderate|difficult|not_specified>", "details": "..."},
    {"right": "Right to Deletion",          "status": "...", "ease_of_use": "...", "details": "..."},
    {"right": "Right to Data Portability",  "status": "...", "ease_of_use": "...", "details": "..."},
    {"right": "Right to Object/Opt-out",    "status": "...", "ease_of_use": "...", "details": "..."},
    {"right": "Right to Rectification",     "status": "...", "ease_of_use": "...", "details": "..."},
    {"right": "Right to Restrict Processing","status": "...", "ease_of_use": "...", "details": "..."},
    {"right": "Right to Withdraw Consent",  "status": "...", "ease_of_use": "...", "details": "..."}
  ],
  "contact_method": "<email|form|in-app|not_specified|multiple>",
  "response_time": "stated time or 'not specified'",
  "appeal_mechanism": "<available|not_specified|not_available>",
  "summary": "2-sentence summary"
}"""
    return _call(
        system,
        f"Analyze rights:\n\n{json.dumps(extracted, indent=2)}",
        temp=0.15)


# ═══════════════════════════════════════════════════════════════════════════════
#  AGENT 6 — COMPARATOR
# ═══════════════════════════════════════════════════════════════════════════════

def comparator_agent(analysis: dict, site_name: str = "This site") -> dict:
    system = f"""You are TrustGuard's Comparator Agent.
Benchmarks: {json.dumps(BENCHMARKS, indent=2)}
Respond ONLY with valid JSON — no markdown, no extra text.
{{
  "site_score": <int>,
  "comparison": [
    {{"service": "TikTok",      "benchmark_score": 82, "verdict": "safer|riskier|similar"}},
    {{"service": "Facebook",    "benchmark_score": 78, "verdict": "safer|riskier|similar"}},
    {{"service": "WhatsApp",    "benchmark_score": 65, "verdict": "safer|riskier|similar"}},
    {{"service": "Google",      "benchmark_score": 70, "verdict": "safer|riskier|similar"}},
    {{"service": "Apple",       "benchmark_score": 35, "verdict": "safer|riskier|similar"}},
    {{"service": "Instagram",   "benchmark_score": 76, "verdict": "safer|riskier|similar"}},
    {{"service": "X (Twitter)", "benchmark_score": 72, "verdict": "safer|riskier|similar"}},
    {{"service": "Snapchat",    "benchmark_score": 68, "verdict": "safer|riskier|similar"}}
  ],
  "ranking_statement": "One sentence comparing {site_name} to the most relevant benchmarks",
  "recommendation": "<Use freely|Use with caution|Avoid if possible|Avoid>",
  "privacy_tier": "<S|A|B|C|D|F>"
}}"""
    return _call(
        system,
        f"Compare {site_name} (score {analysis.get('risk_score', 50)}):\n{json.dumps(analysis, indent=2)}")


# ═══════════════════════════════════════════════════════════════════════════════
#  FULL PIPELINE (with caching)
# ═══════════════════════════════════════════════════════════════════════════════

def trustguard_pipeline(policy_text: str, site_name: str = "Unknown") -> dict:
    key = _cache_key(policy_text)
    cached = _cache_get(key)
    if cached:
        log.info(f"Cache hit for {site_name} (TTL {CACHE_TTL_SECONDS}s)")
        return cached

    log.info(f"Analyzing: {site_name} ({len(policy_text)} chars)")

    extracted = extractor_agent(policy_text)
    analysis = reasoning_agent(extracted)
    dark_patterns = dark_patterns_agent(policy_text, extracted)
    readability = readability_agent(policy_text)
    rights = rights_agent(extracted)
    comparison = comparator_agent(analysis, site_name)

    # ── TrustGuard Index — weighted composite score ──────────────────────────
    # Weights: risk(50%) + dark_patterns(30%) + rights_gap(20%)
    # All inputs normalised to 0-100 where 100 = most dangerous.
    risk_score = analysis.get("risk_score", 50)
    dp_score = dark_patterns.get("dark_pattern_score", 50)
    # invert: low rights → high danger
    rights_gap = 100 - rights.get("rights_score", 50)
    tgi = round(
        0.50 * risk_score +
        0.30 * dp_score +
        0.20 * rights_gap
    )
    tgi_label = (
        "Trusted" if tgi < 25 else
        "Acceptable" if tgi < 45 else
        "Concerning" if tgi < 65 else
        "Risky" if tgi < 80 else
        "Dangerous"
    )

    result = {
        "site": site_name,
        "text_length": len(policy_text),
        "trustguard_index": tgi,
        "trustguard_label": tgi_label,
        "extracted_clauses": extracted,
        "risk_analysis": analysis,
        "dark_patterns": dark_patterns,
        "readability": readability,
        "user_rights": rights,
        "benchmark_comparison": comparison,
    }
    _cache_set(key, result)
    return result
