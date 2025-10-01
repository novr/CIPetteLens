"""
Flask web application with clean architecture.
"""

from pathlib import Path

from flask import Flask, jsonify, render_template, request

from ..config import config
from ..factories import create_metrics_repository, create_metrics_service


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

    # Initialize dependencies using factories
    metrics_repository = create_metrics_repository()
    metrics_service = create_metrics_service()

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
            limit = request.args.get("limit", 100, type=int)
            metrics = metrics_service.get_all_metrics(limit=limit)
            return jsonify({"metrics": [metric.to_dict() for metric in metrics]})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/metrics/<repository>")
    def get_metrics_by_repository(repository: str):
        """Get metrics for a specific repository."""
        try:
            limit = request.args.get("limit", 100, type=int)
            metrics = metrics_service.get_metrics_by_repository(repository, limit=limit)
            return jsonify({"metrics": [metric.to_dict() for metric in metrics]})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/metrics/<repository>/latest")
    def get_latest_metrics(repository: str):
        """Get latest metrics for a specific repository."""
        try:
            latest = metrics_repository.get_latest_metrics_by_repository(repository)
            if latest:
                return jsonify({"metrics": latest.to_dict()})
            else:
                return jsonify({"error": "No metrics found for repository"}), 404
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/metrics/<repository>/<metric_name>/history")
    def get_metric_history(repository: str, metric_name: str):
        """Get metric history for a specific repository and metric."""
        try:
            limit = request.args.get("limit", 100, type=int)
            history = metrics_repository.get_metric_history(
                repository, metric_name, limit
            )
            return jsonify({"history": history})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/repositories")
    def get_repositories():
        """Get list of all repositories."""
        try:
            repositories = metrics_repository.get_repositories()
            return jsonify({"repositories": repositories})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/metric-names")
    def get_metric_names():
        """Get list of all metric names."""
        try:
            metric_names = metrics_repository.get_metric_names()
            return jsonify({"metric_names": metric_names})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return app


def main():
    """Main entry point for web application."""
    app = create_app()
    port = app.config["PORT"]
    debug = app.config["DEBUG"]

    print(f"Starting CIPetteLens web server on port {port}")
    print(f"Debug mode: {debug}")
    print(f"Access the dashboard at: http://localhost:{port}")

    # Use localhost for security in production
    # S104: 0.0.0.0 is only used in debug mode for development
    host = "127.0.0.1" if not debug else "0.0.0.0"
    app.run(host=host, port=port, debug=debug)
