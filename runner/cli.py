"""
Command-line interface for running evaluations.

Usage:
    python -m runner.cli list
    python -m runner.cli run <eval_dir> [--models MODEL1,MODEL2] [--temperature TEMP]
    python -m runner.cli report <run_id>
"""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from runner.core import EvalRunner, EvalSpec
from runner.providers.openai_provider import OpenAIProvider


def list_evals(evals_dir: Path = Path("evals")):
    """List all available evaluations"""
    if not evals_dir.exists():
        print(f"❌ Evals directory not found: {evals_dir}")
        return
    
    print("\n📋 Available Evaluations:\n")
    
    eval_dirs = [d for d in evals_dir.iterdir() if d.is_dir() and (d / "spec.yaml").exists()]
    
    if not eval_dirs:
        print("No evaluations found.")
        return
    
    for eval_dir in sorted(eval_dirs):
        spec_file = eval_dir / "spec.yaml"
        try:
            spec = EvalSpec(spec_file)
            print(f"  • {spec.id} (v{spec.version})")
            print(f"    {spec.description[:80]}..." if len(spec.description) > 80 else f"    {spec.description}")
            print(f"    Path: {eval_dir}")
            print()
        except Exception as e:
            print(f"  ⚠️  {eval_dir.name}: Error loading spec - {e}")
            print()


def run_eval(
    eval_path: str,
    models: str = "gpt-4o-mini",
    temperature: float = 0.2,
    max_tokens: int = 2048,
    seed: int = None
):
    """Run an evaluation"""
    # Load environment variables
    load_dotenv()
    
    # Resolve eval path
    eval_dir = Path(eval_path)
    if not eval_dir.exists():
        # Try as relative to evals/
        eval_dir = Path("evals") / eval_path
    
    if not eval_dir.exists():
        print(f"❌ Evaluation not found: {eval_path}")
        return 1
    
    spec_file = eval_dir / "spec.yaml"
    if not spec_file.exists():
        print(f"❌ spec.yaml not found in: {eval_dir}")
        return 1
    
    # Load eval spec
    try:
        spec = EvalSpec(spec_file)
    except Exception as e:
        print(f"❌ Error loading eval spec: {e}")
        return 1
    
    print(f"\n🚀 Running Evaluation: {spec.id} (v{spec.version})")
    print(f"   {spec.description}\n")
    
    # Parse models
    model_list = [m.strip() for m in models.split(',')]
    
    # Initialize runner
    runner = EvalRunner()
    
    # Register providers
    try:
        runner.register_provider("openai", OpenAIProvider())
    except ValueError as e:
        print(f"⚠️  OpenAI provider not available: {e}")
    
    try:
        from runner.providers.anthropic_provider import AnthropicProvider
        runner.register_provider("anthropic", AnthropicProvider())
    except ValueError as e:
        print(f"⚠️  Anthropic provider not available: {e}")
    except ImportError:
        print(f"⚠️  Anthropic provider not available: module not found")
    
    # TODO: Add Google provider when ready
    
    # Run for each model
    results = []
    for model in model_list:
        print(f"\n📊 Testing model: {model}")
        print("=" * 60)
        
        # Determine provider based on model name
        provider = "openai"  # Default
        if "claude" in model.lower():
            provider = "anthropic"
        elif "gemini" in model.lower():
            provider = "google"  # TODO: Add Google provider
        elif any(x in model.lower() for x in ["gpt", "o1", "o3"]):
            provider = "openai"
        
        try:
            eval_run = runner.run_eval(
                eval_spec=spec,
                model_name=model,
                provider_name=provider,
                temperature=temperature,
                max_tokens=max_tokens,
                seed=seed
            )
            
            results.append(eval_run)
            
            # Print summary
            print(f"\n✅ Completed: {eval_run.run_id}")
            print(f"   Pass rate: {eval_run.aggregates['pass_rate']:.1%}")
            if eval_run.aggregates.get('avg_score') is not None:
                print(f"   Avg score: {eval_run.aggregates['avg_score']:.3f}")
            if eval_run.total_cost:
                print(f"   Tokens: {eval_run.total_cost.total_tokens:,} "
                      f"(in: {eval_run.total_cost.input_tokens:,}, out: {eval_run.total_cost.output_tokens:,})")
                print(f"   Est. cost: ${eval_run.total_cost.estimated_cost_usd:.4f}")
            
        except Exception as e:
            print(f"\n❌ Error running eval: {e}")
            import traceback
            traceback.print_exc()
            return 1
    
    print(f"\n{'='*60}")
    print(f"✅ All evaluations complete!")
    print(f"   Results saved to: results/")
    
    return 0


def show_report(run_id: str):
    """Show report for a specific run"""
    import json
    
    results_file = Path("results") / f"{run_id}.json"
    if not results_file.exists():
        print(f"❌ Results not found: {run_id}")
        print(f"   Looking for: {results_file}")
        return 1
    
    with open(results_file, 'r') as f:
        run_data = json.load(f)
    
    print(f"\n📊 Evaluation Report: {run_data['run_id']}")
    print("=" * 60)
    print(f"Suite: {run_data['suite_name']} (v{run_data['suite_version']})")
    print(f"Model: {run_data['model']} ({run_data['provider']})")
    print(f"Timestamp: {run_data['timestamp']}")
    print(f"\nHyperparameters:")
    for key, value in run_data['hyperparameters'].items():
        print(f"  {key}: {value}")
    
    print(f"\nAggregate Results:")
    for key, value in run_data['aggregates'].items():
        if isinstance(value, float):
            print(f"  {key}: {value:.3f}")
        else:
            print(f"  {key}: {value}")
    
    if run_data.get('total_cost'):
        cost = run_data['total_cost']
        print(f"\nCost Metrics:")
        print(f"  Total tokens: {cost['total_tokens']:,}")
        print(f"  Input tokens: {cost['input_tokens']:,}")
        print(f"  Output tokens: {cost['output_tokens']:,}")
        print(f"  Estimated cost: ${cost['estimated_cost_usd']:.4f}")
    
    print(f"\nPer-Case Results:")
    for case in run_data['cases']:
        status_icon = "✅" if case['status'] == 'pass' else "❌" if case['status'] == 'fail' else "⚠️"
        print(f"\n  {status_icon} {case['case_id']}: {case['status']}")
        if case.get('score') is not None:
            print(f"     Score: {case['score']:.3f}")
        if case.get('latency_ms') is not None:
            print(f"     Latency: {case['latency_ms']:.0f}ms")
        if case.get('error_message'):
            print(f"     Error: {case['error_message']}")
    
    print("\n" + "=" * 60)
    
    return 0


def main():
    parser = argparse.ArgumentParser(description="LLM Evaluation Suite CLI")
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List available evaluations')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Run an evaluation')
    run_parser.add_argument('eval_path', help='Path to evaluation directory')
    run_parser.add_argument('--models', default='gpt-4o-mini', 
                          help='Comma-separated list of models to test')
    run_parser.add_argument('--temperature', type=float, default=0.2,
                          help='Temperature for generation')
    run_parser.add_argument('--max-tokens', type=int, default=2048,
                          help='Maximum tokens to generate')
    run_parser.add_argument('--seed', type=int, default=None,
                          help='Random seed for reproducibility')
    
    # Report command
    report_parser = subparsers.add_parser('report', help='Show report for a run')
    report_parser.add_argument('run_id', help='Run ID to show report for')
    
    args = parser.parse_args()
    
    if args.command == 'list':
        list_evals()
        return 0
    elif args.command == 'run':
        return run_eval(
            eval_path=args.eval_path,
            models=args.models,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            seed=args.seed
        )
    elif args.command == 'report':
        return show_report(args.run_id)
    else:
        parser.print_help()
        return 0


if __name__ == '__main__':
    sys.exit(main())

