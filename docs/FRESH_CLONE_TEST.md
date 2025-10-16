# Fresh Clone Test - External User Setup Simulation

**Purpose:** Verify that new users can successfully set up and run the evaluation suite from scratch.

**Status:** ⏳ Manual test - requires clean environment

---

## Test Environment Requirements

- Clean machine or VM (no prior evaluation-suite setup)
- Python 3.9+ installed
- Git installed
- No pre-existing `.env` files or API keys configured

---

## Test Procedure

### Step 1: Clone Repository

```bash
git clone https://github.com/austinbjohnson/evaluation-suite.git
cd evaluation-suite
```

**Expected:** ✅ Repository clones successfully

### Step 2: Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

**Expected:** ✅ Virtual environment created without errors

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

**Expected:** 
- ✅ All packages install successfully
- ⚠️  May see 1 medium urllib3 vulnerability (expected - see SECURITY_AUDIT_REPORT.md)

### Step 4: Copy Environment Template

```bash
cp .env.example .env
```

**Expected:** ✅ `.env.example` exists and is readable

### Step 5: Verify Setup (No API Keys)

```bash
python -m runner.cli list
```

**Expected:** ✅ Lists available evals without requiring API keys

### Step 6: Run Eval Without Credentials

```bash
python -m runner.cli run bc_tax_spreadsheet
```

**Expected:** 
- ❌ Should fail with clear error message
- ✅ Error message should say: "OpenAI API key not provided. Set OPENAI_API_KEY environment variable."
- ✅ Error message should NOT contain:
  - File paths (e.g., `/Users/...`)
  - Partial API keys
  - Internal system details

### Step 7: Configure API Keys

Edit `.env` file and add real API keys:

```bash
# Edit .env with your preferred editor
nano .env

# Add:
OPENAI_API_KEY=sk-proj-your-key-here
# or
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

**Expected:** ✅ File edits save successfully

### Step 8: Run Successful Eval

```bash
python -m runner.cli run bc_tax_spreadsheet
```

**Expected:**
- ✅ Eval runs successfully
- ✅ Results saved to `results/` directory
- ✅ Console shows progress and final score
- ✅ Cost tracking displayed

### Step 9: View Results

```bash
ls -lh results/
python -m runner.cli report <run-id-from-previous-step>
```

**Expected:**
- ✅ Result file exists in `results/`
- ✅ Report command displays formatted results
- ✅ All metrics visible

### Step 10: Security Verification

```bash
# Check that no secrets committed
git status

# Should show .env as untracked (gitignored)
```

**Expected:**
- ✅ `.env` file NOT staged for commit
- ✅ `.gitignore` preventing sensitive files
- ✅ Only modified files are code/docs (if any)

---

## Success Criteria

| Criterion | Status | Notes |
|-----------|--------|-------|
| Clone successful | ⏳ | - |
| Dependencies install | ⏳ | urllib3 warning acceptable |
| `.env.example` exists | ⏳ | - |
| List command works | ⏳ | No API keys needed |
| Error messages safe | ⏳ | No paths/secrets leaked |
| Eval runs with keys | ⏳ | At least one provider |
| Results generated | ⏳ | JSON file created |
| `.env` gitignored | ⏳ | Not committable |

**Overall:** ⏳ **PENDING** - Requires clean environment test

---

## Common Issues & Solutions

### Issue: `ModuleNotFoundError`
**Solution:** Ensure virtual environment is activated: `source venv/bin/activate`

### Issue: `pip-audit` warnings about urllib3
**Solution:** Expected - see SECURITY_AUDIT_REPORT.md. This is a known, accepted low-severity issue due to AWS botocore constraints.

### Issue: `ValueError: API key not provided`
**Solution:** 
1. Verify `.env` file exists in project root
2. Check API key is correctly formatted
3. Ensure environment variable name matches (OPENAI_API_KEY vs ANTHROPIC_API_KEY)

### Issue: Permission errors on results/
**Solution:** Check file permissions. Should be writable by user. May need: `chmod 755 results/`

### Issue: Git shows `.env` as modified
**Solution:** `.env` should be gitignored. Run: `git check-ignore .env` to verify.

---

## Automated CI/CD Test (Future)

This test should be automated in CI/CD:

```yaml
# .github/workflows/fresh-install-test.yml (example)
name: Fresh Install Test

on: [pull_request]

jobs:
  fresh-install:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          python -m venv venv
          source venv/bin/activate
          pip install -r requirements.txt
      - name: Test without credentials
        run: |
          source venv/bin/activate
          python -m runner.cli list
          # Should succeed
          python -m runner.cli run bc_tax_spreadsheet || true
          # Should fail with safe error
      - name: Security checks
        run: |
          pip install pip-audit
          pip-audit --requirement requirements.txt || true
```

---

## Test Results

**Date:** _TBD - requires manual test_  
**Tester:** _TBD_  
**Environment:** _TBD_  
**Status:** _TBD_  

---

## Notes for External Users

If you're a new user following these steps and encounter issues:

1. Check that you've copied `.env.example` to `.env`
2. Verify API keys are correctly formatted
3. Ensure virtual environment is activated
4. Review [TESTING_GUIDE.md](TESTING_GUIDE.md) for detailed walkthrough
5. Check [SECURITY.md](SECURITY.md) for best practices

**Need help?** Open an issue on GitHub with:
- Steps you followed
- Error messages (redact any API keys!)
- Your environment (OS, Python version)

