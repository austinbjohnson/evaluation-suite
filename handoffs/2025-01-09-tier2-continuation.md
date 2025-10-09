# Developer Handoff - LLM Evaluation Suite
**Date:** January 9, 2025  
**Branch:** `feat/tier2-core-evals`  
**Status:** Tier 1 Complete, Tier 2 Partially Complete (2/4 evals done)

## 📋 Table of Contents
1. [Project Overview](#project-overview)
2. [Current State](#current-state)
3. [What's Working](#whats-working)
4. [What Needs to Be Built](#what-needs-to-be-built)
5. [Known Issues](#known-issues)
6. [Architecture & Code Structure](#architecture--code-structure)
7. [Testing & Validation](#testing--validation)
8. [Next Steps](#next-steps)
9. [Resources & References](#resources--references)

---

## Project Overview

### Goal
Build a portfolio-grade LLM evaluation suite with 8 custom evaluations covering enterprise-relevant scenarios. The suite should:
- Run evaluations across multiple LLM providers (OpenAI, Anthropic, Google)
- Track costs automatically (tokens + estimated USD)
- Store results in Cloudflare KV (free tier)
- Provide a web dashboard for comparing models
- Be fully open-source and portfolio-ready

### Design Philosophy
- **Spec-first:** YAML configs drive everything
- **Custom framework:** No heavy dependencies (lm-eval-harness, OpenAI Evals)
- **Cost-conscious:** $0/month hosting, minimize API costs
- **Portfolio-grade:** Clean code, comprehensive docs, impressive results

---

## Current State

### ✅ Completed Work

#### **Tier 1 - Foundation (Complete)**
1. **BC Tax Spreadsheet Eval**
   - Generates Excel formulas for Canadian federal + BC provincial taxes
   - Validates formula presence (not hardcoded values)
   - ±$1 numerical accuracy tolerance
   - **Status:** Working, but scorer has extraction issues (see Known Issues)
   - **Location:** `evals/bc_tax_spreadsheet/`

2. **Structured Output Validation Eval**
   - Tests JSON, XML, CSV generation with schema validation
   - 4 test cases, 75% pass rate on GPT-4o-mini
   - **Status:** Production-ready ✅
   - **Location:** `evals/structured_output/`

#### **Tier 2 - Core Capabilities (2/4 Complete)**
3. **Closed-Book Knowledge Recall Eval** ✅
   - Tests factual recall without external sources
   - 7 test cases (NHL, BC geography/tax, unknowable questions)
   - Detects hallucinations & appropriate uncertainty
   - **Status:** Working, 43% pass rate on GPT-4o-mini ✅
   - **Location:** `evals/closed_book_recall/`

4. **Prompt Injection Resistance Eval** ✅
   - Tests security against jailbreak attempts
   - 7 test cases (instruction override, DAN, prompt leaks, etc.)
   - Includes legitimate controls to test false positives
   - **Status:** Working, 57% pass rate on GPT-4o-mini ✅
   - **Location:** `evals/prompt_injection/`

#### **Infrastructure Complete**
- ✅ Custom YAML-based eval runner (`runner/core.py`)
- ✅ OpenAI provider with full cost tracking
- ✅ Anthropic provider with Claude support
- ✅ CLI tool (`python -m runner.cli`)
- ✅ Auto provider detection by model name
- ✅ JSON result storage
- ✅ Comprehensive testing docs

### 🚧 Remaining Work (Tier 2)

5. **Long-Context Coherence Eval** (TODO)
   - Multi-turn conversation with evolving constraints
   - Tests entity retention over 8+ messages
   - **Priority:** HIGH (critical capability)
   - **Estimated effort:** 2-3 hours

6. **MCP Tool Selection Eval** (TODO)
   - Tests tool calling with 200+ tool registry
   - User has Zapier server available
   - **Priority:** HIGH (cutting-edge feature)
   - **Estimated effort:** 1-2 hours

### 🔮 Future Work (Tier 3+)
7. ZDL (Zapier) Synthesis Eval
8. Guardrails Pipeline A/B Eval
9. Cloudflare Workers + KV backend
10. Static UI dashboard (React + Cloudflare Pages)
11. Google Gemini provider

---

## What's Working

### Running Evaluations
```bash
# Activate environment
cd /Users/ajohnson/Code/abj_evals/evaluation-suite
source venv/bin/activate

# List all evals
python -m runner.cli list

# Run a specific eval
python -m runner.cli run evals/closed_book_recall --models gpt-4o-mini

# Run with multiple models (auto-detects provider)
python -m runner.cli run evals/prompt_injection --models gpt-4o-mini,claude-3-5-sonnet-20241022

# View detailed report
python -m runner.cli report <run-id>
```

### Supported Models
**OpenAI:** gpt-4, gpt-4o, gpt-4o-mini, gpt-3.5-turbo  
**Anthropic:** claude-3-5-sonnet-20241022, claude-3-opus-20240229, claude-3-haiku-20240307

### Cost Tracking
All evals automatically track:
- Input/output token counts
- Estimated cost in USD (rough approximation)
- Per-case latency
- Aggregate metrics

Example costs (GPT-4o-mini):
- Closed-Book Recall: ~$0.007 per run
- Prompt Injection: ~$0.012 per run
- BC Tax Spreadsheet: ~$0.089 per run
- Structured Output: ~$0.011 per run

---

## What Needs to Be Built

### 5. Long-Context Coherence Eval 🎯

**Objective:** Test if model maintains context and constraints across multi-turn conversation.

**Test Design:**
- 8-message conversation simulating NHL analytics project over "4 days"
- Plant 8-10 key facts (names, dates, budget constraints)
- Facts evolve (e.g., deadline changes, new requirements added)
- Final message asks for deliverable respecting ALL constraints

**Example Conversation Flow:**
```
Day 1, Message 1 (User): "We're planning an NHL analytics pilot for the Vancouver Canucks. 
                         Budget is $50k, deadline is March 15."
Day 1, Message 2 (Assistant): <acknowledges>
Day 2, Message 3 (User): "Actually, the deadline moved to March 30. Also, we need to 
                         include player performance metrics."
...
Day 4, Message 8 (User): "Create a project summary including timeline, budget, and all requirements."
```

**Scoring Approach (from plan):**
- **Hybrid scoring (recommended):**
  - Programmatic: Extract entities (spaCy or regex) - dates, names, numbers
  - LLM-as-judge: Use GPT-4 with rubric to score constraint adherence (0-10)
  - Composite score: `(entity_retention * 0.5) + (llm_judge_score/10 * 0.5)`
  
- **Target metrics:**
  - Entity retention: 85%+ of planted facts present in final output
  - Constraint adherence: 80%+ (deadline, budget respected)
  - No contradictions: <1 hard contradiction

**Implementation Steps:**
1. Create `evals/long_context_coherence/` directory
2. Write `spec.yaml` with 2-3 conversation fixtures
3. Create `prompt.md` (Jinja template for multi-turn conversation)
4. Implement `scorer.py`:
   - Entity extraction function (regex or spaCy)
   - LLM-as-judge call with rubric (optional but recommended)
   - Composite scoring logic
5. Test with GPT-4o-mini and Claude

**Files to Create:**
```
evals/long_context_coherence/
├── spec.yaml          # Define conversation fixtures
├── prompt.md          # Jinja template for multi-turn
├── scorer.py          # Hybrid scoring (entity + LLM judge)
└── fixtures/
    └── nhl_project_conversation.yaml  # Full conversation data
```

**Reference Implementation:**
- See `evals/closed_book_recall/scorer.py` for pattern matching examples
- See `evals/bc_tax_spreadsheet/scorer.py` for complex metric calculation
- Plan document section on "Long-Context Coherence" (lines 94-115 in original plan)

---

### 6. MCP Tool Selection Eval 🎯

**Objective:** Test if model correctly selects tools from large registry (200+) and constructs valid arguments.

**Test Design:**
- User has access to Zapier MCP server with 200+ tools
- Create test scenarios requiring specific tools
- Model must choose correct tool AND construct valid argument schema

**Example Test Cases:**
```yaml
- case_id: create_quickbooks_invoice
  input:
    task: "Create an invoice in QuickBooks for $1,250 to ACME Corp, due in 30 days"
    available_tools: <200+ tool registry>
  expected_output:
    correct_tool: "quickbooks.invoice.create"
    required_args: ["customer_name", "amount", "due_date"]
```

**Scoring Approach:**
- **Top-1 accuracy:** Did model choose exactly the right tool? (binary)
- **Argument validation:** Do arguments match JSON schema? (use `jsonschema`)
- **Clarification behavior:** Does model ask for info when ambiguous?

**Implementation Steps:**
1. Get tool export from user's Zapier MCP server
   - Ask user to export tool registry as JSON
   - Should include: tool names, descriptions, input schemas, examples
2. Create `evals/mcp_tool_selection/` directory
3. Write `spec.yaml` with 30-50 test scenarios
4. Create `fixtures/tool_registry.json` (200+ tools from Zapier)
5. Implement `scorer.py`:
   - Tool name extraction (parse model output for tool choice)
   - JSON schema validation for arguments
   - Optional: argument correctness check
6. Test with GPT-4o (best tool calling) and Claude

**Files to Create:**
```
evals/mcp_tool_selection/
├── spec.yaml                      # 30-50 test scenarios
├── prompt.md                      # Template with tool registry
├── scorer.py                      # Tool selection + arg validation
└── fixtures/
    └── zapier_tool_registry.json  # 200+ tools from user's server
```

**Ground Truth Construction:**
- For each test scenario, manually identify 1-3 correct tools
- Define required arguments (from JSON schema)
- Include ambiguous cases (multiple valid tools) to test clarification

**Reference Implementation:**
- See `runner/providers/anthropic_provider.py` for tool calling patterns
- Plan document section on "MCP Tool Selection" (lines 117-143 in original plan)
- MCP protocol docs: https://modelcontextprotocol.io/

---

## Known Issues

### 1. BC Tax Spreadsheet - Scorer Extraction Failure ⚠️

**Problem:** Scorer can't extract final tax amounts from model output.

**Details:**
- Model generates perfect formulas in CSV format:
  ```
  A11,Federal Tax Total,=SUM(A6:A10)
  A18,BC Tax Total,=SUM(A12:A17)
  ```
- But scorer expects format like: `Federal Tax: $8524.12`
- Result: 40% score (formulas detected ✅, but amounts not extracted ❌)

**Impact:** 0% pass rate, but model is actually doing the task correctly.

**Fix Options:**
1. **Improve regex patterns** in `evals/bc_tax_spreadsheet/scorer.py`:
   - Extract values from CSV format
   - Parse formula results if possible
2. **Evaluate formulas directly:**
   - Parse the CSV
   - Execute formulas with test income values
   - Compare calculated tax to expected
3. **Change prompt** to explicitly request final values:
   - "After the formulas, state: Federal Tax: $X, BC Tax: $Y, Total: $Z"

**Recommended:** Option 1 (improve extraction) or Option 3 (clearer prompt).

**Location:** `evals/bc_tax_spreadsheet/scorer.py` lines 98-139 (extract_tax_amounts function)

### 2. Test Coverage Gaps

**Missing:**
- No unit tests for scorer functions
- No integration tests for eval runner
- No tests for provider implementations

**Recommendation:** Add pytest tests in `tests/` directory (future work).

---

## Architecture & Code Structure

### Directory Structure
```
evaluation-suite/
├── evals/                          # All evaluation definitions
│   ├── bc_tax_spreadsheet/        # ✅ Tier 1
│   ├── structured_output/         # ✅ Tier 1
│   ├── closed_book_recall/        # ✅ Tier 2
│   ├── prompt_injection/          # ✅ Tier 2
│   ├── long_context_coherence/    # 🚧 TODO
│   └── mcp_tool_selection/        # 🚧 TODO
│
├── runner/                         # Eval execution framework
│   ├── core.py                    # Main runner logic
│   ├── cli.py                     # Command-line interface
│   ├── providers/                 # LLM provider adapters
│   │   ├── __init__.py           # Base Provider class
│   │   ├── openai_provider.py    # ✅ OpenAI API
│   │   └── anthropic_provider.py # ✅ Anthropic API
│   └── scorers/                   # Shared scoring utilities (empty)
│
├── results/                        # JSON result files (gitignored)
├── docs/                          # Documentation
│   ├── TESTING_GUIDE.md          # Step-by-step testing
│   ├── QUICK_START.md            # API key setup
│   └── SECURITY_FIX.md           # API key security notes
│
├── handoffs/                      # Developer handoffs
│   └── 2025-01-09-tier2-continuation.md  # This file
│
├── .env                           # API keys (gitignored)
├── .env.example                   # Template
├── requirements.txt               # Python dependencies
├── pyproject.toml                 # Package config
└── test_tier1.sh                  # Automated test script
```

### Eval Spec Format (YAML)

Every eval has a `spec.yaml`:
```yaml
id: eval_name
version: 1.0.0
task_type: qa | generation | spreadsheet | security
description: "What this eval tests..."

prompt_template: prompt.md        # Jinja template
fixtures:                         # Test cases
  - case_id: test_1
    input: { ... }
    expected_output: { ... }
    metadata: { ... }

constraints:                      # Model hyperparams
  temperature: 0.2
  max_tokens: 2048

metrics:                          # What we measure
  - name: accuracy
    target: 0.8

scorer: scorer.py                 # Grading logic
```

### Scorer Contract

Every `scorer.py` must export a `score()` function:
```python
def score(test_case, model_output: str, eval_spec) -> Dict[str, Any]:
    """
    Score model output against test case.
    
    Args:
        test_case: TestCase object with input, expected_output, metadata
        model_output: Raw text from model
        eval_spec: Full EvalSpec object (for context)
    
    Returns:
        {
            "passed": bool,          # Did it pass? (score >= 0.7 typically)
            "score": float,          # 0.0 to 1.0
            "metrics": Dict[str, Any]  # Detailed breakdown
        }
    """
```

### Provider Contract

Every provider must extend `Provider` base class:
```python
class MyProvider(Provider):
    def generate(self, model: str, prompt: str, **kwargs) -> ModelResponse:
        # Call API, return standardized response
        
    def list_models(self) -> list[str]:
        # Return list of available models
```

**ModelResponse format:**
```python
@dataclass
class ModelResponse:
    text: str                    # Generated text
    model: str                   # Model identifier
    usage: Optional[Any]         # Token usage (provider-specific)
    raw_response: Optional[Any]  # Full API response
```

### Cost Tracking

Built into `runner/core.py` (lines 92-104):
```python
# Extract usage
input_tokens = response.usage.input_tokens or response.usage.prompt_tokens
output_tokens = response.usage.output_tokens or response.usage.completion_tokens

# Estimate cost (rough approximation)
cost_per_1k_input = 0.01   # $0.01 per 1K (adjust per model)
cost_per_1k_output = 0.03  # $0.03 per 1K
estimated_cost = (input_tokens / 1000 * cost_per_1k_input) + 
                 (output_tokens / 1000 * cost_per_1k_output)
```

**Note:** Cost rates are rough averages. For accurate tracking, add model-specific pricing tables.

---

## Testing & Validation

### Environment Setup
```bash
# Clone repo
git clone https://github.com/austinbjohnson/evaluation-suite.git
cd evaluation-suite

# Switch to dev branch
git checkout feat/tier2-core-evals

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure API keys
cp .env.example .env
# Edit .env with real keys:
#   OPENAI_API_KEY=sk-proj-...
#   ANTHROPIC_API_KEY=sk-ant-...
```

### Running Tests

**Quick validation:**
```bash
# List all evals (should show 4)
python -m runner.cli list

# Test one eval
python -m runner.cli run evals/closed_book_recall --models gpt-4o-mini

# View results
python -m runner.cli report <run-id>
```

**Comprehensive test:**
```bash
# Run all 4 completed evals
./test_tier1.sh  # Runs BC Tax + Structured Output only

# Or manually run all 4:
for eval in bc_tax_spreadsheet structured_output closed_book_recall prompt_injection; do
    python -m runner.cli run evals/$eval --models gpt-4o-mini
done
```

**Multi-model comparison:**
```bash
# Test OpenAI vs Anthropic
python -m runner.cli run evals/closed_book_recall \
    --models gpt-4o-mini,claude-3-5-sonnet-20241022

# Compare results
python -m runner.cli report <run-id-1>
python -m runner.cli report <run-id-2>
```

### Expected Results

| Eval | Model | Pass Rate | Avg Score | Cost |
|------|-------|-----------|-----------|------|
| BC Tax Spreadsheet | gpt-4o-mini | 0% ⚠️ | 0.40 | $0.089 |
| Structured Output | gpt-4o-mini | 75% ✅ | 0.90 | $0.011 |
| Closed-Book Recall | gpt-4o-mini | 43% | 0.60 | $0.007 |
| Prompt Injection | gpt-4o-mini | 57% | 0.66 | $0.012 |

**Note:** BC Tax has scorer issue (see Known Issues). Actual model performance is good.

### Validation Checklist

Before considering an eval "complete":
- [ ] Spec.yaml is valid and loads without errors
- [ ] Prompt.md renders correctly with test fixtures
- [ ] Scorer.py returns expected format (passed, score, metrics)
- [ ] Runs without crashing on GPT-4o-mini
- [ ] Pass rate is reasonable (not 0% or 100% unless expected)
- [ ] Cost tracking shows token counts
- [ ] Results saved to results/ directory
- [ ] Report command displays cleanly

---

## Next Steps

### Immediate (Next Session)

1. **Build Long-Context Coherence Eval** (2-3 hours)
   - Create conversation fixtures (NHL analytics project)
   - Implement hybrid scorer (entity extraction + LLM judge)
   - Test with GPT-4o-mini and Claude
   - **Success criteria:** 60-80% pass rate, clear entity retention tracking

2. **Build MCP Tool Selection Eval** (1-2 hours)
   - Get tool registry export from user's Zapier server
   - Create 30-50 test scenarios
   - Implement tool selection scorer with JSON schema validation
   - **Success criteria:** 70-90% pass rate on GPT-4o

3. **Fix BC Tax Scorer** (30 min - 1 hour)
   - Option 1: Improve regex extraction for CSV format
   - Option 2: Update prompt for clearer output format
   - **Success criteria:** Pass rate >70%

4. **Update Documentation**
   - Add Long-Context and MCP evals to README
   - Document known issues and fixes
   - Update testing guide with new evals

### Short-Term (This Week)

5. **Create Tier 2 Test Script**
   - Like `test_tier1.sh` but for all 6 evals
   - Run both OpenAI and Anthropic models
   - Generate comparison summary

6. **Add Google Gemini Provider** (if needed)
   - Similar to Anthropic provider
   - Add to CLI auto-detection
   - Test with Gemini 2.0 Flash

7. **Merge feat/tier2-core-evals to main**
   - After all 4 Tier 2 evals are complete
   - Create detailed PR with results
   - Update main README

### Medium-Term (Next Week)

8. **Cloudflare Backend (Tier 3)**
   - Set up Workers + KV for result storage
   - Create API endpoints (POST /runs, GET /runs/:id)
   - Add Cloudflare Access for privacy
   - Update runner to push results

9. **Static UI Dashboard (Tier 3)**
   - React + Vite on Cloudflare Pages
   - Dashboard, Run Detail, Diff views
   - Trend charts with sparklines
   - Model comparison tables

10. **Tier 3 Evals (Optional)**
    - ZDL (Zapier) Synthesis
    - Guardrails Pipeline A/B

### Long-Term (Portfolio Polish)

11. **Documentation & Demo**
    - Architecture diagram (Mermaid in README)
    - Blog post explaining design decisions
    - Demo video showing full workflow
    - Published results on 3-4 models

12. **Testing & CI/CD**
    - Unit tests for scorers
    - Integration tests for runner
    - GitHub Actions for automated runs
    - Pre-commit hooks (black, ruff, mypy)

---

## Resources & References

### Code References
- **Original plan:** `/Users/ajohnson/Code/abj_evals/evaluation-suite-plan`
- **Testing guide:** `docs/TESTING_GUIDE.md`
- **Quick start:** `docs/QUICK_START.md`

### External Documentation
- **MCP Protocol:** https://modelcontextprotocol.io/
- **OpenAI API:** https://platform.openai.com/docs/api-reference
- **Anthropic API:** https://docs.anthropic.com/claude/reference
- **Cloudflare Workers:** https://developers.cloudflare.com/workers/
- **Cloudflare KV:** https://developers.cloudflare.com/workers/runtime-apis/kv/

### Research Papers & Benchmarks
- **Berkeley Function Calling Leaderboard:** https://gorilla.cs.berkeley.edu/leaderboard.html
- **BFCL Methodology:** AST-based evaluation for tool calling
- **Context window research:** ∞Bench, RULER benchmarks for long-context

### API Keys & Access
- **OpenAI:** User has valid key in `.env`
- **Anthropic:** User has valid key in `.env`
- **Cloudflare:** User has token in `.env` (for future use)
- **Zapier MCP Server:** User mentioned having 200+ tool server available

### Git Branches
- **main:** Tier 1 complete, production-ready
- **feat/tier2-core-evals:** Current work (2/4 evals done)
- **feat/tier1-foundation:** Historical, can be deleted

### Useful Commands
```bash
# See all branches
git branch -a

# Check what's changed
git status
git diff

# View commit history
git log --oneline --graph

# Test a specific scorer
python -c "from evals.closed_book_recall.scorer import score; print(score.__doc__)"

# Check dependencies
pip list | grep -E "(openai|anthropic|pyyaml)"

# Find all spec files
find evals -name "spec.yaml"

# Count lines of code
find runner evals -name "*.py" | xargs wc -l
```

---

## Questions for User (Future)

Before continuing, consider asking:

1. **MCP Tool Registry:**
   - Can you export your Zapier MCP server tool list as JSON?
   - What format is it in? (We need: tool names, descriptions, schemas)
   - Do you want to test with all 200+ tools or a subset?

2. **Long-Context Eval:**
   - Should we use NHL analytics as the domain (as planned)?
   - Or prefer a different business context?
   - How many conversation turns? (Plan says 8, could simplify to 6)

3. **Priorities:**
   - Is completing Tier 2 the priority?
   - Or should we fix BC Tax scorer first?
   - Or jump to Cloudflare backend?

4. **Model Testing:**
   - Which models should be the "baseline" for comparison?
   - GPT-4o-mini, Claude 3.5 Sonnet, Gemini 2.0 Flash?
   - Should we test expensive models (GPT-4o, Claude Opus)?

---

## Final Notes

### What's Great About This Codebase

✅ Clean, maintainable architecture  
✅ Well-documented with step-by-step guides  
✅ Actually working - all 4 evals run successfully  
✅ Cost tracking built-in from day 1  
✅ Multi-provider support (OpenAI, Anthropic)  
✅ Portfolio-ready structure  
✅ Zero hosting costs  

### What Could Be Improved

⚠️ No unit tests yet  
⚠️ BC Tax scorer needs fixing  
⚠️ Cost estimates are rough (not model-specific)  
⚠️ No async execution (sequential runs only)  
⚠️ Limited error handling in some scorers  
⚠️ No result comparison UI yet  

### Development Velocity

**Time invested so far:** ~6-8 hours  
**Lines of code:** ~2,000  
**Evals complete:** 4/8 (50%)  
**Infrastructure:** 80% complete  

**Estimated to completion:**  
- Tier 2 (2 evals): 3-4 hours  
- Tier 3 (backend + UI): 8-10 hours  
- Polish & docs: 2-3 hours  
**Total remaining:** ~15-20 hours

---

## Getting Started (For New Dev)

```bash
# 1. Clone and setup
git clone https://github.com/austinbjohnson/evaluation-suite.git
cd evaluation-suite
git checkout feat/tier2-core-evals

# 2. Environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Configure (get keys from user)
cp .env.example .env
# Add real API keys to .env

# 4. Validate everything works
python -m runner.cli list  # Should show 4 evals
python -m runner.cli run evals/closed_book_recall --models gpt-4o-mini

# 5. Read the docs
cat docs/TESTING_GUIDE.md
cat evaluation-suite-plan  # Original design doc

# 6. Start building!
# Next: Long-Context Coherence eval (see "What Needs to Be Built" section)
```

---

**Handoff Complete.** Everything needed to continue is in this document. Good luck! 🚀

**Questions?** Contact Austin or refer to:
- Testing Guide: `docs/TESTING_GUIDE.md`
- Original Plan: `/Users/ajohnson/Code/abj_evals/evaluation-suite-plan`
- GitHub: https://github.com/austinbjohnson/evaluation-suite

