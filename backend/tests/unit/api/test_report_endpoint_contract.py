from datetime import datetime
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import analyses as analyses_api
from app.models.user import AgentRun, Analysis, Report, User
from app.services.structured_report import FINANCIAL_FIELDS


class _ScalarRows:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class _ExecuteResult:
    def __init__(self, scalar=None, rows=None):
        self._scalar = scalar
        self._rows = rows or []

    def scalar_one_or_none(self):
        return self._scalar

    def scalars(self):
        return _ScalarRows(self._rows)


class _ReportSession:
    def __init__(self, *, analysis, report, agent_runs):
        self._results = [
            _ExecuteResult(scalar=analysis),
            _ExecuteResult(scalar=report),
            _ExecuteResult(rows=agent_runs),
        ]

    async def execute(self, _statement):
        return self._results.pop(0)


def test_report_endpoint_returns_structured_payload_and_legacy_content():
    user_id = uuid4()
    analysis_id = uuid4()
    report_id = uuid4()
    now = datetime.utcnow()
    financials = {field: 1 for field in FINANCIAL_FIELDS}
    financials.update(
        {
            "revenue": 1000000,
            "net_profit": 120000,
            "roe": 12.3,
            "pe_ratio": 8.5,
            "pb_ratio": None,
        }
    )
    user = User(id=user_id, email="analyst@example.com", password_hash="hash")
    analysis = Analysis(
        id=analysis_id,
        user_id=user_id,
        company_name="测试股份",
        stock_code="600000",
        status="completed",
    )
    report = Report(
        id=report_id,
        analysis_id=analysis_id,
        content_md="# 测试报告",
        content_html="<h1>测试报告</h1>",
        created_at=now,
        structured_data_json={
            "company": {
                "company_name": "测试股份",
                "stock_code": "600000",
                "exchange": "SH",
                "industry": "银行",
                "data_source": "unit-test",
                "data_date": "2026-04-27",
            },
            "financials": financials,
            "synthesis": {
                "company_profile": "测试公司画像",
                "consensus": ["现金流稳定"],
                "disagreements": [],
                "final_score": 7.2,
                "investment_decision": "谨慎持有",
                "insufficient_data": False,
                "core_reasons": ["估值合理"],
                "major_risks": ["数据样本有限"],
            },
            "agents": [
                {
                    "name": "munger",
                    "title": "芒格视角",
                    "status": "completed",
                    "score": 7.5,
                    "summary": "商业质量稳定",
                    "thesis": ["护城河可观察"],
                    "positives": ["现金流稳定"],
                    "risks": ["增长放缓"],
                    "red_flags": [],
                    "questions": [],
                    "evidence": [
                        {
                            "item": "年报现金流",
                            "source": "annual report",
                            "confidence": 0.9,
                        }
                    ],
                    "insufficient_data": False,
                }
            ],
            "data_quality": {
                "is_mock": False,
                "quality_note": "unit test payload",
                "missing_fields": [],
                "missing_financial_fields": ["pb_ratio"],
                "completed_agent_count": 1,
                "failed_agent_roles": [],
            },
        },
    )
    fake_session = _ReportSession(analysis=analysis, report=report, agent_runs=[])
    app = FastAPI()
    app.include_router(analyses_api.router, prefix="/api/v1/analyses")

    async def override_get_current_user():
        return user

    async def override_get_db():
        yield fake_session

    app.dependency_overrides[analyses_api.get_current_user] = override_get_current_user
    app.dependency_overrides[analyses_api.get_db] = override_get_db

    response = TestClient(app).get(f"/api/v1/analyses/{analysis_id}/report")

    assert response.status_code == 200
    payload = response.json()
    assert payload["content_md"] == "# 测试报告"
    assert payload["content_html"] == "<h1>测试报告</h1>"
    assert payload["company"]["company_name"] == "测试股份"
    assert payload["financials"]["revenue"] == 1000000
    assert payload["synthesis"]["final_score"] == 7.2
    assert payload["agents"][0]["name"] == "munger"
    assert payload["data_quality"]["missing_financial_fields"] == ["pb_ratio"]
    assert payload["original"]["content_md"] == "# 测试报告"
