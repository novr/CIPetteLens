"""
Legacy lens module for running CIAnalyzer and processing results.
This file is kept for backward compatibility.
Use cipettelens.cli.collect for new implementations.
"""

from .cli.collect import collect_metrics


def main():
    """Main entry point for data collection."""
    collect_metrics()
