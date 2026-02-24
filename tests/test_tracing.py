"""Tests for OpenTelemetry tracing configuration."""

import os
from collections.abc import Generator
from unittest.mock import Mock, patch

import pytest

from app.core.tracing import configure_tracing


class TestTracingConfiguration:
    """Test tracing configuration with timeout."""

    @pytest.fixture(autouse=True)
    def setup_environment(self) -> Generator[None, None, None]:
        """Clean up environment before and after tests."""
        # Save original env vars
        original_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
        original_timeout = os.getenv("OTEL_EXPORTER_TIMEOUT")

        yield

        # Restore original env vars
        if original_endpoint:
            os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = original_endpoint
        elif "OTEL_EXPORTER_OTLP_ENDPOINT" in os.environ:
            del os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"]

        if original_timeout:
            os.environ["OTEL_EXPORTER_TIMEOUT"] = original_timeout
        elif "OTEL_EXPORTER_TIMEOUT" in os.environ:
            del os.environ["OTEL_EXPORTER_TIMEOUT"]

    def test_default_timeout_is_configured(self) -> None:
        """Test that default timeout is applied when env var not set."""
        os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = "https://api.honeycomb.io"
        if "OTEL_EXPORTER_TIMEOUT" in os.environ:
            del os.environ["OTEL_EXPORTER_TIMEOUT"]

        with patch("app.core.tracing.OTLPSpanExporter") as mock_exporter:
            configure_tracing()

            # Should be called with default timeout of 10 seconds
            mock_exporter.assert_called_once()
            call_kwargs = mock_exporter.call_args[1]
            assert "timeout" in call_kwargs
            assert call_kwargs["timeout"] == 10

    def test_custom_timeout_from_environment(self) -> None:
        """Test that timeout from environment variable is used."""
        os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = "https://api.honeycomb.io"
        os.environ["OTEL_EXPORTER_TIMEOUT"] = "15"

        with patch("app.core.tracing.OTLPSpanExporter") as mock_exporter:
            configure_tracing()

            # Should be called with custom timeout
            mock_exporter.assert_called_once()
            call_kwargs = mock_exporter.call_args[1]
            assert "timeout" in call_kwargs
            assert call_kwargs["timeout"] == 15

    def test_no_timeout_when_otlp_not_configured(self) -> None:
        """Test that exporter is not created when OTLP endpoint not configured."""
        if "OTEL_EXPORTER_OTLP_ENDPOINT" in os.environ:
            del os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"]

        with patch("app.core.tracing.OTLPSpanExporter") as mock_exporter:
            configure_tracing()

            # Exporter should not be called when endpoint not configured
            mock_exporter.assert_not_called()

    def test_timeout_prevents_indefinite_hangs(self) -> None:
        """Test that timeout parameter prevents indefinite hangs."""
        os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = "https://api.honeycomb.io"
        os.environ["OTEL_EXPORTER_TIMEOUT"] = "5"

        with patch("app.core.tracing.OTLPSpanExporter") as mock_exporter:
            # Create a mock exporter instance
            mock_instance = Mock()
            mock_exporter.return_value = mock_instance

            configure_tracing()

            # Verify timeout was passed to constructor
            call_kwargs = mock_exporter.call_args[1]
            assert call_kwargs["timeout"] == 5
