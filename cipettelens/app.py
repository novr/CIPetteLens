"""
Legacy Flask web application for CIPetteLens dashboard.
This file is kept for backward compatibility.
Use cipettelens.web.app for new implementations.
"""

from .web.app import create_app, main

# Create app instance for backward compatibility
app = create_app()


if __name__ == "__main__":
    main()
