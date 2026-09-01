# -*- coding: utf-8 -*-
import pytest
from domains.analyst.context_builder import AnalystContextBuilder
from domains.analyst.providers.openai_provider import OpenAIAnalystProvider
from domains.analyst.schemas import AnalystContext, StructuredAnalystOutput

class TestProviderFailures:
    @pytest.fixture
    def sample_context(self) -> AnalystContext:
        return AnalystContextBuilder.build_context(
            business_date="2026-06-12",
            facts_dict={"sales": 13092000, "labor_ratio": 0.355},
            alerts_list=[{"rule_id": "R-LAB-01", "severity": "HIGH", "actual_value": "35.5%", "threshold_value": "33.0%", "evidence_id": "EV-ALT-01"}],
            evidence_list=[{"evidence_id": "EV-ALT-01"}]
        )

    def test_provider_01_missing_api_key(self, sample_context):
        provider = OpenAIAnalystProvider(api_key=None, allow_fallback=False)
        output = provider.generate_brief(sample_context)
        assert output.status == "PROVIDER_UNAVAILABLE"
        assert output.actual_provider == "none"
        assert output.fallback_used is False
        assert output.fallback_reason == "MISSING_API_KEY"

    def test_provider_01_missing_api_key_with_explicit_fallback(self, sample_context):
        provider = OpenAIAnalystProvider(api_key=None, allow_fallback=True)
        output = provider.generate_brief(sample_context)
        assert output.status == "READY"
        assert output.requested_provider == "openai"
        assert output.actual_provider == "mock"
        assert output.fallback_used is True
        assert output.fallback_reason == "MISSING_API_KEY"

    def test_provider_02_timeout(self, sample_context):
        def timeout_mock(ctx):
            raise TimeoutError("Request timed out after 30s")
        
        provider = OpenAIAnalystProvider(api_key="sk-dummy", allow_fallback=False, mock_transport=timeout_mock)
        output = provider.generate_brief(sample_context)
        assert output.status == "PROVIDER_UNAVAILABLE"
        assert output.fallback_reason == "TIMEOUT"

    def test_provider_03_http_429_rate_limit(self, sample_context):
        def rate_limit_mock(ctx):
            raise Exception("HTTP 429 Too Many Requests: RateLimitExceeded")
        
        provider = OpenAIAnalystProvider(api_key="sk-dummy", allow_fallback=False, mock_transport=rate_limit_mock)
        output = provider.generate_brief(sample_context)
        assert output.status == "PROVIDER_UNAVAILABLE"
        assert output.fallback_reason == "RATE_LIMIT_429"

    def test_provider_04_http_500_server_error(self, sample_context):
        def server_error_mock(ctx):
            raise Exception("HTTP 500 InternalServerError from OpenAI API")
        
        provider = OpenAIAnalystProvider(api_key="sk-dummy", allow_fallback=False, mock_transport=server_error_mock)
        output = provider.generate_brief(sample_context)
        assert output.status == "PROVIDER_UNAVAILABLE"
        assert output.fallback_reason == "SERVER_ERROR_500"

    def test_provider_05_malformed_json(self, sample_context):
        def malformed_json_mock(ctx):
            return "MALFORMED_NON_JSON_STRING_<<<>>>"
        
        provider = OpenAIAnalystProvider(api_key="sk-dummy", allow_fallback=False, mock_transport=malformed_json_mock)
        output = provider.generate_brief(sample_context)
        assert output.status == "PROVIDER_UNAVAILABLE"
        assert output.fallback_reason == "MALFORMED_JSON"

    def test_provider_06_schema_invalid_response(self, sample_context):
        def schema_invalid_mock(ctx):
            return {"status": "INVALID_SCHEMA", "unknown_field": 123}
        
        provider = OpenAIAnalystProvider(api_key="sk-dummy", allow_fallback=False, mock_transport=schema_invalid_mock)
        output = provider.generate_brief(sample_context)
        assert output.status == "PROVIDER_UNAVAILABLE"
        assert output.fallback_reason == "SCHEMA_INVALID"

    def test_provider_07_empty_response(self, sample_context):
        def empty_mock(ctx):
            return ""
        
        provider = OpenAIAnalystProvider(api_key="sk-dummy", allow_fallback=False, mock_transport=empty_mock)
        output = provider.generate_brief(sample_context)
        assert output.status == "PROVIDER_UNAVAILABLE"
        assert output.fallback_reason == "EMPTY_RESPONSE"

    def test_provider_08_unexpected_exception(self, sample_context):
        def exception_mock(ctx):
            raise RuntimeError("Unexpected OS socket disconnection")
        
        provider = OpenAIAnalystProvider(api_key="sk-dummy", allow_fallback=False, mock_transport=exception_mock)
        output = provider.generate_brief(sample_context)
        assert output.status == "ERROR"
        assert output.fallback_reason == "UNEXPECTED_EXCEPTION"

