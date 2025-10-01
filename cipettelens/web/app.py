"""
Flask web application with clean architecture.
"""

from pathlib import Path

from flask import Flask, render_template

from ..config import config
from ..repositories.sqlite_metrics import SQLiteMetricsRepository
from ..services.metrics_service import MetricsService


def create_app() -> Flask:
    """Create and configure Flask application."""
    # Get the directory containing this file
    current_dir = Path(__file__).parent
    project_root = current_dir.parent.parent

    # Set template and static folders relative to project root
    template_folder = str(project_root / "templates")
    static_folder = str(project_root / "static")

    app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)

    # Configuration
    app.config["DEBUG"] = config.FLASK_DEBUG
    app.config["PORT"] = config.FLASK_PORT

    # Initialize dependencies
    metrics_repository = SQLiteMetricsRepository()
    metrics_service = MetricsService(metrics_repository)

    @app.route("/")
    def dashboard():
        """Main dashboard route."""
        return render_template("dashboard.html")

    @app.route("/api/health")
    def health():
        """Health check endpoint."""
        return {"status": "healthy", "version": "1.0.0"}

    @app.route("/api/metrics")
    def get_metrics():
        """Get metrics API endpoint."""
        try:
            metrics = metrics_service.get_all_metrics(limit=100)
            return {"metrics": metrics}
        except Exception as e:
            return {"error": str(e)}, 500

    return app


def main():
    """Main entry point for web application."""
    app = create_app()
    port = app.config["PORT"]
    debug = app.config["DEBUG"]

    print(f"Starting CIPetteLens web server on port {port}")
    print(f"Debug mode: {debug}")
    print(f"Access the dashboard at: http://localhost:{port}")

    app.run(host="0.0.0.0", port=port, debug=debug)
