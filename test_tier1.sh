#!/bin/bash
# Quick test script for Tier 1 evaluations

set -e  # Exit on any error

echo "🧪 Testing Tier 1 Evaluations"
echo "=============================="
echo ""

# Check if venv is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "⚠️  Virtual environment not activated. Activating now..."
    source venv/bin/activate
fi

# Check for API keys
if [[ -z "$OPENAI_API_KEY" && ! -f .env ]]; then
    echo "❌ Error: No .env file found and OPENAI_API_KEY not set"
    echo "   Please create a .env file with your API keys"
    echo "   See .env.example for template"
    exit 1
fi

echo "✅ Environment ready"
echo ""

# Test 1: List evals
echo "📋 Test 1: Listing available evaluations..."
python -m runner.cli list
echo ""

# Test 2: Run BC Tax Spreadsheet
echo "📊 Test 2: Running BC Tax Spreadsheet eval..."
echo "   Model: gpt-4o-mini"
echo "   Expected cost: ~$0.01-0.02"
echo ""
BC_RUN_ID=$(python -m runner.cli run evals/bc_tax_spreadsheet --models gpt-4o-mini 2>&1 | grep "Completed:" | awk '{print $3}')
echo ""
echo "   Run ID: $BC_RUN_ID"
echo ""

# Test 3: Run Structured Output
echo "📄 Test 3: Running Structured Output eval..."
echo "   Model: gpt-4o-mini"
echo "   Expected cost: ~$0.005-0.01"
echo ""
SO_RUN_ID=$(python -m runner.cli run evals/structured_output --models gpt-4o-mini 2>&1 | grep "Completed:" | awk '{print $3}')
echo ""
echo "   Run ID: $SO_RUN_ID"
echo ""

# Display reports
echo "📈 Results Summary"
echo "=================="
echo ""
echo "BC Tax Spreadsheet:"
python -m runner.cli report $BC_RUN_ID 2>/dev/null | grep -A 5 "Aggregate Results:"
echo ""
echo "Structured Output:"
python -m runner.cli report $SO_RUN_ID 2>/dev/null | grep -A 5 "Aggregate Results:"
echo ""

# Summary
echo "✅ Testing Complete!"
echo ""
echo "📁 Results saved to:"
echo "   - results/$BC_RUN_ID.json"
echo "   - results/$SO_RUN_ID.json"
echo ""
echo "📖 For detailed reports, run:"
echo "   python -m runner.cli report $BC_RUN_ID"
echo "   python -m runner.cli report $SO_RUN_ID"
echo ""
echo "🎉 Tier 1 validation successful!"

