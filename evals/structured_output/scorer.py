"""
Scorer for Structured Output evaluation.

Validates:
1. Syntactic validity (can it be parsed?)
2. Schema compliance (all required fields present?)
3. No extraneous text (just the structured data)
"""

import csv
import io
import json
import re
import xml.etree.ElementTree as ET
from typing import Any, Dict


def extract_code_block(text: str, format_type: str) -> str:
    """
    Extract content from markdown code blocks if present.
    
    Example:
        ```json
        {"key": "value"}
        ```
    """
    # Try to find code block with format specifier
    pattern = f'```{format_type.lower()}\\s*\\n(.*?)\\n```'
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    # Try generic code block
    pattern = r'```\s*\n(.*?)\n```'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    
    return text.strip()


def validate_json(output: str, required_fields: list) -> Dict[str, Any]:
    """Validate JSON output"""
    # Extract from code block if present
    clean_output = extract_code_block(output, 'json')
    
    try:
        parsed = json.loads(clean_output)
    except json.JSONDecodeError as e:
        return {
            "parse_valid": False,
            "schema_compliance": False,
            "no_extra_text": False,
            "error": f"JSON parse error: {str(e)}"
        }
    
    # Check required fields
    missing_fields = [field for field in required_fields if field not in parsed]
    schema_compliant = len(missing_fields) == 0
    
    # Check for extra text (if output != clean extracted JSON)
    reconstructed = json.dumps(parsed, separators=(',', ':'))
    no_extra = (clean_output.replace(' ', '').replace('\n', '') == 
                reconstructed.replace(' ', '').replace('\n', ''))
    
    # More lenient check: just see if there's non-JSON text outside code blocks
    if '```' in output:
        # If it was in a code block, that's acceptable
        no_extra = True
    else:
        # Check if there's significant text before/after JSON
        json_start = output.find('{') if '{' in output else output.find('[')
        json_end = output.rfind('}') if '}' in output else output.rfind(']')
        if json_start >= 0 and json_end >= 0:
            before = output[:json_start].strip()
            after = output[json_end+1:].strip()
            # Allow small annotations but not paragraphs
            no_extra = len(before) < 50 and len(after) < 50
        else:
            no_extra = False
    
    return {
        "parse_valid": True,
        "schema_compliance": schema_compliant,
        "no_extra_text": no_extra,
        "missing_fields": missing_fields,
        "parsed_data": parsed
    }


def validate_xml(output: str, required_fields: list) -> Dict[str, Any]:
    """Validate XML output"""
    # Extract from code block if present
    clean_output = extract_code_block(output, 'xml')
    
    try:
        root = ET.fromstring(clean_output)
    except ET.ParseError as e:
        return {
            "parse_valid": False,
            "schema_compliance": False,
            "no_extra_text": False,
            "error": f"XML parse error: {str(e)}"
        }
    
    # Check required fields (as child elements)
    found_fields = {child.tag for child in root}
    missing_fields = [field for field in required_fields if field not in found_fields]
    schema_compliant = len(missing_fields) == 0
    
    # Check for extra text
    if '```' in output:
        no_extra = True
    else:
        xml_start = output.find('<')
        xml_end = output.rfind('>') + 1
        if xml_start >= 0 and xml_end > 0:
            before = output[:xml_start].strip()
            after = output[xml_end:].strip()
            no_extra = len(before) < 50 and len(after) < 50
        else:
            no_extra = False
    
    return {
        "parse_valid": True,
        "schema_compliance": schema_compliant,
        "no_extra_text": no_extra,
        "missing_fields": missing_fields,
        "found_fields": list(found_fields)
    }


def validate_csv(output: str, required_columns: list) -> Dict[str, Any]:
    """Validate CSV output"""
    # Extract from code block if present
    clean_output = extract_code_block(output, 'csv')
    
    try:
        # Parse CSV
        reader = csv.DictReader(io.StringIO(clean_output))
        rows = list(reader)
        
        if not rows:
            return {
                "parse_valid": False,
                "schema_compliance": False,
                "no_extra_text": False,
                "error": "CSV has no data rows"
            }
        
        # Check required columns
        actual_columns = reader.fieldnames or []
        missing_columns = [col for col in required_columns if col not in actual_columns]
        schema_compliant = len(missing_columns) == 0
        
        # Check for extra text
        if '```' in output:
            no_extra = True
        else:
            # Simple check: CSV should start near beginning
            csv_start = 0
            for i, char in enumerate(output):
                if char.strip():
                    csv_start = i
                    break
            no_extra = csv_start < 50
        
        return {
            "parse_valid": True,
            "schema_compliance": schema_compliant,
            "no_extra_text": no_extra,
            "missing_columns": missing_columns,
            "actual_columns": actual_columns,
            "row_count": len(rows)
        }
        
    except Exception as e:
        return {
            "parse_valid": False,
            "schema_compliance": False,
            "no_extra_text": False,
            "error": f"CSV parse error: {str(e)}"
        }


def score(test_case, model_output: str, eval_spec) -> Dict[str, Any]:
    """
    Score the structured output.
    
    Returns dict with:
    - passed: bool
    - score: float (0.0 to 1.0)
    - metrics: dict with detailed validation results
    """
    expected = test_case.expected_output
    if not expected:
        return {
            "passed": False,
            "score": 0.0,
            "metrics": {"error": "No expected output defined"}
        }
    
    format_type = expected.get('format', '').lower()
    
    # Route to appropriate validator
    if format_type == 'json':
        required_fields = expected.get('required_fields', [])
        result = validate_json(model_output, required_fields)
    elif format_type == 'xml':
        required_fields = expected.get('required_fields', [])
        result = validate_xml(model_output, required_fields)
    elif format_type == 'csv':
        required_columns = expected.get('required_columns', [])
        result = validate_csv(model_output, required_columns)
    else:
        return {
            "passed": False,
            "score": 0.0,
            "metrics": {"error": f"Unknown format type: {format_type}"}
        }
    
    # Calculate score
    # Equal weight to each criterion
    score = 0.0
    if result.get('parse_valid', False):
        score += 0.4
    if result.get('schema_compliance', False):
        score += 0.4
    if result.get('no_extra_text', False):
        score += 0.2
    
    passed = (score >= 0.8)  # Need parse + schema to pass
    
    return {
        "passed": passed,
        "score": score,
        "metrics": result
    }

