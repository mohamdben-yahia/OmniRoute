#!/usr/bin/env python3
"""
Windsurf Unified Configuration Manager - Manages configuration for hybrid approach.

This module provides a unified configuration interface that:
1. Loads and saves configuration from windsurf_config.json
2. Updates configuration from passive health checks
3. Updates configuration from active API validations
4. Validates configuration freshness and completeness
5. Provides migration from old config format

Usage:
    from windsurf_unified_config import WindsurfConfig

    config = WindsurfConfig()

    # Update from health check
    health = windsurf_health_check()
    config.update_from_health(health)

    # Update from API validation
    validation = validate_windsurf_api(...)
    config.update_from_validation(validation)

    # Check if valid
    if config.is_valid():
        port = config.get("port")
        csrf_token = config.get("csrfToken")
"""

import json
import pathlib
from typing import Any, Optional
from datetime import datetime, timezone, timedelta


class WindsurfConfig:
    """Unified Windsurf configuration manager."""

    def __init__(self, config_path: Optional[pathlib.Path] = None):
        """
        Initialize configuration manager.

        Args:
            config_path: Path to config file (default: scripts/windsurf_config.json)
        """
        if config_path is None:
            config_path = pathlib.Path(__file__).parent / "windsurf_config.json"

        self.config_path = config_path
        self.config = self.load()

    def load(self) -> dict[str, Any]:
        """Load configuration from file."""
        if not self.config_path.exists():
            return self._default_config()

        try:
            config = json.loads(self.config_path.read_text(encoding="utf-8"))
            # Migrate old format if needed
            return self._migrate_config(config)
        except Exception:
            return self._default_config()

    def save(self) -> None:
        """Save configuration to file."""
        self.config_path.write_text(
            json.dumps(self.config, indent=2),
            encoding="utf-8"
        )

    def _default_config(self) -> dict[str, Any]:
        """Get default configuration structure."""
        return {
            "version": "2.0.0",
            "port": None,
            "languageServerPort": None,
            "epoch": None,
            "pid": None,
            "csrfToken": None,
            "lastUpdated": None,
            "lastHealthCheck": None,
            "lastValidation": None,
            "lastValidationResult": None,
            "lastValidationErrors": [],
            "status": "unknown"
        }

    def _migrate_config(self, config: dict[str, Any]) -> dict[str, Any]:
        """Migrate old config format to new format."""
        version = config.get("version", "1.0.0")

        if version == "2.0.0":
            return config

        # Migrate from 1.0.0 to 2.0.0
        migrated = self._default_config()
        migrated.update({
            "port": config.get("port"),
            "epoch": config.get("epoch"),
            "pid": config.get("pid"),
            "csrfToken": config.get("csrfToken"),
            "lastUpdated": config.get("lastUpdated"),
            "status": config.get("status", "unknown")
        })

        return migrated

    def update_from_health(self, health: dict[str, Any]) -> None:
        """
        Update configuration from passive health check results.

        Args:
            health: Results from windsurf_health_check()
        """
        self.config.update({
            "port": health.get("port"),
            "epoch": health.get("epoch"),
            "pid": health.get("pid"),
            "status": health.get("status"),
            "lastHealthCheck": datetime.now(timezone.utc).isoformat(),
            "lastUpdated": datetime.now(timezone.utc).isoformat()
        })

        self.save()

    def update_from_validation(
        self,
        validation: dict[str, Any],
        language_server_port: int
    ) -> None:
        """
        Update configuration from active API validation results.

        Args:
            validation: Results from validate_windsurf_api()
            language_server_port: Port used for validation
        """
        self.config.update({
            "languageServerPort": language_server_port,
            "lastValidation": datetime.now(timezone.utc).isoformat(),
            "lastValidationResult": "success" if validation.get("valid") else "failed",
            "lastValidationErrors": validation.get("errors", []),
            "lastUpdated": datetime.now(timezone.utc).isoformat()
        })

        self.save()

    def set_csrf_token(self, csrf_token: str) -> None:
        """
        Set CSRF token and mark as updated.

        Args:
            csrf_token: CSRF token value
        """
        self.config["csrfToken"] = csrf_token
        self.config["lastUpdated"] = datetime.now(timezone.utc).isoformat()
        self.save()

    def set_language_server_port(self, port: int) -> None:
        """
        Set Language Server port.

        Args:
            port: Language Server port (usually 59455)
        """
        self.config["languageServerPort"] = port
        self.config["lastUpdated"] = datetime.now(timezone.utc).isoformat()
        self.save()

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return self.config.get(key, default)

    def is_valid(self, max_age_minutes: float = 30.0) -> bool:
        """
        Check if configuration is valid and recent.

        Args:
            max_age_minutes: Maximum age for configuration to be considered valid

        Returns:
            True if configuration is valid and recent
        """
        # Check required fields
        if not self.config.get("port"):
            return False

        if not self.config.get("csrfToken"):
            return False

        # Check freshness
        last_updated = self.config.get("lastUpdated")
        if not last_updated:
            return False

        try:
            updated_time = datetime.fromisoformat(last_updated.replace("Z", "+00:00"))
            age = datetime.now(timezone.utc) - updated_time
            if age > timedelta(minutes=max_age_minutes):
                return False
        except Exception:
            return False

        # Check status
        status = self.config.get("status")
        if status not in ["alive", "stale"]:
            return False

        return True

    def needs_validation(self, validation_interval_minutes: float = 5.0) -> bool:
        """
        Check if API validation is needed.

        Args:
            validation_interval_minutes: Minimum interval between validations

        Returns:
            True if validation is needed
        """
        last_validation = self.config.get("lastValidation")

        if not last_validation:
            return True

        try:
            validation_time = datetime.fromisoformat(last_validation.replace("Z", "+00:00"))
            age = datetime.now(timezone.utc) - validation_time
            return age > timedelta(minutes=validation_interval_minutes)
        except Exception:
            return True

    def get_summary(self) -> dict[str, Any]:
        """
        Get configuration summary for display.

        Returns:
            dict with human-readable summary
        """
        return {
            "version": self.config.get("version"),
            "extensionServerPort": self.config.get("port"),
            "languageServerPort": self.config.get("languageServerPort"),
            "epoch": self.config.get("epoch"),
            "csrfConfigured": bool(self.config.get("csrfToken")),
            "status": self.config.get("status"),
            "lastHealthCheck": self.config.get("lastHealthCheck"),
            "lastValidation": self.config.get("lastValidation"),
            "lastValidationResult": self.config.get("lastValidationResult"),
            "isValid": self.is_valid(),
            "needsValidation": self.needs_validation()
        }

    def clear(self) -> None:
        """Clear configuration (reset to defaults)."""
        self.config = self._default_config()
        self.save()

    def __repr__(self) -> str:
        """String representation of configuration."""
        summary = self.get_summary()
        return f"WindsurfConfig(port={summary['extensionServerPort']}, valid={summary['isValid']})"


# Example usage
if __name__ == "__main__":
    print("=" * 70)
    print("Windsurf Unified Configuration Manager - Test")
    print("=" * 70)

    # Create config manager
    config = WindsurfConfig()

    print("\n[1/4] Current Configuration")
    print("-" * 70)
    summary = config.get_summary()
    for key, value in summary.items():
        print(f"{key:25s}: {value}")

    # Test health update
    print("\n[2/4] Simulating Health Check Update")
    print("-" * 70)
    mock_health = {
        "port": 53300,
        "epoch": "20260504T001558",
        "pid": 12116,
        "status": "alive",
        "lastActivity": datetime.now(timezone.utc).isoformat()
    }
    config.update_from_health(mock_health)
    print(f"Updated from health check: port={config.get('port')}, epoch={config.get('epoch')}")

    # Test validation update
    print("\n[3/4] Simulating API Validation Update")
    print("-" * 70)
    mock_validation = {
        "valid": True,
        "startCascade": True,
        "sendMessage": True,
        "errors": []
    }
    config.update_from_validation(mock_validation, language_server_port=59455)
    print(f"Updated from validation: languageServerPort={config.get('languageServerPort')}")
    print(f"Last validation result: {config.get('lastValidationResult')}")

    # Test validity checks
    print("\n[4/4] Validity Checks")
    print("-" * 70)
    print(f"Is valid: {config.is_valid()}")
    print(f"Needs validation: {config.needs_validation()}")

    print("\n[OK] Configuration manager test complete")
    print(f"\nConfig file: {config.config_path}")
