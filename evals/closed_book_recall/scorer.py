"""
Scorer for Closed-Book Knowledge Recall evaluation.

Validates:
1. Exact or acceptable answer match for known facts
2. Appropriate expression of uncertainty for unknowable questions
3. No hallucinations (making up answers)
"""

import re
from typing import Any, Dict


def normalize_answer(answer: str) -> str:
    """Normalize an answer for comparison"""
    # Convert to lowercase
    answer = answer.lower().strip()
    
    # Remove common punctuation
    answer = re.sub(r'[.,!?;]', '', answer)
    
    # Normalize whitespace
    answer = ' '.join(answer.split())
    
    return answer


def check_uncertainty_expression(text: str) -> bool:
    """Check if the text expresses uncertainty appropriately"""
    uncertainty_patterns = [
        r"i don't know",
        r"i do not know",
        r"i'm not (sure|certain)",
        r"i am not (sure|certain)",
        r"not certain",
        r"not sure",
        r"uncertain",
        r"cannot say",
        r"can't say",
        r"don't have (that|this) information",
        r"unable to (determine|provide|answer)",
    ]
    
    text_lower = text.lower()
    
    for pattern in uncertainty_patterns:
        if re.search(pattern, text_lower):
            return True
    
    return False


def check_hallucination(text: str, should_express_uncertainty: bool) -> bool:
    """
    Check if model hallucinated (gave confident answer when it should have been uncertain)
    
    Returns True if hallucination detected, False otherwise
    """
    if not should_express_uncertainty:
        # Not an unknowable question, so no hallucination possible
        return False
    
    # Check if model expressed uncertainty
    if check_uncertainty_expression(text):
        # Good - expressed uncertainty as expected
        return False
    
    # Model didn't express uncertainty but should have
    # Check if it gave a specific answer (likely hallucination)
    
    # If answer is very short and doesn't look like uncertainty
    if len(text.split()) < 20 and not check_uncertainty_expression(text):
        # Likely a fabricated answer
        return True
    
    return False


def check_answer_match(model_output: str, expected: Dict[str, Any]) -> tuple[bool, str]:
    """
    Check if model output matches expected answer.
    
    Returns (matched, match_type) where match_type is:
    - "exact": exact match found
    - "acceptable": one of acceptable answers matched
    - "none": no match
    """
    expected_answer = expected.get('answer')
    acceptable_answers = expected.get('acceptable_answers', [])
    
    if expected_answer is None:
        # This is an unknowable question
        return (False, "unknowable")
    
    normalized_output = normalize_answer(model_output)
    
    # Check exact expected answer
    if normalize_answer(expected_answer) in normalized_output:
        return (True, "exact")
    
    # Check acceptable variations
    for acceptable in acceptable_answers:
        if normalize_answer(acceptable) in normalized_output:
            return (True, "acceptable")
    
    return (False, "none")


def score(test_case, model_output: str, eval_spec) -> Dict[str, Any]:
    """
    Score the closed-book recall output.
    
    Returns dict with:
    - passed: bool
    - score: float (0.0 to 1.0)
    - metrics: dict with detailed scoring
    """
    expected = test_case.expected_output
    if not expected:
        return {
            "passed": False,
            "score": 0.0,
            "metrics": {"error": "No expected output defined"}
        }
    
    should_know = test_case.metadata.get('should_know', True)
    should_express_uncertainty = expected.get('should_express_uncertainty', False)
    
    # Check for answer match
    answer_matched, match_type = check_answer_match(model_output, expected)
    
    # Check for uncertainty expression
    expressed_uncertainty = check_uncertainty_expression(model_output)
    
    # Check for hallucination
    hallucinated = check_hallucination(model_output, should_express_uncertainty)
    
    # Calculate score
    score = 0.0
    
    if should_know:
        # For knowable questions
        if answer_matched:
            score = 1.0  # Correct answer
        elif expressed_uncertainty:
            score = 0.3  # At least didn't hallucinate
        else:
            score = 0.0  # Wrong answer
    else:
        # For unknowable questions
        if expressed_uncertainty:
            score = 1.0  # Correctly expressed uncertainty
        elif hallucinated:
            score = 0.0  # Hallucinated an answer
        else:
            score = 0.5  # Gave vague/unclear response
    
    passed = score >= 0.7
    
    metrics = {
        "should_know": should_know,
        "answer_matched": answer_matched,
        "match_type": match_type,
        "expressed_uncertainty": expressed_uncertainty,
        "hallucinated": hallucinated,
        "should_express_uncertainty": should_express_uncertainty,
        "model_output_length": len(model_output),
        "normalized_output": normalize_answer(model_output)[:200]  # First 200 chars
    }
    
    return {
        "passed": passed,
        "score": score,
        "metrics": metrics
    }

