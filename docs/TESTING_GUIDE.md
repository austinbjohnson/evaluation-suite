# Testing Guide - Tier 1 Evaluations

This guide walks you through testing the BC Tax Spreadsheet and Structured Output evaluations step-by-step.

## Prerequisites

✅ You should have:
- Cloned the repository
- Created a virtual environment
- Installed dependencies
- Added API keys to `.env` file

## Setup Steps

### 1. Navigate to the Project Directory

```bash
cd /Users/ajohnson/Code/abj_evals/evaluation-suite
```

### 2. Activate Virtual Environment

```bash
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt.

### 3. Verify Your API Keys

```bash
# Check that your .env file exists and has keys
cat .env
```

You should see:
```
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

If not, create the file:
```bash
echo "OPENAI_API_KEY=your-key-here" > .env
echo "ANTHROPIC_API_KEY=your-key-here" >> .env
```

## Test 1: List Available Evaluations

This verifies the CLI and spec loading works.

```bash
python -m runner.cli list
```

**Expected Output:**
```
📋 Available Evaluations:

  • bc_tax_spreadsheet (v1.0.0)
    Tests the model's ability to generate a working spreadsheet...
    Path: evals/bc_tax_spreadsheet

  • structured_output (v1.0.0)
    Tests the model's ability to generate structured output...
    Path: evals/structured_output
```

✅ **Success:** Both evaluations appear in the list.

---

## Test 2: Run BC Tax Spreadsheet Eval

This tests spreadsheet generation with formulas for Canadian tax calculations.

### Run the Evaluation

```bash
python -m runner.cli run evals/bc_tax_spreadsheet --models gpt-4o-mini
```

**What happens:**
- The eval runs 3 test cases (income levels: $45k, $75k, $125k)
- Model generates spreadsheet formulas for each
- Scorer validates formula presence and numerical accuracy
- Takes ~30-60 seconds
- Costs ~$0.01-0.02

**Expected Output:**
```
🚀 Running Evaluation: bc_tax_spreadsheet (v1.0.0)
   Tests the model's ability to generate a working spreadsheet...

📊 Testing model: gpt-4o-mini
============================================================
Running case: income_45000
Running case: income_75000
Running case: income_125000

✅ Completed: 20250110_123456_abc12345
   Pass rate: 66.7%
   Avg score: 0.733
   Tokens: 2,456 (in: 1,234, out: 1,222)
   Est. cost: $0.0123
```

### View Detailed Results

```bash
# Copy the run_id from the output above (e.g., 20250110_123456_abc12345)
python -m runner.cli report 20250110_123456_abc12345
```

**Expected Output:**
```
📊 Evaluation Report: 20250110_123456_abc12345
============================================================
Suite: bc_tax_spreadsheet (v1.0.0)
Model: gpt-4o-mini (openai)
Timestamp: 2025-01-10T12:34:56...

Hyperparameters:
  temperature: 0.2
  max_tokens: 2048

Aggregate Results:
  pass_rate: 0.667
  passed_cases: 2
  total_cases: 3
  avg_score: 0.733
  avg_latency_ms: 1234.5

Cost Metrics:
  Total tokens: 2,456
  Input tokens: 1,234
  Output tokens: 1,222
  Estimated cost: $0.0123

Per-Case Results:

  ✅ income_45000: pass
     Score: 0.800
     Latency: 1200ms

  ✅ income_75000: pass
     Score: 0.800
     Latency: 1150ms

  ❌ income_125000: fail
     Score: 0.600
     Latency: 1350ms
```

### Check the Raw Results File

```bash
# View the JSON results (use the run_id from above)
cat results/20250110_123456_abc12345.json | python -m json.tool | head -50
```

This shows the full structured data including model outputs, scores, and metrics.

---

## Test 3: Run Structured Output Eval

This tests JSON, XML, and CSV generation with schema validation.

### Run the Evaluation

```bash
python -m runner.cli run evals/structured_output --models gpt-4o-mini
```

**What happens:**
- Runs 4 test cases (JSON contact, JSON invoice, XML product, CSV sales)
- Model generates structured data for each format
- Scorer validates parsing, schema compliance, and no extra text
- Takes ~20-40 seconds
- Costs ~$0.005-0.01

**Expected Output:**
```
🚀 Running Evaluation: structured_output (v1.0.0)
   Tests the model's ability to generate structured output...

📊 Testing model: gpt-4o-mini
============================================================
Running case: json_contact
Running case: json_invoice
Running case: xml_product
Running case: csv_sales

✅ Completed: 20250110_123500_def67890
   Pass rate: 100.0%
   Avg score: 1.000
   Tokens: 1,123 (in: 567, out: 556)
   Est. cost: $0.0056
```

### View Results

```bash
python -m runner.cli report 20250110_123500_def67890
```

**Expected Output:**
```
📊 Evaluation Report: 20250110_123500_def67890
============================================================
Suite: structured_output (v1.0.0)
Model: gpt-4o-mini (openai)

...

Per-Case Results:

  ✅ json_contact: pass
     Score: 1.000
     Latency: 450ms

  ✅ json_invoice: pass
     Score: 1.000
     Latency: 520ms

  ✅ xml_product: pass
     Score: 1.000
     Latency: 480ms

  ✅ csv_sales: pass
     Score: 1.000
     Latency: 510ms
```

---

## Test 4: Compare Multiple Models

Run both evals on multiple models to see differences.

### Run with Multiple Models

```bash
# Test BC Tax with both GPT-4o-mini and GPT-4o
python -m runner.cli run evals/bc_tax_spreadsheet --models gpt-4o-mini,gpt-4o

# Or test with Anthropic (if you added the provider)
# python -m runner.cli run evals/bc_tax_spreadsheet --models gpt-4o-mini,claude-3-5-sonnet-20241022
```

**What happens:**
- Runs the eval sequentially for each model
- Generates separate run_ids for each
- You can compare results side-by-side

### Compare Results

```bash
# View both reports
python -m runner.cli report <run_id_1>
python -m runner.cli report <run_id_2>
```

Look for differences in:
- Pass rates
- Average scores
- Token usage
- Costs
- Per-case performance

---

## Test 5: Test with Different Parameters

Try different hyperparameters to see their effect.

### Higher Temperature (More Creative)

```bash
python -m runner.cli run evals/bc_tax_spreadsheet \
  --models gpt-4o-mini \
  --temperature 0.7 \
  --max-tokens 3000
```

### With Seed (Reproducible)

```bash
python -m runner.cli run evals/structured_output \
  --models gpt-4o-mini \
  --seed 42
```

Run it twice with the same seed - results should be nearly identical.

---

## Troubleshooting

### Error: "OpenAI API key not provided"

**Solution:**
```bash
# Make sure .env file exists in the project root
cat .env

# If missing, create it:
echo "OPENAI_API_KEY=your-actual-key" > .env
```

### Error: "No module named 'runner'"

**Solution:**
```bash
# Make sure you're in the project directory
pwd  # Should show .../evaluation-suite

# Make sure venv is activated
source venv/bin/activate
```

### Error: "spec.yaml not found"

**Solution:**
```bash
# Make sure you're running from the project root
cd /Users/ajohnson/Code/abj_evals/evaluation-suite

# Then run the command
python -m runner.cli run evals/bc_tax_spreadsheet
```

### Results Seem Wrong

**Check:**
1. View the raw model output in the JSON file
2. Check if formulas were detected (has_formulas in metrics)
3. Look at extracted tax amounts vs expected
4. Some failure is expected - models aren't perfect!

---

## Expected Results Summary

### BC Tax Spreadsheet
- **Pass rate:** 60-100% (depends on model)
- **Common issues:** 
  - Model might hardcode values instead of formulas
  - Tax calculations might be off by a few dollars
  - Federal vs provincial rates might be confused
- **Cost:** ~$0.01-0.03 per run

### Structured Output
- **Pass rate:** 80-100% (most models do well)
- **Common issues:**
  - Extra explanatory text before/after the structure
  - Missing fields from schema
  - Invalid syntax (rare with modern models)
- **Cost:** ~$0.005-0.015 per run

---

## Next Steps After Testing

Once you've verified both evals work:

1. ✅ **Check results/** directory for JSON files
2. ✅ **Try different models** to see performance differences
3. ✅ **Document any interesting findings**
4. 🚀 **Ready to move to Tier 2** - more evaluations!

---

## Quick Reference Commands

```bash
# Activate venv
source venv/bin/activate

# List evals
python -m runner.cli list

# Run BC Tax
python -m runner.cli run evals/bc_tax_spreadsheet --models gpt-4o-mini

# Run Structured Output
python -m runner.cli run evals/structured_output --models gpt-4o-mini

# View report
python -m runner.cli report <run-id>

# View all results
ls -lh results/

# View latest result
ls -t results/*.json | head -1 | xargs python -m runner.cli report
```

---

## Success Criteria

You've successfully tested Tier 1 if:
- ✅ Both evals run without errors
- ✅ You can view reports with `python -m runner.cli report`
- ✅ Cost tracking shows reasonable token counts
- ✅ Results are saved to `results/` directory
- ✅ Pass rates are between 60-100%

**🎉 If all checks pass, Tier 1 is validated and working!**

