"""
TrustGuard AI — Unit tests for pure-local functions (no Azure API needed).
Run: pytest tests/test_local.py -v
"""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("AZURE_ENDPOINT",  "https://placeholder.openai.azure.com/")
os.environ.setdefault("AZURE_API_KEY",   "placeholder")
os.environ.setdefault("DEPLOYMENT_NAME", "gpt-5.4")

from agents import (
    _smart_chunk, _flesch_kincaid,
    _cache_key, _cache_get, _cache_set, cache_clear,
    CACHE_TTL_SECONDS,
)


# ── _smart_chunk ──────────────────────────────────────────────────────────────

def test_chunk_short_no_split():
    chunks = _smart_chunk("Short text.", max_chars=500)
    assert len(chunks) == 1

def test_chunk_long_splits():
    para = "Data privacy collection sharing. " * 10
    text = "\n\n".join([para] * 5)
    chunks = _smart_chunk(text, max_chars=200)
    assert len(chunks) > 1

def test_chunk_at_limit():
    assert len(_smart_chunk("A" * 500, max_chars=500)) == 1

def test_chunk_each_within_limit():
    para = "Word " * 50
    text = "\n\n".join([para] * 20)
    for chunk in _smart_chunk(text, max_chars=400):
        assert len(chunk) <= 900  # overlap window adds up to 500 extra chars


# ── _flesch_kincaid ───────────────────────────────────────────────────────────

def test_fk_keys():
    r = _flesch_kincaid("Simple test. We collect data.")
    for k in ["reading_ease", "grade_level", "word_count", "sentence_count"]:
        assert k in r

def test_fk_bounded():
    r = _flesch_kincaid("Hello world. Simple text.")
    assert 0 <= r["reading_ease"] <= 100

def test_fk_word_count():
    assert _flesch_kincaid("One two three four five.")["word_count"] == 5

def test_fk_empty():
    r = _flesch_kincaid("")
    assert r["word_count"] == 0 and r["reading_ease"] == 0

def test_fk_legal_harder_than_simple():
    simple = _flesch_kincaid("We use your data. You can delete it.")
    legal  = _flesch_kincaid(
        "Notwithstanding any aforementioned provisions, the data controller shall "
        "implement appropriate pseudonymization measures pursuant to Article 32 of "
        "the General Data Protection Regulation concerning organizational obligations."
    )
    assert legal["grade_level"] >= simple["grade_level"]


# ── _cache_key ────────────────────────────────────────────────────────────────

def test_cache_key_sha256():
    key = _cache_key("test")
    assert len(key) == 64
    assert all(c in "0123456789abcdef" for c in key)

def test_cache_key_deterministic():
    assert _cache_key("same") == _cache_key("same")

def test_cache_key_unique():
    assert _cache_key("aaa") != _cache_key("bbb")

def test_cache_key_first_6000():
    base = "A" * 6000
    assert _cache_key(base + "B" * 500) == _cache_key(base + "C" * 500)


# ── TTL Cache ─────────────────────────────────────────────────────────────────

def test_cache_set_get():
    cache_clear()
    k = _cache_key("policy-abc")
    _cache_set(k, {"risk_score": 42})
    assert _cache_get(k) == {"risk_score": 42}

def test_cache_miss():
    cache_clear()
    assert _cache_get("ghost-key") is None

def test_cache_clear_works():
    _cache_set(_cache_key("x"), {"v": 1})
    cache_clear()
    assert _cache_get(_cache_key("x")) is None

def test_cache_ttl_expiry(monkeypatch):
    cache_clear()
    k = _cache_key("ttl-policy")
    _cache_set(k, {"risk_score": 99})
    future = time.time() + CACHE_TTL_SECONDS + 10
    monkeypatch.setattr("agents.time.time", lambda: future)
    assert _cache_get(k) is None
