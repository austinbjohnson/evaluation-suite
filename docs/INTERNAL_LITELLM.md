# Internal LiteLLM Router Configuration

This document explains how to configure the evaluation suite to use an internal LiteLLM router instead of public APIs.

## Overview

The LiteLLM provider supports custom base URLs and metadata for internal company routers. This allows you to:
- Route all inference through a central internal service
- Track usage with custom metadata fields
- Maintain cost attribution across teams and products

## Configuration

### 1. Create Internal Config File

Create a `.env.internal` file in the repository root (this file is gitignored):

```bash
# Internal LiteLLM Router
LITELLM_BASE_URL=https://litellm.your-company.com
LITELLM_API_KEY=your-internal-api-key

# Required Metadata
LITELLM_METADATA_PRODUCT=evaluation-suite
LITELLM_METADATA_OWNER=team-data-ai-ml
LITELLM_METADATA_ENVIRONMENT=development  # or staging/production

# Optional Metadata
LITELLM_METADATA_FEATURE=model-evaluation
LITELLM_METADATA_REFERRERS=
LITELLM_METADATA_CUSTOMUSER_ID=
LITELLM_METADATA_ACCOUNT_ID=
LITELLM_METADATA_ZAP_ID=

# Debugging
LITELLM_VERBOSE=false
```

### 2. Load Internal Config

Add to your shell profile or load before running:

```bash
# Load both standard and internal configs
export $(cat .env .env.internal 2>/dev/null | xargs)
```

Or use Python's dotenv:

```python
from dotenv import load_dotenv

load_dotenv()  # Loads .env
load_dotenv('.env.internal')  # Loads internal config
```

## Metadata Fields

The LiteLLM provider automatically includes the following metadata in requests:

### Required Fields

- **product** (string): Name of the product/service
  - Use names from your internal service catalog when available
  - Example: `evaluation-suite`, `custom-actions`, `central`

- **owner** (string): Responsible team identifier
  - Format: team name without prefix
  - Example: `team-data-ai-ml`, `team-platform`

- **environment** (string): Deployment environment
  - Values: `development`, `staging`, or `production`
  - Match this to your LiteLLM instance (staging → staging)

### Optional Fields

- **feature** (string): Sub-product feature identifier
  - Useful for breaking down usage within products
  - Example: `code-generation`, `input-field-schema`

- **referrers** (string): Comma-separated list of calling services
  - Tracks the chain of services that led to this call
  - Example: `central, zap-guesser`
  - If service A calls service B which calls LiteLLM, B includes `referrers: "A"`

- **customuser_id** (integer): User identifier
- **account_id** (integer): Account identifier  
- **zap_id** (integer): Workflow identifier

## Example Request Structure

When configured, the provider sends requests like:

```python
{
    "model": "your-model-name",
    "messages": [...],
    "metadata": {
        "spend_logs_metadata": {
            "owner": "team-data-ai-ml",
            "environment": "development",
            "product": "evaluation-suite",
            "feature": "model-evaluation",
            "referrers": "",
            "customuser_id": 1234567,
            "account_id": 1234567,
        }
    }
}
```

## Usage

Once configured, the evaluation suite automatically routes LiteLLM requests through your internal router:

```bash
# This will use internal router for LiteLLM-routed models
python -m runner.cli run evals/structured_output \
    --models together_ai/meta-llama/Meta-Llama-3.1-70B

# Direct providers (OpenAI, Anthropic) still use their APIs
python -m runner.cli run evals/structured_output \
    --models gpt-4o-mini,claude-sonnet-4-20250514
```

## Security Notes

1. **Never commit** `.env.internal` to git (already in .gitignore)
2. **Never hardcode** internal URLs or API keys in code
3. **Never include** company-specific identifiers in public documentation
4. Store API keys in secure secret management systems
5. Rotate keys regularly according to company policy

## Fallback Behavior

If `LITELLM_BASE_URL` is not set, the provider falls back to public LiteLLM behavior:
- Uses provider-specific API keys (OPENAI_API_KEY, etc.)
- No custom metadata included
- Routes directly to public APIs

## Troubleshooting

### Enable Verbose Logging

```bash
export LITELLM_VERBOSE=true
python -m runner.cli run evals/structured_output --models <model>
```

This prints full request/response details for debugging.

### Verify Configuration

Check that environment variables are loaded:

```bash
echo $LITELLM_BASE_URL
echo $LITELLM_API_KEY
echo $LITELLM_METADATA_PRODUCT
```

### Test Connection

```python
from runner.providers.litellm_provider import LiteLLMProvider

provider = LiteLLMProvider()
print(f"Base URL: {provider.base_url}")
print(f"Metadata: {provider.custom_metadata}")

# Make test request
response = provider.generate(
    model="your-model-name",
    prompt="this is a test request",
    max_tokens=50
)
print(response.text)
```

## Reference

- LiteLLM Documentation: https://docs.litellm.ai/
- Internal router documentation: (see your company's internal docs)

