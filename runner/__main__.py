"""
Entry point for running the evaluation suite as a module.

Usage:
    python -m runner.cli list
    python -m runner.cli run <eval>
"""

from runner.cli import main

if __name__ == '__main__':
    main()

