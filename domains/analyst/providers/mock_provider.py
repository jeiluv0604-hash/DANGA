# -*- coding: utf-8 -*-
from domains.analyst.providers.base import BaseAnalystProvider
from domains.analyst.schemas import AnalystContext, StructuredAnalystOutput
from domains.analyst.deterministic_brief import DeterministicAnalyst

class MockAnalystProvider(BaseAnalystProvider):
    """
    MockAnalystProvider:
    Default test & production-ready deterministic provider.
    Requires no external API keys, satisfies all safety guarantees.
    """
    def generate_brief(self, context: AnalystContext) -> StructuredAnalystOutput:
        output = DeterministicAnalyst.generate_brief(context)
        output.provider = "mock"
        output.model = "mock-analyst-gpt4o-mini-simulator"
        return output
