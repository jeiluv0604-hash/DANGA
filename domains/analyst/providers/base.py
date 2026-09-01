# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod
from domains.analyst.schemas import AnalystContext, StructuredAnalystOutput

class BaseAnalystProvider(ABC):
    @abstractmethod
    def generate_brief(self, context: AnalystContext) -> StructuredAnalystOutput:
        pass
