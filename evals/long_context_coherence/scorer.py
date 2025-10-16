"""
Scorer for Long-Context Coherence evaluation.

Hybrid scoring:
1. Entity extraction (50%): Regex/pattern matching for planted facts
2. LLM-as-judge (50%): Claude evaluation for constraint adherence
"""

import os
import re
from typing import Any, Dict, List


def extract_entities(output: str, expected_entities: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract planted entities from model output using pattern matching.
    
    Returns dict with:
        - found_entities: list of entity keys found
        - missing_entities: list of entity keys missing
        - retention_score: percentage found
    """
    found = []
    missing = []
    
    # Normalize output for searching
    output_lower = output.lower()
    
    # Check each expected entity
    for key, value in expected_entities.items():
        if key == "team":
            # Look for "Vancouver Canucks"
            if re.search(r'vancouver\s+canucks', output_lower):
                found.append(key)
            else:
                missing.append(key)
        
        elif key == "budget":
            # Look for $65k or $65,000 (updated value, NOT $50k)
            if re.search(r'\$\s*65[,\s]*[k0]{3}', output_lower) or re.search(r'\$65,000', output_lower) or re.search(r'\$65k', output_lower):
                found.append(key)
            # Check if outdated value is used (should be penalized)
            elif re.search(r'\$\s*50[,\s]*[k0]{3}', output_lower) or re.search(r'\$50,000', output_lower) or re.search(r'\$50k', output_lower):
                missing.append(key + "_outdated")
            else:
                missing.append(key)
        
        elif key == "deadline":
            # Look for March 30, 2025 (updated, NOT March 15)
            if re.search(r'march\s+30', output_lower):
                found.append(key)
            # Check if outdated deadline used
            elif re.search(r'march\s+15', output_lower):
                missing.append(key + "_outdated")
            else:
                missing.append(key)
        
        elif key == "lead":
            # Look for "Sarah Chen"
            if re.search(r'sarah\s+chen', output_lower):
                found.append(key)
            else:
                missing.append(key)
        
        elif key == "requirements":
            # Check for both requirements
            req_found = []
            if re.search(r'player\s+performance', output_lower):
                req_found.append("player_performance")
            if re.search(r'injury\s+prediction', output_lower):
                req_found.append("injury_prediction")
            
            if len(req_found) == 2:
                found.append(key)
            elif len(req_found) == 1:
                found.append(key + "_partial")
            else:
                missing.append(key)
        
        elif key == "data_constraint":
            # Look for "2024-2025 season" (with possible words in between like "NHL season")
            if re.search(r'2024[-\s/]*2025.*?season', output_lower):
                found.append(key)
            else:
                missing.append(key)
    
    total_entities = len(expected_entities)
    retention_score = len([k for k in found if not k.endswith("_partial")]) / total_entities
    
    return {
        "found_entities": found,
        "missing_entities": missing,
        "retention_score": retention_score,
        "total_entities": total_entities
    }


def judge_with_llm(
    conversation: str,
    final_output: str,
    expected_entities: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Use Claude Sonnet 4 as judge to evaluate constraint adherence.
    
    Returns dict with:
        - judge_score: 0-10 score
        - normalized_score: 0-1 score
        - reasoning: judge's explanation
    """
    # Construct judge prompt
    judge_prompt = f"""You are evaluating an AI assistant's performance in a multi-turn conversation task.

CONVERSATION HISTORY:
{conversation}

ASSISTANT'S FINAL OUTPUT:
{final_output}

EXPECTED INFORMATION (based on conversation):
- Team: Vancouver Canucks
- Budget: $65,000 (UPDATED from initial $50,000)
- Deadline: March 30, 2025 (UPDATED from initial March 15, 2025)
- Team Lead: Sarah Chen
- Requirements: Player performance metrics AND injury prediction
- Data Constraint: Only 2024-2025 season data

SCORING RUBRIC (0-10 points):
1. Uses UPDATED budget ($65k, not $50k): 2 points
2. Uses UPDATED deadline (March 30, not March 15): 2 points
3. Includes team lead name (Sarah Chen): 1 point
4. Includes ALL requirements (both player performance and injury prediction): 3 points
5. Mentions data constraint (2024-2025 season): 1 point
6. No contradictions with conversation history: 1 point

Provide your score (0-10) and brief reasoning. Format:
SCORE: <number>
REASONING: <explanation>
"""
    
    # Call Claude Sonnet 4 for judgment
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            temperature=0.0,
            messages=[{"role": "user", "content": judge_prompt}]
        )
        
        judge_output = response.content[0].text
        
        # Extract score
        score_match = re.search(r'SCORE:\s*(\d+)', judge_output)
        reasoning_match = re.search(r'REASONING:\s*(.+)', judge_output, re.DOTALL)
        
        if score_match:
            judge_score = int(score_match.group(1))
            judge_score = max(0, min(10, judge_score))  # Clamp to 0-10
        else:
            judge_score = 0
        
        reasoning = reasoning_match.group(1).strip() if reasoning_match else "No reasoning provided"
        
        return {
            "judge_score": judge_score,
            "normalized_score": judge_score / 10.0,
            "reasoning": reasoning,
            "judge_output": judge_output
        }
    
    except Exception as e:
        # Fallback if LLM judge fails
        return {
            "judge_score": 0,
            "normalized_score": 0.0,
            "reasoning": f"LLM judge error: {str(e)}",
            "judge_output": ""
        }


def score(test_case, model_output: str, eval_spec) -> Dict[str, Any]:
    """
    Score the model's long-context coherence.
    
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
    
    expected_entities = expected.get("entities", {})
    
    # 1. Entity extraction (programmatic)
    entity_results = extract_entities(model_output, expected_entities)
    entity_score = entity_results["retention_score"]
    
    # 2. LLM-as-judge (if API key available)
    # Build conversation history from test_case metadata
    conversation_history = test_case.metadata.get("conversation_history", "Conversation history not available")
    
    judge_results = judge_with_llm(
        conversation_history,
        model_output,
        expected_entities
    )
    judge_score = judge_results["normalized_score"]
    
    # 3. Composite score (50/50 weighted)
    composite_score = (entity_score * 0.5) + (judge_score * 0.5)
    
    # Pass threshold: 75%
    passed = composite_score >= 0.75
    
    metrics = {
        "entity_retention": entity_score,
        "entities_found": entity_results["found_entities"],
        "entities_missing": entity_results["missing_entities"],
        "judge_score_raw": judge_results["judge_score"],
        "judge_score_normalized": judge_score,
        "judge_reasoning": judge_results["reasoning"],
        "composite_score": composite_score,
    }
    
    return {
        "passed": passed,
        "score": composite_score,
        "metrics": metrics
    }

