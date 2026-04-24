"""Compatibility exports for role-agent classes.

Prefer importing from dedicated modules:
- app.services.agents.munger_agent
- app.services.agents.industry_agent
- app.services.agents.audit_agent
"""

from app.services.agents.audit_agent import AuditAgent
from app.services.agents.industry_agent import IndustryAgent
from app.services.agents.munger_agent import MungerAgent

__all__ = ["MungerAgent", "IndustryAgent", "AuditAgent"]
