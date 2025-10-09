"""
Scorer for BC Tax Spreadsheet evaluation.

Validates:
1. Presence of formulas (not hardcoded values)
2. Numerical accuracy of tax calculations (±$1 tolerance)
"""

import json
import re
from pathlib import Path
from typing import Any, Dict


def load_tax_params(year: int = 2025) -> Dict[str, Any]:
    """Load tax parameters for the specified year"""
    params_file = Path(__file__).parent / "params" / f"{year}.json"
    with open(params_file, 'r') as f:
        return json.load(f)


def calculate_progressive_tax(income: float, brackets: list, basic_personal_amount: float) -> float:
    """
    Calculate tax using progressive tax brackets.
    
    Args:
        income: Total income
        brackets: List of tax brackets with 'min', 'max', 'rate'
        basic_personal_amount: Tax-free basic amount
    
    Returns:
        Total tax owing
    """
    # Apply basic personal amount
    taxable_income = max(0, income - basic_personal_amount)
    
    if taxable_income == 0:
        return 0.0
    
    tax = 0.0
    
    for bracket in brackets:
        bracket_min = bracket['min']
        bracket_max = bracket['max']
        rate = bracket['rate']
        
        if taxable_income <= bracket_min:
            # Income doesn't reach this bracket
            break
        
        if bracket_max is None:
            # Top bracket - tax all remaining income
            taxable_in_bracket = taxable_income - bracket_min
            tax += taxable_in_bracket * rate
            break
        else:
            if taxable_income <= bracket_max:
                # Income falls within this bracket
                taxable_in_bracket = taxable_income - bracket_min
                tax += taxable_in_bracket * rate
                break
            else:
                # Income exceeds this bracket - tax the full bracket
                taxable_in_bracket = bracket_max - bracket_min
                tax += taxable_in_bracket * rate
    
    return round(tax, 2)


def check_formulas_present(output: str) -> bool:
    """
    Check if the output contains formulas (not just hardcoded numbers).
    
    Looks for patterns like:
    - =A1*0.14
    - =SUM(B2:B5)
    - =IF(A1>50000, ...)
    - =MIN(MAX(...))
    """
    # Common formula patterns
    formula_patterns = [
        r'=[A-Z]+\d+',  # Cell references like =A1
        r'=\w+\(',       # Functions like =SUM(, =IF(, =MAX(
        r'\*\s*0\.\d+',  # Tax rates like * 0.14
        r'[-+*/]\s*[A-Z]+\d+',  # Arithmetic with cells
    ]
    
    for pattern in formula_patterns:
        if re.search(pattern, output, re.IGNORECASE):
            return True
    
    return False


def extract_tax_amounts(output: str) -> Dict[str, float]:
    """
    Attempt to extract tax amounts from model output.
    
    Returns dict with 'federal_tax', 'bc_tax', 'total_tax' if found.
    
    Prioritizes extraction from Summary section if present, with improved
    patterns to handle comma-formatted currency (e.g., $4,108.30).
    """
    amounts = {}
    
    # Try to extract from Summary section first (more reliable)
    summary_section = re.search(r'###?\s*Summary.*?(?=###|$)', output, re.IGNORECASE | re.DOTALL)
    search_text = summary_section.group(0) if summary_section else output
    
    # Improved patterns that handle currency formatting better
    # Look for patterns like "Federal Tax: $4,108.30" or "- **Federal Tax:** $4,108.30"
    patterns = {
        'federal_tax': [
            r'\*?\*?Federal\s+Tax\*?\*?\s*[:*]+\s*\$\s*([\d,]+\.?\d*)',
            r'federal\s+tax\s*[:]+\s*\$\s*([\d,]+\.?\d*)',
        ],
        'bc_tax': [
            r'\*?\*?BC\s+Tax\*?\*?\s*[:*]+\s*\$\s*([\d,]+\.?\d*)',
            r'bc\s+(?:provincial\s+)?tax\s*[:]+\s*\$\s*([\d,]+\.?\d*)',
        ],
        'total_tax': [
            r'\*?\*?Total\s+Tax\*?\*?\s*[:*]+\s*\$\s*([\d,]+\.?\d*)',
            r'total\s+tax\s*(?:payable)?\s*[:]+\s*\$\s*([\d,]+\.?\d*)',
        ]
    }
    
    for key, pattern_list in patterns.items():
        for pattern in pattern_list:
            match = re.search(pattern, search_text, re.IGNORECASE)
            if match:
                # Extract and clean the number (remove commas)
                value_str = match.group(1).replace(',', '')
                try:
                    amounts[key] = float(value_str)
                    break
                except ValueError:
                    continue
    
    return amounts


def score(test_case, model_output: str, eval_spec) -> Dict[str, Any]:
    """
    Score the model's spreadsheet output.
    
    Returns dict with:
    - passed: bool
    - score: float (0.0 to 1.0)
    - metrics: dict with detailed scoring
    """
    # Load expected output
    expected = test_case.expected_output
    if not expected:
        return {
            "passed": False,
            "score": 0.0,
            "metrics": {"error": "No expected output defined"}
        }
    
    # Check 1: Formulas present
    has_formulas = check_formulas_present(model_output)
    
    # Check 2: Extract actual tax amounts from output
    extracted = extract_tax_amounts(model_output)
    
    # Calculate expected tax amounts
    year = test_case.input.get('year', 2025)
    income = test_case.input.get('income', 0)
    
    tax_params = load_tax_params(year)
    
    expected_federal = calculate_progressive_tax(
        income,
        tax_params['federal']['brackets'],
        tax_params['federal']['basic_personal_amount']
    )
    
    expected_bc = calculate_progressive_tax(
        income,
        tax_params['bc']['brackets'],
        tax_params['bc']['basic_personal_amount']
    )
    
    expected_total = expected_federal + expected_bc
    
    # Compare with tolerance of ±$1
    tolerance = 1.0
    
    federal_correct = False
    bc_correct = False
    total_correct = False
    
    federal_error = None
    bc_error = None
    total_error = None
    
    if 'federal_tax' in extracted:
        federal_error = abs(extracted['federal_tax'] - expected_federal)
        federal_correct = federal_error <= tolerance
    
    if 'bc_tax' in extracted:
        bc_error = abs(extracted['bc_tax'] - expected_bc)
        bc_correct = bc_error <= tolerance
    
    if 'total_tax' in extracted:
        total_error = abs(extracted['total_tax'] - expected_total)
        total_correct = total_error <= tolerance
    
    # Scoring
    # - 40% for having formulas
    # - 60% for numerical accuracy (20% each for federal, BC, total)
    score = 0.0
    
    if has_formulas:
        score += 0.4
    
    if federal_correct:
        score += 0.2
    if bc_correct:
        score += 0.2
    if total_correct:
        score += 0.2
    
    passed = (score >= 0.8)  # Need at least 80% to pass
    
    metrics = {
        "has_formulas": has_formulas,
        "expected_federal_tax": expected_federal,
        "expected_bc_tax": expected_bc,
        "expected_total_tax": expected_total,
        "extracted_federal_tax": extracted.get('federal_tax'),
        "extracted_bc_tax": extracted.get('bc_tax'),
        "extracted_total_tax": extracted.get('total_tax'),
        "federal_error": federal_error,
        "bc_error": bc_error,
        "total_error": total_error,
        "federal_correct": federal_correct,
        "bc_correct": bc_correct,
        "total_correct": total_correct,
    }
    
    return {
        "passed": passed,
        "score": score,
        "metrics": metrics
    }

