# 📨 Opportunity Inbox Copilot

**An intelligent, AI-powered inbox filtering system designed to rescue students from the noise of irrelevant internship, scholarship, and fellowship emails.** 

Built for the **SOFTEC 2026 AI Hackathon**, the Opportunity Inbox Copilot natively understands unstructured opportunity emails, categorizes them, extracts exact requirements, ranks them against an individualized student profile, and synthesizes them into actionable insights using GPT-4o.

---

## 🌟 Key Features

* **💅 Gmail-Inspired UI**: A clean, modern, high-contrast Material You design system built entirely over Streamlit.
* **🧠 Smart Heuristic Pipeline**: Fast, purely offline extraction engines that parse raw email noise into structured entities (Deadlines, Stipends, Organizations) using regex and NLP heuristics without relying on expensive API calls for every email.
* **🎯 Dynamic Profile Ranking**: Analyzes opportunities against your *current* specific context (Major, CGPA, Target Location, Financial Need). If an opportunity falls below a **50% strict Match Score limit**, it is automatically dumped into Spam.
* **✨ AI Strategic Summaries**: Generates concise, 5-bullet tactical overviews summarizing the strategic logic of why an opportunity matches you utilizing the **GitHub Models API (OpenAI GPT-4o)** model.
* **📂 Smart Classification**: Automatically segregates your raw inbox feed into clean **Inbox**, **Opportunities**, and **Spam** lists based on calculated metrics and spam-keyword heuristics.
* **🗄️ Persistent Local Storage**: Fast and lightweight local data persistence using SQLite3 to maintain inbox views, profile configurations, and parsed artifacts across sessions.

---

## 🛠️ Technology Stack

* **Frontend**: Python / Streamlit (Injected with custom CSS matching modern web standards)
* **Backend AI**: OpenAI Python SDK routing to `https://models.github.ai/inference` (`gpt-4o`)
* **Database**: Embedded SQLite3
* **Environment**: `python-dotenv`

---

## 🚀 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd AI-Hackathon
   ```

2. **Create a virtual environment & install dependencies:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install streamlit openai python-dotenv
   ```

3. **Configure Environment Variables:**
   Create a `.env` file in the root directory and add a valid GitHub Personal Access Token (for the GitHub Models inference API).
   ```text
   GITHUB_TOKEN=ghp_your_actual_github_token_here
   ```

4. **Run the Application:**
   ```bash
   streamlit run app.py
   ```

---

## 💡 How It Works (The Pipeline)

1. **Import:** You paste or upload raw text emails into the *Import* tab. They land in your Pending Inbox.
2. **Setup:** You configure your background in the left sidebar (Degree, Major, Semester, CGPA, Location, Preferred Roles).
3. **Execution:** Hitting "Find Opportunities" triggers the `run_pipeline` engine:
    * **Classifier:** Scans for hard spam keywords (sales, promos) vs opportunity keywords.
    * **Extractor:** If an opportunity, mines unstructured text for exact rules, documents, dates, and locations.
    * **Ranker:** Compares the extracted data strictly against the user's Profile Configuration. Generates 6 metrics: Final Score, Match Score, Urgency, Preference, Completeness, and Value.
    * **Spam Threshold Filter:** If the Final Score is `< 50%`, the email is rejected as noise and sent to Spam.
    * **Summarizer:** Surviving top-tier emails are sent to GPT-4o for rapid tactical summarization.

---

## 📁 Project Architecture

```text
├── app.py                     # Main Streamlit Frontend Application
├── .env                       # Environment configurations
├── database/
│   └── db.py                  # SQLite CRUD handlers & Schemas
├── controller/
│   └── pipeline.py            # Core engine that bridges UI with models
├── models/
│   └── schemas.py             # Dataclass definitions (Opportunity, Profile)
├── modules/
│   ├── classifier.py          # Heuristic keyword categorizer
│   ├── extractor.py           # Regex-based data miner for unstructured text
│   ├── normalizer.py          # Value formatting and standardizing 
│   ├── explainer.py           # Checklist & Logic generation
│   └── ranker.py              # Profile vs Opportunity algorithmic comparison
└── utils/
    ├── github_openai_client.py   # Wrapper for the github.ai GPT-4o API 
    └── summarizer.py          # GPT-4o prompt builder for the UI summaries
```

---

## 👥 Team

* **Uzair Majeed** — 23i-3063
* **Rizwan Saeed** — 23i-3009
* **Zaki Haider** — 23i-3091

---
*Created for SOFTEC 2026.*
