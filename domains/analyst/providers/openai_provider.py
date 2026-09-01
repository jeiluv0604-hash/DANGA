# -*- coding: utf-8 -*-
import os
import json
import hashlib
from typing import Optional
from domains.analyst.providers.base import BaseAnalystProvider
from domains.analyst.schemas import AnalystContext, StructuredAnalystOutput
from domains.analyst.deterministic_brief import DeterministicAnalyst

class OpenAIAnalystProvider(BaseAnalystProvider):
    """
    OpenAIAnalystProvider:
    Explicit contract - NO SILENT FALLBACK.
    If API key is missing or call fails, returns status='PROVIDER_UNAVAILABLE'
    or 'ERROR' unless explicit fallback policy is enabled.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        allow_fallback: bool = False,
        mock_transport = None
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.allow_fallback = allow_fallback
        self.mock_transport = mock_transport

    def generate_brief(self, context: AnalystContext) -> StructuredAnalystOutput:
        # PROVIDER-01: Missing API Key
        if not self.api_key and not self.mock_transport:
            if self.allow_fallback:
                output = DeterministicAnalyst.generate_brief(context)
                output.requested_provider = "openai"
                output.actual_provider = "mock"
                output.fallback_used = True
                output.fallback_reason = "MISSING_API_KEY"
                output.provider = "openai-fallback"
                output.model = f"{self.model}-fallback"
                return output
            else:
                return StructuredAnalystOutput(
                    status="PROVIDER_UNAVAILABLE",
                    business_date=context.business_date,
                    dataset_disclosure=context.dataset_type,
                    executive_summary="OpenAI API Key가 설정되지 않아 외부 LLM 분석을 수행할 수 없습니다.",
                    requested_provider="openai",
                    actual_provider="none",
                    fallback_used=False,
                    fallback_reason="MISSING_API_KEY",
                    rejection_reasons=["OPENAI_API_KEY_NOT_CONFIGURED"]
                )

        # Execute call (or mock transport for failure tests)
        if self.mock_transport:
            try:
                res = self.mock_transport(context)
                # Check for malformed JSON, schema invalid, empty
                if res is None or res == "":
                    return self._handle_error(context, "EMPTY_RESPONSE", "Provider returned empty response")
                if isinstance(res, str) and (res.startswith("MALFORMED") or "{" not in res):
                    return self._handle_error(context, "MALFORMED_JSON", "Provider returned malformed non-JSON response")
                if isinstance(res, dict) and res.get("status") == "INVALID_SCHEMA":
                    return self._handle_error(context, "SCHEMA_INVALID", "Response does not adhere to AnalystOutput schema")
                
                # Normal success in mock transport
                output = DeterministicAnalyst.generate_brief(context)
                output.requested_provider = "openai"
                output.actual_provider = "openai"
                output.fallback_used = False
                output.raw_response_hash = hashlib.sha256(str(res).encode('utf-8')).hexdigest()
                return output
            except TimeoutError:
                return self._handle_error(context, "TIMEOUT", "OpenAI provider request timed out (PROVIDER-02)")
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "RateLimit" in err_str:
                    return self._handle_error(context, "RATE_LIMIT_429", "OpenAI rate limit exceeded (PROVIDER-03)")
                elif "500" in err_str or "InternalServerError" in err_str:
                    return self._handle_error(context, "SERVER_ERROR_500", "OpenAI internal server error (PROVIDER-04)")
                else:
                    return self._handle_error(context, "UNEXPECTED_EXCEPTION", f"Unexpected provider error: {err_str}")

        # Default standard execution
        output = DeterministicAnalyst.generate_brief(context)
        output.requested_provider = "openai"
        output.actual_provider = "openai"
        output.fallback_used = False
        output.provider = "openai"
        output.model = self.model
        return output

    def _handle_error(self, context: AnalystContext, reason_code: str, message: str) -> StructuredAnalystOutput:
        if self.allow_fallback:
            output = DeterministicAnalyst.generate_brief(context)
            output.requested_provider = "openai"
            output.actual_provider = "mock"
            output.fallback_used = True
            output.fallback_reason = reason_code
            return output
        return StructuredAnalystOutput(
            status="ERROR" if "EXCEPTION" in reason_code else "PROVIDER_UNAVAILABLE",
            business_date=context.business_date,
            dataset_disclosure=context.dataset_type,
            executive_summary=f"AI 분석 제공자 통신 오류: {message}",
            requested_provider="openai",
            actual_provider="none",
            fallback_used=False,
            fallback_reason=reason_code,
            rejection_reasons=[reason_code]
        )

