"""
Main entry point for CIPetteLens application.
"""

import sys
from pathlib import Path

from .cli.collect import collect_metrics
from .web.app import main as web_main

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def main():
    """Main entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == "web":
        web_main()
    else:
        collect_metrics()


if __name__ == "__main__":
    main()
