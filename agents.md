# Model Agents & Provider Configuration

**Last Updated:** At least October 9, 2025  
**Status:** Active Development

This document details the model families currently in scope for testing and the provider infrastructure supporting them.

---

## Models in Scope for Testing

### OpenAI Models

**GPT-5 Family:**
- `gpt-5` (placeholder - to be verified with OpenAI API docs)
- `gpt-5-turbo` (placeholder - to be verified)
- Note: Exact model identifiers pending verification due to training cutoff (April 2024)

**GPT-5 Codex Family:**
- `gpt-5-codex` (placeholder - to be verified)
- Specialized for code generation and understanding

**OSS Family:**
- OpenAI's open-source model offerings (to be verified)

**Legacy Models (Currently Supported):**
- `gpt-4o`
- `gpt-4o-mini`
- `gpt-4-turbo`
- `gpt-4`
- `gpt-3.5-turbo`

### Anthropic Models

**Claude 4 Family (Verified):**
- `claude-sonnet-4-20250514` - Claude Sonnet 4
- `claude-sonnet-4.5-*` (to be verified if available)
- `claude-opus-4-1-20250805` - Claude Opus 4.1
- `claude-3-5-haiku-20241022` - Claude Haiku 3.5

**Legacy Models (Currently Supported):**
- `claude-3-5-sonnet-20241022`
- `claude-3-5-sonnet-20240620`
- `claude-3-opus-20240229`
- `claude-3-haiku-20240307`

### Open Source Models (via AWS Bedrock & LiteLLM)

**Llama Models:**
- Meta Llama 3.x family
- Available through AWS Bedrock

**Mistral Models:**
- Mistral 7B, Mixtral 8x7B
- Available through AWS Bedrock

**Qwen Models:**
- Alibaba Qwen family
- Available through LiteLLM router

**DeepSeek Models:**
- DeepSeek Coder, DeepSeek Chat
- Available through LiteLLM router

**Other OSS Models:**
- Apple Intelligence models (via LiteLLM)
- IBM Granite models (via LiteLLM)
- Kimi models (via LiteLLM)
- Additional models as they become available

---

## Provider Infrastructure

### Provider Architecture

The evaluation suite supports multiple model providers through a unified `Provider` interface:

```python
class Provider(ABC):
    def generate(self, model: str, prompt: str, **kwargs) -> ModelResponse
    def list_models(self) -> list[str]
```

### Implemented Providers

#### 1. OpenAI Provider
**File:** `runner/providers/openai_provider.py`  
**Environment Variable:** `OPENAI_API_KEY`  
**Supports:** GPT-4, GPT-4o, GPT-4o-mini, GPT-3.5-turbo, future GPT-5 models

#### 2. Anthropic Provider
**File:** `runner/providers/anthropic_provider.py`  
**Environment Variable:** `ANTHROPIC_API_KEY`  
**Supports:** Claude 3, Claude 3.5, Claude 4 family models

#### 3. AWS Bedrock Provider
**File:** `runner/providers/bedrock_provider.py`  
**Environment Variables:** 
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION` (default: us-east-1)

**Supports:**
- Meta Llama models
- Anthropic Claude models (via Bedrock)
- Mistral models
- Amazon Titan models
- Cohere models

**Routing:** Auto-detected by model prefix:
- `meta.*` → Bedrock
- `mistral.*` → Bedrock
- `amazon.*` → Bedrock
- `cohere.*` → Bedrock

#### 4. LiteLLM Provider (Universal Router)
**File:** `runner/providers/litellm_provider.py`  
**Environment Variables:** 
- `LITELLM_BASE_URL` - Optional custom base URL for internal routers
- `LITELLM_API_KEY` - Optional API key for custom instances
- `LITELLM_METADATA_*` - Optional metadata fields for tracking
- Model-specific keys (OpenAI, Anthropic, etc.) for public routing

**Supports:** 100+ models through unified interface:
- All major providers (OpenAI, Anthropic, Google, etc.)
- Open source models (Llama, Qwen, DeepSeek, etc.)
- Custom internal routers
- Local models

**Routing:** Fallback for any model not handled by specific providers

**Internal Routing:** Supports custom base URLs and metadata for company-internal LiteLLM instances. See `docs/INTERNAL_LITELLM.md` for configuration details.

---

## Provider Selection Logic

The CLI automatically detects the appropriate provider based on model name:

```python
if "claude" in model_name:
    provider = "anthropic"
elif any(x in model_name for x in ["gpt", "o1", "o3"]):
    provider = "openai"
elif any(x in model_name for x in ["meta", "llama", "mistral", "amazon", "cohere"]):
    provider = "bedrock"
else:
    provider = "litellm"  # Universal fallback
```

---

## Cost Tracking

All providers implement automatic cost tracking:

- **Input tokens:** Counted per API response
- **Output tokens:** Counted per API response
- **Estimated USD:** Rough approximation based on provider pricing
- **Per-case breakdown:** Available in detailed reports

**Note:** Cost estimates use approximate rates. Consult provider documentation for exact pricing.

---

## Testing Strategy

### Evaluation Coverage

All models run through the same evaluation suite:

**Tier 1 (Foundation):**
1. BC Tax Spreadsheet - Formula generation and validation
2. Structured Output Validation - JSON/XML/CSV compliance

**Tier 2 (Core Capabilities):**
3. Closed-Book Knowledge Recall - Factual accuracy
4. Prompt Injection Resistance - Security testing
5. Long-Context Coherence (Planned)
6. MCP Tool Selection (Planned)

**Tier 3 (Advanced):**
7. ZDL (Zapier) Synthesis (Planned)
8. Guardrails Pipeline A/B (Planned)

### Cross-Model Comparison

Results are stored in `results/` directory with format:
```
results/YYYYMMDD_HHMMSS_<run-id>.json
```

Each result includes:
- Model name and provider
- Pass rate and average score
- Per-case breakdown
- Token usage and cost
- Latency metrics

### Running Tests

```bash
# Test with specific model
python -m runner.cli run evals/closed_book_recall --models gpt-4o-mini

# Test across multiple providers
python -m runner.cli run evals/structured_output \
    --models gpt-4o-mini,claude-sonnet-4-20250514,meta.llama3-70b-instruct

# Compare OpenAI vs Anthropic vs OSS
python -m runner.cli run evals/prompt_injection \
    --models gpt-5-turbo,claude-opus-4-1-20250805,mistral.mixtral-8x7b
```

---

## Configuration & Setup

### Required API Keys

Create `.env` file in repository root:

```bash
# OpenAI
OPENAI_API_KEY=sk-proj-...

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# AWS Bedrock
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1

# LiteLLM (uses same keys as above, plus any additional providers)
```

### Dependencies

Install required packages:

```bash
pip install -r requirements.txt
```

Key dependencies:
- `openai` - OpenAI API client
- `anthropic` - Anthropic API client
- `boto3` - AWS SDK for Bedrock
- `litellm` - Universal LLM router

---

## Future Roadmap

### Planned Providers
- **Google Gemini:** Direct API integration for Gemini 2.0 family
- **Groq:** High-speed inference for Llama models
- **Together AI:** Additional OSS model hosting
- **Replicate:** Community models and fine-tuned variants

### Planned Models
- Google Gemini 2.0 Flash, Pro
- Additional Apple Intelligence models
- IBM Granite code models
- Open source models as released

### Infrastructure Improvements
- Async execution for parallel model testing
- Model-specific cost rate tables (accurate pricing)
- Provider fallback/retry logic
- Caching for repeated evaluations

---

## References

- **OpenAI API Docs:** https://platform.openai.com/docs
- **Anthropic API Docs:** https://docs.anthropic.com/
- **AWS Bedrock Docs:** https://docs.aws.amazon.com/bedrock/
- **LiteLLM Docs:** https://docs.litellm.ai/
- **Evaluation Suite Plan:** `/evaluation-suite-plan`
- **Handoff Document:** `/handoffs/2025-01-09-tier2-continuation.md`

