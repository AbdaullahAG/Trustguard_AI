<div align="center">

<!-- Animated Header -->

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0F172A,50:1E3A8A,100:00F0FF&height=180&section=header&text=TrustGuard%20AI&fontSize=48&fontColor=ffffff&animation=fadeIn&fontAlignY=35&desc=Multi-Agent%20Privacy%20Policy%20Analyzer&descAlignY=55&descSize=16" alt="TrustGuard AI Header" />

<!-- Typing Animation -->

<a href="https://github.com/AbdaullahAG/trustguard-ai">
  <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=22&pause=1200&color=00F0FF&center=true&vCenter=true&width=700&height=50&lines=No+one+reads+privacy+policies.;TrustGuard+does.;6+Specialized+AI+Agents;Policy+DNA%E2%84%A2+Benchmark;Built+for+Agents+League+Hackathon" alt="Typing SVG" />
</a>

<br/>

<!-- Badges -->

<p>
  <img src="https://img.shields.io/badge/Agents%20League-Reasoning%20Agents%20Track-00F0FF?style=for-the-badge&logo=microsoft&logoColor=white" alt="Agents League" />
  <img src="https://img.shields.io/badge/Microsoft%20Foundry-Powered-0078D4?style=for-the-badge&logo=microsoftazure&logoColor=white" alt="Microsoft Foundry" />
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/License-PolyForm%20Noncommercial-red?style=for-the-badge" alt="License" />
</p>

<p>
  <a href="https://github.com/AbdaullahAG/trustguard-ai/stargazers">
    <img src="https://img.shields.io/github/stars/AbdaullahAG/trustguard-ai?style=social" alt="Stars" />
  </a>
  <a href="https://github.com/AbdaullahAG/trustguard-ai/network/members">
    <img src="https://img.shields.io/github/forks/AbdaullahAG/trustguard-ai?style=social" alt="Forks" />
  </a>
  <img src="https://visitor-badge.laobi.icu/badge?page_id=AbdaullahAG.trustguard-ai&left_color=gray&right_color=00F0FF" alt="Visitors" />
</p>

</div>

---

## 🛡️ What is TrustGuard AI?

**TrustGuard AI** is a multi-agent privacy policy analyzer built for the [Agents League Hackathon](https://aka.ms/AgentsLeagueRules) (Microsoft Foundry · Reasoning Agents Track).

It deploys **6 specialized AI agents** in a sequential reasoning pipeline to deeply analyze any privacy policy or Terms of Service — then benchmarks it against major platforms like TikTok, Facebook, WhatsApp, and more.

> *"No one reads privacy policies. TrustGuard does."*

---

## 🏆 The 6 Specialized Agents

| Agent                          | Role                     | Superpower                                       |
| ------------------------------ | ------------------------ | ------------------------------------------------ |
| 🔍 **Extractor**               | Parses every clause      | Data collection, sharing, retention, rights      |
| ⚖️ **Legal Reasoner**          | Infers real-world impact | Goes beyond summaries → actual consequences      |
| 🕵️ **Dark Patterns Detector** | Finds manipulation       | Vague language, forced consent, obstruction      |
| 📖 **Readability Analyzer**    | Grades understandability | Flesch-Kincaid + AI scoring                      |
| 🧾 **User Rights Auditor**     | Checks 7 core rights     | Access, deletion, portability & ease of exercise |
| 📊 **Comparator**              | Policy DNA™              | Benchmarks against 8 major platforms             |

---

## ✨ Key Features

| Feature                        | Description                                                               |
| ------------------------------ | ------------------------------------------------------------------------- |
| **🧬 Policy DNA™ Benchmark**   | "This site is 23% riskier than TikTok" — unique cross-platform comparison |
| **🔄 Change Tracker**          | Detects silent policy updates using SHA-256 diffs                         |
| **📜 6-Framework Compliance**  | GDPR · CCPA · PDPA · PIPEDA · LGPD · DPDPA                                |
| **📄 Professional PDF Export** | Clean, downloadable analysis report                                       |
| **⚡ Instant Analysis**         | URL or raw text input                                                     |
| **🛡️ Resilient Pipeline**     | Retry logic + in-memory caching                                           |

---

## 🏗️ Architecture

```text
User Input (URL or Text)
           │
           ▼
┌────────────────────────────────────────────────────────────┐
│                  TrustGuard Pipeline                       │
│                                                            │
│   [1] Extractor  →  [2] Legal Reasoner  →  [3] Dark       │
│                                           Patterns          │
│                                                            │
│   [4] Readability →  [5] Rights Auditor →  [6] Comparator │
│                                                            │
│          + Change Tracker (SHA-256 history)                │
└────────────────────────────────────────────────────────────┘
           │
           ▼
    Tabbed Dashboard + PDF Report
```

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/AbdaullahAG/trustguard-ai.git
cd trustguard-ai

python -m venv venv

# Linux / macOS
source venv/bin/activate

# Windows
venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Add your Azure AI Foundry credentials to `.env`.

### 3. Run

```bash
python app.py
```

Then open:

```text
http://localhost:5000
```

---

## ⚙️ Configuration

Create a `.env` file:

```env
AZURE_ENDPOINT=https://your-resource.services.ai.azure.com/
AZURE_API_KEY=your-api-key-here
DEPLOYMENT_NAME=gpt-5.4
```

> **Note:** Never commit your `.env` file or API keys to GitHub.

---

## 🔧 Tech Stack

| Layer                | Technology                      |
| -------------------- | ------------------------------- |
| **AI Agents**        | Azure AI Foundry · GPT-5.4      |
| **Backend**          | Python · Flask · fpdf2          |
| **Frontend**         | Vanilla JavaScript · HTML · CSS |
| **Policy Fetching**  | BeautifulSoup4 · Requests       |
| **Readability**      | Flesch-Kincaid + AI grading     |
| **Change Detection** | SHA-256                         |
| **Deployment**       | Python / Flask                  |

---

## 📁 Project Structure

```text
trustguard-ai/
├── agents.py              # 6 AI agents + sequential pipeline
├── app.py                 # Flask backend + PDF export + rate limiting
├── templates/
│   └── index.html         # Full tabbed dashboard
├── requirements.txt       # Python dependencies
├── .env.example           # Environment configuration template
└── policy_history.json    # Change tracker database
```

---

## 🎯 Why TrustGuard Wins

1. **Real reasoning, not summarizing**
   Agents infer what clauses *actually mean* for users instead of simply generating summaries.

2. **Policy DNA™**
   A cross-platform privacy benchmark that provides a comparative view of how risky a policy is.

3. **Dark patterns detection**
   Identifies manipulative privacy practices, vague language, forced consent, and barriers to exercising user rights.

4. **6-law simultaneous compliance**
   Evaluates policies against GDPR, CCPA, PDPA, PIPEDA, LGPD, and DPDPA.

5. **Silent change tracking**
   Detects policy updates using SHA-256-based document comparison.

---

## 📊 Analysis Pipeline

TrustGuard processes a privacy policy through six specialized reasoning stages:

```text
                    Privacy Policy
                           │
                           ▼
                  ┌─────────────────┐
                  │    Extractor    │
                  └────────┬────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │   Legal Reasoner    │
                └──────────┬──────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │   Dark Patterns Agent   │
              └────────────┬────────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │  Readability Analyzer   │
              └────────────┬────────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │    Rights Auditor       │
              └────────────┬────────────┘
                           │
                           ▼
                 ┌──────────────────┐
                 │    Comparator    │
                 └────────┬─────────┘
                          │
                          ▼
                ┌──────────────────┐
                │   Final Report   │
                └──────────────────┘
```

---

## 📺 Demo Video

<div align="center">

<a href="https://github.com/user-attachments/assets/7b26619c-3c1d-4183-b567-44622f12f195">
  <img src="https://img.shields.io/badge/▶_Watch_Demo-00F0FF?style=for-the-badge&logo=youtube&logoColor=white" alt="Watch Demo" />
</a>

</div>

---

## 🏅 Built for the Agents League Hackathon

TrustGuard AI was designed for the **Agents League Hackathon**, specifically targeting the **Reasoning Agents Track** and leveraging **Microsoft Foundry** to orchestrate specialized AI agents.

The project focuses on demonstrating how multi-agent reasoning can transform complex privacy policies into actionable, understandable privacy intelligence.

---

## 🔐 Privacy & Security

TrustGuard is designed with privacy and security in mind:

* API credentials are loaded through environment variables.
* `.env` files should never be committed to version control.
* Policy change detection uses SHA-256 hashing.
* The analysis pipeline uses resilient retry mechanisms.
* Policy content is processed through specialized analysis stages rather than relying on a single monolithic prompt.

---

## 📄 License

This project is licensed under the **PolyForm Noncommercial License 1.0.0**.

You are free to use, study, modify, and share this code for **personal, educational, or research purposes**.

**Commercial use is not permitted** without prior written permission from the author:

**Abdallah Abughallous**
📧 [abd.moh9999@yahoo.com](mailto:abd.moh9999@yahoo.com)

---

<div align="center">

**TrustGuard AI** — *Because privacy policies shouldn't require a law degree.*

<br/>

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:00F0FF,50:1E3A8A,100:0F172A&height=100&section=footer" alt="Footer" />

</div>
