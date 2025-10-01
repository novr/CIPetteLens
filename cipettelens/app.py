"""
Flask web application for CIPetteLens dashboard.
"""

import os

from dotenv import load_dotenv
from flask import Flask, render_template

# Load environment variables
load_dotenv()

app = Flask(__name__, template_folder='/app/templates', static_folder='/app/static')

# Configuration
app.config["DEBUG"] = os.getenv("FLASK_DEBUG", "False").lower() == "true"
app.config["PORT"] = int(os.getenv("FLASK_PORT", "5000"))


@app.route("/")
def dashboard():
    """Main dashboard route."""
    return render_template("dashboard.html")


def main():
    """Main entry point for the web application."""
    port = app.config["PORT"]
    debug = app.config["DEBUG"]

    print(f"Starting CIPetteLens web server on port {port}")
    print(f"Debug mode: {debug}")
    print(f"Access the dashboard at: http://localhost:{port}")

    app.run(host="0.0.0.0", port=port, debug=debug)


if __name__ == "__main__":
    main()
