"""
Tests for security module.
"""

import os
import tempfile
from unittest.mock import patch

from cipettelens.security import SecurityConfig


class TestSecurityConfig:
    """Test SecurityConfig class."""

    def test_validate_github_token_always_true(self):
        """Test GitHub token validation always returns True (validation disabled)."""
        # All tokens should pass validation since it's disabled
        test_tokens = [
            "ghp_1234567890abcdef1234567890abcdef12345678",
            "invalid_token",
            "",
            "any_token_format",
        ]

        for token in test_tokens:
            assert SecurityConfig.validate_github_token(token) is True

    def test_validate_repository_format_valid(self):
        """Test valid repository format validation."""
        valid_repos = [
            "owner/repo",
            "user-name/repo-name",
            "user_name/repo_name",
            "user.name/repo.name",
            "123/456",
        ]

        for repo in valid_repos:
            assert SecurityConfig.validate_repository_format(repo) is True

    def test_validate_repository_format_invalid(self):
        """Test invalid repository format validation."""
        invalid_repos = [
            "",
            "invalid",
            "owner/",
            "/repo",
            "owner/repo/extra",
            "owner repo",
            "owner@repo",
        ]

        for repo in invalid_repos:
            assert SecurityConfig.validate_repository_format(repo) is False

    def test_validate_port_valid(self):
        """Test valid port validation."""
        valid_ports = ["1", "80", "443", "5000", "65535"]

        for port in valid_ports:
            assert SecurityConfig.validate_port(port) is True

    def test_validate_port_invalid(self):
        """Test invalid port validation."""
        invalid_ports = ["0", "65536", "abc", "-1", "1.5", ""]

        for port in invalid_ports:
            assert SecurityConfig.validate_port(port) is False

    def test_mask_sensitive_data(self):
        """Test sensitive data masking."""
        # Test short data
        assert SecurityConfig.mask_sensitive_data("short") == "*****"

        # Test medium data
        result = SecurityConfig.mask_sensitive_data("12345678")
        assert len(result) == 8
        assert result == "********"

        # Test long data
        result = SecurityConfig.mask_sensitive_data("1234567890abcdef")
        assert len(result) == 16
        assert result.startswith("1234")
        assert result.endswith("cdef")
        assert "*" in result

    def test_create_secure_temp_file(self):
        """Test secure temporary file creation."""
        content = "sensitive_data"
        file_path = SecurityConfig.create_secure_temp_file(content, ".test")

        try:
            # Check file exists
            assert os.path.exists(file_path)

            # Check file permissions (should be 0o600)
            file_stat = os.stat(file_path)
            assert file_stat.st_mode & 0o777 == 0o600

            # Check content
            with open(file_path) as f:
                assert f.read() == content
        finally:
            # Clean up
            if os.path.exists(file_path):
                os.unlink(file_path)

    def test_secure_cleanup(self):
        """Test secure file cleanup."""
        # Create a test file
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".test") as f:
            f.write("test_content")
            file_path = f.name

        try:
            # Verify file exists
            assert os.path.exists(file_path)

            # Secure cleanup
            SecurityConfig.secure_cleanup(file_path)

            # Verify file is deleted
            assert not os.path.exists(file_path)
        except Exception:
            # Clean up if test fails
            if os.path.exists(file_path):
                os.unlink(file_path)
            raise

    @patch.dict(
        os.environ,
        {
            "GITHUB_TOKEN": "ghp_1234567890abcdef1234567890abcdef12345678",
            "TARGET_REPOSITORIES": "owner/repo1,owner/repo2",
            "FLASK_PORT": "5000",
        },
    )
    def test_validate_environment_valid(self):
        """Test environment validation with valid values."""
        errors = SecurityConfig.validate_environment()
        assert errors == {}

    @patch.dict(os.environ, {}, clear=True)
    def test_validate_environment_missing_token(self):
        """Test environment validation with missing token."""
        errors = SecurityConfig.validate_environment()
        assert "GITHUB_TOKEN" in errors
        assert "required" in errors["GITHUB_TOKEN"]

    @patch.dict(
        os.environ,
        {
            "GITHUB_TOKEN": "any_token_format",
            "TARGET_REPOSITORIES": "owner/repo1,owner/repo2",
            "FLASK_PORT": "5000",
        },
    )
    def test_validate_environment_any_token(self):
        """Test environment validation with any token format (validation disabled)."""
        errors = SecurityConfig.validate_environment()
        # Should not have any errors since token validation is disabled
        assert "GITHUB_TOKEN" not in errors

    @patch.dict(
        os.environ,
        {
            "GITHUB_TOKEN": "ghp_1234567890abcdef1234567890abcdef12345678",
            "TARGET_REPOSITORIES": "invalid-repo,owner/repo2",
            "FLASK_PORT": "5000",
        },
    )
    def test_validate_environment_invalid_repos(self):
        """Test environment validation with invalid repositories."""
        errors = SecurityConfig.validate_environment()
        assert "TARGET_REPOSITORIES" in errors
        assert "Invalid repository format" in errors["TARGET_REPOSITORIES"]

    @patch.dict(
        os.environ,
        {
            "GITHUB_TOKEN": "ghp_1234567890abcdef1234567890abcdef12345678",
            "TARGET_REPOSITORIES": "owner/repo1,owner/repo2",
            "FLASK_PORT": "99999",
        },
    )
    def test_validate_environment_invalid_port(self):
        """Test environment validation with invalid port."""
        errors = SecurityConfig.validate_environment()
        assert "FLASK_PORT" in errors
        assert "Invalid port number" in errors["FLASK_PORT"]

    def test_get_secure_log_message(self):
        """Test secure log message generation."""
        message = "Token: ghp_1234567890abcdef1234567890abcdef12345678"
        sensitive_data = "ghp_1234567890abcdef1234567890abcdef12345678"

        result = SecurityConfig.get_secure_log_message(message, sensitive_data)
        assert "ghp_" in result
        assert "****" in result
        assert "5678" in result
        assert sensitive_data not in result
