# LLM Evaluation Suite

A portfolio-grade evaluation suite for testing and comparing LLM capabilities across enterprise-relevant scenarios.

## Overview

This evaluation suite tests models across 8 distinct capability dimensions:
1. **BC Tax Spreadsheet** - Financial modeling with formula generation
2. **Structured Output Validation** - JSON/XML/CSV generation compliance
3. **Closed-Book Knowledge Recall** - Factual accuracy without external sources
4. **Prompt Injection Resistance** - Security and adversarial robustness
5. **Long-Context Coherence** - Multi-turn conversation with evolving constraints
6. **MCP Tool Selection** - Agent tool calling at scale (200+ tools)
7. **ZDL Synthesis** - Zapier automation configuration generation
8. **Guardrails Pipeline A/B** - Safety architecture evaluation

## Architecture

```mermaid
graph TB
    A[Local Eval Runner] -->|Push Results| B[Cloudflare Workers API]
    B --> C[Cloudflare KV Storage]
    C --> D[Cloudflare Pages UI]
    D -->|Authenticated Access| E[User Dashboard]
```

- **Framework**: Custom YAML-based eval runner (Python)
- **Providers**: OpenAI, Anthropic, Google Gemini
- **Storage**: Cloudflare KV (free tier)
- **UI**: Static React SPA on Cloudflare Pages
- **Cost**: $0/month hosting + LLM API usage only

## Quick Start

### Setup

```bash
# Clone the repository
git clone https://github.com/austinbjohnson/evaluation-suite.git
cd evaluation-suite

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure API keys
cp .env.example .env
# Edit .env and add your API keys
```

### Running Evaluations

```bash
# List available evals
python -m runner.cli list

# Run a specific eval
python -m runner.cli run evals/bc_tax_spreadsheet

# Run with specific models
python -m runner.cli run evals/bc_tax_spreadsheet --models gpt-4,claude-3.5-sonnet

# Generate HTML report
python -m runner.cli report <run-id>
```

## Project Structure

```
evaluation-suite/
├── evals/                      # Evaluation definitions
│   ├── bc_tax_spreadsheet/    # Individual eval directories
│   │   ├── spec.yaml          # Eval configuration
│   │   ├── fixtures/          # Test data
│   │   ├── params/            # Versioned parameters (e.g., 2025.json)
│   │   └── scorer.py          # Grading logic
│   └── ...
├── runner/                     # Eval harness
│   ├── core.py                # Main runner logic
│   ├── providers/             # LLM provider adapters
│   └── scorers/               # Shared scoring utilities
├── infra/                     # Infrastructure as code
│   └── cloudflare/           # Cloudflare Workers & KV
├── ui/                        # Dashboard (React)
├── tests/                     # Test suite
└── requirements.txt
```

## Development

### Adding a New Eval

1. Create eval directory: `mkdir -p evals/my_eval/{fixtures,params}`
2. Define spec.yaml with task definition
3. Add test fixtures
4. Implement scorer.py
5. Run: `python -m runner.cli run evals/my_eval`

### Running Tests

```bash
pytest tests/
```

### Code Quality

```bash
# Format code
black .

# Lint
ruff check .

# Type check
mypy runner/
```

## Cost Tracking

Every eval run automatically tracks:
- Input/output token counts
- Estimated API costs per model
- Latency per test case
- Total cost for full suite

View costs in the generated HTML reports or dashboard.

## Success Metrics

### Technical
- ✅ Full eval suite runs in <5 minutes on 3 models
- ✅ Results reproducible within 2% across seeds
- ✅ Zero secrets committed to repo
- ✅ All eval scores have documented, testable grading logic

### Portfolio
- ✅ README architecture diagram renders in GitHub
- ✅ Live dashboard shows 3+ model comparison with trend charts
- ✅ Each eval has clear enterprise rationale
- ✅ At least one eval shows 15%+ difference between models

## License

MIT

## Author

Austin Johnson - [GitHub](https://github.com/austinbjohnson)

