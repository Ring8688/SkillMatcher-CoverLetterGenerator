# Skill Matcher and Cover Letter Generator

A config-driven Streamlit app that matches your resume with job postings and generates tailored cover letters. Works with any OpenAI-compatible LLM API.

<p align="center">
  <img src="images/image1.png" alt="demo image" width="450"/>
  <img src="images/image2.png" alt="demo image2" width="450"/>
  <img src="images/image3.png" alt="demo image3" width="450"/>
</p>

## Features

- Paste a job URL or job description text to extract job details
- Match your resume against job requirements with skill gap analysis
- Generate and download personalized cover letters as PDF
- Upload PDF/MD documents via sidebar — auto-discovered by the app
- All prompts and profile data are config-driven (no hardcoded data)
- Supports any OpenAI-compatible API (OpenRouter, Claude proxy, local LLMs, etc.)

## Project Structure

```
├── app.py                 # Streamlit UI (sidebar upload, job input, cover letter)
├── chains.py              # LLM chains (prompts loaded from config.yml)
├── config_loader.py       # Config loading + validation
├── profile_data.py        # Resume data loading with auto-discovery
├── utils.py               # Text extraction (PDF/MD), PDF generation
├── config.yml.example     # Config template (profile, prompts, resources)
├── .env.example           # API env vars template
├── dockerfile             # Docker image build
├── docker-compose.yml     # Local dev compose
├── deploy.sh              # Build & push to Docker Hub (ARM64)
├── deploy/                # Cloud deployment templates (git-ignored)
│   ├── docker-compose.yml
│   ├── .env.example
│   └── config.yml.example
└── data/                  # Resume/document files (git-ignored)
```

## Quick Start

### 1. Clone & configure

```bash
git clone https://github.com/Ring8688/SkillMatcher-CoverLetterGenerator.git
cd SkillMatcher-CoverLetterGenerator

cp config.yml.example config.yml   # Fill in your personal info & prompts
cp .env.example .env               # Fill in your API key & endpoint
```

### 2. Add your resume files

Place your `.pdf` or `.md` files in the `data/` directory:

```bash
mkdir -p data
cp /path/to/your/cv.md data/
```

Update `config.yml` resources section to point to your files, or simply drop them in `data/` — they will be auto-discovered.

### 3. Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Or with Docker:

```bash
docker compose up --build
```

App runs at `http://localhost:8501`.

## Configuration

### `.env` — API settings

```env
API_BASE_URL=https://openrouter.ai/api/v1
API_KEY=your-api-key-here
API_MODEL=gpt-4o
API_TEMPERATURE=0
```

### `config.yml` — Profile & prompts

Key sections:

| Section | Description |
|---------|-------------|
| `personal` | Name, email, phone, location |
| `links` | LinkedIn, portfolio, GitHub |
| `education` | University, degree, GPA |
| `experience` | Current role, tech stack, summary |
| `resources` | Explicit list of resume files to load |
| `cover_letter` | Value propositions, tone, max words |
| `prompts` | 4 LLM prompt templates (extract_jobs, write_match, extract_personal_info, cover_letter) |
| `app` | UI title, caption, default job URL |

## Cloud Deployment (Docker)

### Build & push image

```bash
./deploy.sh   # Builds linux/arm64 → ring8688/jasper-server:coverlettertool
```

### Deploy on cloud server

```bash
mkdir -p ~/coverlettertool/data
cd ~/coverlettertool

# Copy templates from deploy/ directory and fill in your values
cp .env.example .env
cp config.yml.example config.yml

# Add resume files to data/

docker compose pull
docker compose up -d
```

The `deploy/` directory contains ready-to-use templates with cloud networking (external `cloud_net` network).

Single Docker mount: `./data:/app/data` — uploaded files persist across container restarts.

## Tech Stack

- **Frontend**: Streamlit
- **LLM**: LangChain + any OpenAI-compatible API
- **PDF**: PyPDF (reading), FPDF (generation)
- **Config**: YAML + python-dotenv
- **Deploy**: Docker (ARM64), Docker Compose
