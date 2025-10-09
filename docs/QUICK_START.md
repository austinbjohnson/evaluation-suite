# Quick Start - Add Your API Keys

## Step 1: Create .env File

From the project root directory, create a `.env` file:

```bash
cd /Users/ajohnson/Code/abj_evals/evaluation-suite

# Create .env file (it will be in .gitignore, so it won't be committed)
touch .env
```

## Step 2: Add Your API Keys

Open the `.env` file in your text editor and add your keys:

```bash
# Option 1: Use a text editor
code .env  # If you use VS Code
# or
nano .env  # If you prefer terminal editor
# or
open -e .env  # Opens in TextEdit on Mac
```

Add these lines (replace with your actual keys):

```
OPENAI_API_KEY=sk-proj-your-actual-key-here
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
```

**Important:** 
- No spaces around the `=` sign
- No quotes around the keys
- Replace `your-actual-key-here` with your real API keys

## Step 3: Verify It Works

```bash
# Check that the file exists and has content
cat .env

# You should see your keys (first few characters will show)
```

## Step 4: Run the Test

Now try the test script again:

```bash
source venv/bin/activate
./test_tier1.sh
```

## Alternative: Manual Testing

If the script still doesn't work, you can test manually:

```bash
cd /Users/ajohnson/Code/abj_evals/evaluation-suite
source venv/bin/activate

# Export keys directly in your terminal (temporary for this session)
export OPENAI_API_KEY="sk-proj-your-key-here"
export ANTHROPIC_API_KEY="sk-ant-your-key-here"

# List evals
python -m runner.cli list

# Run BC Tax eval
python -m runner.cli run evals/bc_tax_spreadsheet --models gpt-4o-mini

# Run Structured Output eval
python -m runner.cli run evals/structured_output --models gpt-4o-mini
```

## Troubleshooting

### Error: "OPENAI_API_KEY not set"

**Solution:** Make sure your `.env` file is in the project root directory:
```bash
# Check you're in the right place
pwd
# Should show: /Users/ajohnson/Code/abj_evals/evaluation-suite

# Check .env exists
ls -la .env

# Check .env has content
cat .env
```

### Error: "command not found"

**Solution:** Make sure venv is activated:
```bash
source venv/bin/activate
# You should see (venv) in your prompt
```

### Still Not Working?

Use the export method above to set keys directly in your terminal, then run the CLI commands manually.

