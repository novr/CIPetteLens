"""
Flask web application for CIPetteLens dashboard.
"""

from pathlib import Path

from flask import Flask, render_template

from .config import config

# Get the directory containing this file
current_dir = Path(__file__).parent
project_root = current_dir.parent

# Set template and static folders relative to project root
template_folder = str(project_root / "templates")
static_folder = str(project_root / "static")

app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)

# Configuration
app.config["DEBUG"] = config.FLASK_DEBUG
app.config["PORT"] = config.FLASK_PORT


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
