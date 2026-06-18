# 🛡️ TrustGuard AI

**Multi-Agent Privacy Policy Analyzer** — Built for the [Agents League Hackathon](https://aka.ms/AgentsLeagueRules) · Microsoft Foundry · Reasoning Agents Track

> *"No one reads privacy policies. TrustGuard does."*

---

## 🏆 What it does

TrustGuard AI deploys **6 specialized AI agents** in a sequential reasoning pipeline to analyze any privacy policy or Terms of Service — and benchmark it against TikTok, Facebook, WhatsApp, and more.

| Agent | Role |
|-------|------|
| 🔍 **Extractor** | Parses every clause: data collection, sharing, retention, rights |
| ⚖️ **Legal Reasoner** | Infers real-world implications — not just summaries |
| 🕵️ **Dark Patterns Detector** | Finds manipulative tactics (vague language, forced consent, obstruction) |
| 📖 **Readability Analyzer** | Flesch-Kincaid + AI grading — how understandable is this policy? |
| 🧾 **User Rights Auditor** | Checks 7 rights (access, deletion, portability…) and how easy they are to exercise |
| 📊 **Comparator** | **Policy DNA™** — benchmarks the site against 8 major platforms |

---

## ✨ Key Features

- **Policy DNA™ Benchmark** — "This site is 23% riskier than TikTok" — nothing else does this
- **Change Tracker** — detects silent policy updates between visits  
- **6-Framework Compliance** — GDPR · CCPA · PDPA · PIPEDA · LGPD · DPDPA  
- **PDF Export** — professional downloadable report  
- **URL or text input** — analyze any site instantly  
- **Retry logic + in-memory caching** — fast and resilient

---

## 🏗️ Architecture

```
User Input (URL or text)
        │
        ▼
┌───────────────────────────────────────────────────────┐
│                  TrustGuard Pipeline                  │
│                                                       │
│  [Agent 1]        [Agent 2]        [Agent 3]          │
│  Extractor   →   Legal Reasoner  → Dark Patterns      │
│                                                       │
│  [Agent 4]        [Agent 5]        [Agent 6]          │
│  Readability  →   Rights Auditor → Comparator         │
│                                                       │
│  + Change Tracker (SHA-256 diff between visits)       │
└───────────────────────────────────────────────────────┘
        │
        ▼
  Tabbed Dashboard + PDF Report
```

---

## 🚀 Quick Start

### 1. Clone & install

```bash
git clone https://github.com/YOUR_USERNAME/trustguard-ai.git
cd trustguard-ai
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your Azure Foundry credentials
```

### 3. Run

```bash
python app.py
# Open http://localhost:5000
```

---

## ⚙️ Configuration

Copy `.env.example` to `.env` and fill in:

```env
AZURE_ENDPOINT=https://your-resource.services.ai.azure.com/
AZURE_API_KEY=your-api-key-here
DEPLOYMENT_NAME=gpt-5.4
```

---

## 🔧 Tech Stack

| Layer | Technology |
|-------|-----------|
| AI Agents | Azure AI Foundry · GPT-5.4 |
| Backend | Python · Flask · fpdf2 |
| Frontend | Vanilla JS · HTML/CSS |
| Policy Fetching | BeautifulSoup4 · requests |
| Readability | Flesch-Kincaid (local) + AI grading |

---

## 📁 Project Structure

```
trustguard-ai/
├── agents.py           # 6 AI agents + pipeline
├── app.py              # Flask backend + PDF export + rate limiting
├── templates/
│   └── index.html      # Full tabbed dashboard
├── requirements.txt
├── .env.example
└── policy_history.json # Change tracker database
```

---

## 🎯 Why TrustGuard wins

1. **Real reasoning, not summarizing** — agents infer what clauses *actually mean* for users
2. **Policy DNA™** — world's first cross-platform privacy benchmark comparison
3. **Dark patterns detection** — finds manipulation tactics no other tool catches
4. **6-law compliance** — covers GDPR, CCPA, PDPA, PIPEDA, LGPD, DPDPA simultaneously
5. **Change tracking** — silent policy updates are a real threat; we catch them

---
## 📺 Demo Video

https://github.com/user-attachments/assets/7b26619c-3c1d-4183-b567-44622f12f195

---

## 📄 License

This project is licensed under the [PolyForm Noncommercial License 1.0.0](LICENSE).

You're free to use, study, modify, and share this code for personal, educational, or research purposes. **Commercial use is not permitted without prior written permission** from the author (Abd.moh9999@yahoo.com).


---

*TrustGuard AI — Because privacy policies shouldn't require a law degree.*
