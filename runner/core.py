"""
Core evaluation runner with YAML spec loading, provider abstraction, and cost tracking.
"""

import importlib.util
import json
import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from jinja2 import Template


@dataclass
class TestCase:
    """Individual test case within an evaluation"""
    case_id: str
    input: Dict[str, Any]
    expected_output: Optional[Any] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CostMetrics:
    """Token usage and cost tracking"""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
    
    def add(self, input_tokens: int, output_tokens: int, cost: float):
        """Add token counts and costs"""
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.total_tokens += input_tokens + output_tokens
        self.estimated_cost_usd += cost


@dataclass
class EvalResult:
    """Result from running a single test case"""
    case_id: str
    status: str  # "pass", "fail", "error"
    model_output: Any
    score: Optional[float] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    latency_ms: Optional[float] = None
    error_message: Optional[str] = None
    cost: Optional[CostMetrics] = None


@dataclass
class EvalRun:
    """Complete evaluation run with all results"""
    run_id: str
    suite_name: str
    suite_version: str
    model_name: str
    provider: str
    timestamp: str
    hyperparameters: Dict[str, Any]
    cases: List[EvalResult]
    aggregates: Dict[str, Any] = field(default_factory=dict)
    total_cost: Optional[CostMetrics] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "run_id": self.run_id,
            "suite_name": self.suite_name,
            "suite_version": self.suite_version,
            "model": self.model_name,
            "provider": self.provider,
            "timestamp": self.timestamp,
            "hyperparameters": self.hyperparameters,
            "cases": [
                {
                    "case_id": case.case_id,
                    "status": case.status,
                    "model_output": case.model_output,
                    "score": case.score,
                    "metrics": case.metrics,
                    "latency_ms": case.latency_ms,
                    "error_message": case.error_message,
                    "cost": {
                        "input_tokens": case.cost.input_tokens,
                        "output_tokens": case.cost.output_tokens,
                        "total_tokens": case.cost.total_tokens,
                        "estimated_cost_usd": case.cost.estimated_cost_usd
                    } if case.cost else None
                }
                for case in self.cases
            ],
            "aggregates": self.aggregates,
            "total_cost": {
                "input_tokens": self.total_cost.input_tokens,
                "output_tokens": self.total_cost.output_tokens,
                "total_tokens": self.total_cost.total_tokens,
                "estimated_cost_usd": self.total_cost.estimated_cost_usd
            } if self.total_cost else None,
            "metadata": self.metadata
        }


class EvalSpec:
    """Evaluation specification loaded from YAML"""
    
    # Security constants
    MAX_SPEC_FILE_SIZE_MB = 10  # Max size for spec.yaml files
    MAX_FIXTURE_FILE_SIZE_MB = 50  # Max size for fixture files
    
    def __init__(self, spec_path: Path):
        self.spec_path = spec_path
        self.eval_dir = spec_path.parent
        
        # Security: Check spec file size
        spec_size_mb = spec_path.stat().st_size / (1024 * 1024)
        if spec_size_mb > self.MAX_SPEC_FILE_SIZE_MB:
            raise ValueError(
                f"Spec file too large: {spec_size_mb:.2f}MB "
                f"(max: {self.MAX_SPEC_FILE_SIZE_MB}MB)"
            )
        
        with open(spec_path, 'r') as f:
            self.spec = yaml.safe_load(f)
        
        # Security: Validate spec schema
        self._validate_spec_schema()
        
        self.id = self.spec['id']
        self.version = self.spec.get('version', '1.0.0')
        self.task_type = self.spec['task_type']
        self.description = self.spec.get('description', '')
        self.prompt_template_path = self.spec.get('prompt_template')
        self.constraints = self.spec.get('constraints', {})
        self.metrics = self.spec.get('metrics', [])
        self.scorer_path = self.spec.get('scorer', 'scorer.py')
        
        # Load test cases from fixtures
        self.test_cases = self._load_test_cases()
        
        # Load scorer module
        self.scorer = self._load_scorer()
    
    def _load_test_cases(self) -> List[TestCase]:
        """Load test cases from fixtures defined in spec"""
        cases = []
        fixtures_config = self.spec.get('fixtures', [])
        
        for fixture in fixtures_config:
            case_id = fixture.get('case_id', str(uuid.uuid4()))
            input_data = fixture.get('input', {})
            expected_output = fixture.get('expected_output')
            metadata = fixture.get('metadata', {})
            
            cases.append(TestCase(
                case_id=case_id,
                input=input_data,
                expected_output=expected_output,
                metadata=metadata
            ))
        
        return cases
    
    def _load_scorer(self):
        """Dynamically load the scorer module"""
        scorer_path = self.eval_dir / self.scorer_path
        if not scorer_path.exists():
            raise FileNotFoundError(f"Scorer not found: {scorer_path}")
        
        spec = importlib.util.spec_from_file_location("scorer", scorer_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load scorer from {scorer_path}")
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        return module
    
    def _validate_spec_schema(self):
        """Validate that spec YAML has required fields"""
        required_fields = ['id', 'task_type']
        missing_fields = [field for field in required_fields if field not in self.spec]
        
        if missing_fields:
            raise ValueError(
                f"Invalid spec schema: missing required fields: {missing_fields}"
            )
        
        # Validate task_type is a known value
        valid_task_types = [
            'spreadsheet_generation',
            'structured_output',
            'knowledge_recall',
            'prompt_injection',
            'long_context_coherence',
            'tool_selection',
            'custom'
        ]
        task_type = self.spec.get('task_type')
        if task_type not in valid_task_types:
            # Warning only - allow custom task types
            pass
        
        # Validate fixtures if present
        if 'fixtures' in self.spec:
            if not isinstance(self.spec['fixtures'], list):
                raise ValueError("'fixtures' must be a list")
    
    def _check_fixture_file_size(self, file_path: Path):
        """Security: Check fixture file size"""
        if not file_path.exists():
            return  # File doesn't exist - let normal error handling deal with it
        
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.MAX_FIXTURE_FILE_SIZE_MB:
            raise ValueError(
                f"Fixture file too large: {file_path.name} is {file_size_mb:.2f}MB "
                f"(max: {self.MAX_FIXTURE_FILE_SIZE_MB}MB)"
            )
    
    def render_prompt(self, test_case: TestCase) -> str:
        """Render prompt template with test case input"""
        if not self.prompt_template_path:
            # If no template, just use the input as a simple prompt
            return str(test_case.input.get('prompt', ''))
        
        template_path = self.eval_dir / self.prompt_template_path
        with open(template_path, 'r') as f:
            template_str = f.read()
        
        # Prepare template variables
        template_vars = dict(test_case.input)
        
        # Handle multi-turn conversations if conversation_file is specified
        if 'conversation_file' in test_case.input:
            conversation_data = self._load_conversation(test_case)
            template_vars['conversation'] = conversation_data['conversation_text']
            # Store conversation history in metadata for scorer
            test_case.metadata['conversation_history'] = conversation_data['conversation_history']
        
        template = Template(template_str)
        return template.render(**template_vars)
    
    def _load_conversation(self, test_case: TestCase) -> Dict[str, Any]:
        """Load and format conversation from YAML file"""
        conversation_file = test_case.input['conversation_file']
        conversation_path = self.eval_dir / "fixtures" / conversation_file
        
        # Security: Check fixture file size
        self._check_fixture_file_size(conversation_path)
        
        with open(conversation_path, 'r') as f:
            data = yaml.safe_load(f)
        
        conversation = data.get('conversation', [])
        
        # Build formatted conversation text
        conversation_text = []
        user_messages = []
        
        for msg in conversation:
            role = msg.get('role')
            content = msg.get('content', '').strip()
            day = msg.get('day', '')
            
            if role == 'user' and content:
                conversation_text.append(f"[Day {day}] User: {content}")
                user_messages.append(content)
            elif role == 'assistant' and content:
                conversation_text.append(f"[Day {day}] Assistant: {content}")
        
        # Join with double newlines for readability
        formatted_conversation = "\n\n".join(conversation_text)
        
        # Build conversation history string for scorer
        history_text = []
        for msg in conversation:
            role = msg.get('role')
            content = msg.get('content', '').strip()
            day = msg.get('day', '')
            
            if content:
                history_text.append(f"[Day {day}] {role.upper()}: {content}")
        
        conversation_history = "\n\n".join(history_text)
        
        return {
            "conversation_text": formatted_conversation,
            "user_messages": user_messages,
            "conversation_history": conversation_history,
            "message_count": len([m for m in conversation if m.get('content')])
        }


class EvalRunner:
    """Main evaluation runner"""
    
    def __init__(self, results_dir: Path = Path("results")):
        self.results_dir = results_dir
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.providers = {}
    
    def register_provider(self, name: str, provider):
        """Register a model provider"""
        self.providers[name] = provider
    
    def run_eval(
        self,
        eval_spec: EvalSpec,
        model_name: str,
        provider_name: str,
        temperature: float = 0.2,
        max_tokens: int = 2048,
        seed: Optional[int] = None
    ) -> EvalRun:
        """Run a complete evaluation"""
        
        # Input validation
        if provider_name not in self.providers:
            raise ValueError(f"Provider not registered: {provider_name}")
        
        # Sanitize model name (prevent injection attacks)
        if not model_name or not isinstance(model_name, str):
            raise ValueError("Model name must be a non-empty string")
        if any(char in model_name for char in ['..', '/', '\\', '\n', '\r', ';', '|', '&']):
            raise ValueError(f"Invalid model name: contains unsafe characters")
        
        # Validate temperature
        if not 0.0 <= temperature <= 2.0:
            raise ValueError(f"Temperature must be between 0.0 and 2.0, got {temperature}")
        
        # Validate max_tokens
        if not 1 <= max_tokens <= 100000:
            raise ValueError(f"Max tokens must be between 1 and 100000, got {max_tokens}")
        
        provider = self.providers[provider_name]
        
        # Create run metadata
        run_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        hyperparameters = {
            "temperature": temperature,
            "max_tokens": max_tokens,
            "seed": seed
        }
        
        # Override with spec constraints if provided
        hyperparameters.update(eval_spec.constraints)
        
        # Run all test cases
        results = []
        total_cost = CostMetrics()
        
        for test_case in eval_spec.test_cases:
            print(f"Running case: {test_case.case_id}")
            
            try:
                # Render prompt
                prompt = eval_spec.render_prompt(test_case)
                
                # Call model
                start_time = time.time()
                response = provider.generate(
                    model=model_name,
                    prompt=prompt,
                    **hyperparameters
                )
                latency_ms = (time.time() - start_time) * 1000
                
                # Track costs
                case_cost = CostMetrics()
                if hasattr(response, 'usage'):
                    input_tokens = getattr(response.usage, 'input_tokens', 0) or getattr(response.usage, 'prompt_tokens', 0)
                    output_tokens = getattr(response.usage, 'output_tokens', 0) or getattr(response.usage, 'completion_tokens', 0)
                    
                    # Estimate cost (rough approximation, adjust per model)
                    cost_per_1k_input = 0.01  # $0.01 per 1K input tokens (average)
                    cost_per_1k_output = 0.03  # $0.03 per 1K output tokens (average)
                    estimated_cost = (
                        (input_tokens / 1000 * cost_per_1k_input) +
                        (output_tokens / 1000 * cost_per_1k_output)
                    )
                    
                    case_cost.add(input_tokens, output_tokens, estimated_cost)
                    total_cost.add(input_tokens, output_tokens, estimated_cost)
                
                # Score the output
                model_output = response.text if hasattr(response, 'text') else str(response)
                score_result = eval_spec.scorer.score(
                    test_case=test_case,
                    model_output=model_output,
                    eval_spec=eval_spec
                )
                
                # Create result
                result = EvalResult(
                    case_id=test_case.case_id,
                    status="pass" if score_result.get('passed', False) else "fail",
                    model_output=model_output,
                    score=score_result.get('score'),
                    metrics=score_result.get('metrics', {}),
                    latency_ms=latency_ms,
                    cost=case_cost
                )
                
            except Exception as e:
                print(f"Error running case {test_case.case_id}: {e}")
                result = EvalResult(
                    case_id=test_case.case_id,
                    status="error",
                    model_output=None,
                    error_message=str(e),
                    cost=CostMetrics()
                )
            
            results.append(result)
        
        # Calculate aggregates
        passed_cases = sum(1 for r in results if r.status == "pass")
        total_cases = len(results)
        pass_rate = passed_cases / total_cases if total_cases > 0 else 0.0
        
        avg_score = None
        scored_cases = [r for r in results if r.score is not None]
        if scored_cases:
            avg_score = sum(r.score for r in scored_cases) / len(scored_cases)
        
        avg_latency = None
        latency_cases = [r for r in results if r.latency_ms is not None]
        if latency_cases:
            avg_latency = sum(r.latency_ms for r in latency_cases) / len(latency_cases)
        
        aggregates = {
            "pass_rate": pass_rate,
            "passed_cases": passed_cases,
            "total_cases": total_cases,
            "avg_score": avg_score,
            "avg_latency_ms": avg_latency
        }
        
        # Create eval run
        eval_run = EvalRun(
            run_id=run_id,
            suite_name=eval_spec.id,
            suite_version=eval_spec.version,
            model_name=model_name,
            provider=provider_name,
            timestamp=datetime.now().isoformat(),
            hyperparameters=hyperparameters,
            cases=results,
            aggregates=aggregates,
            total_cost=total_cost,
            metadata={"eval_dir": str(eval_spec.eval_dir)}
        )
        
        # Save results
        self._save_results(eval_run)
        
        return eval_run
    
    def _save_results(self, eval_run: EvalRun):
        """Save evaluation results to JSON"""
        output_file = self.results_dir / f"{eval_run.run_id}.json"
        with open(output_file, 'w') as f:
            json.dump(eval_run.to_dict(), f, indent=2)
        
        print(f"\n✅ Results saved to: {output_file}")

