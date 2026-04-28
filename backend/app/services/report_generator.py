"""
报告生成服务模块

负责生成投资分析报告，支持两种格式：
- Markdown 格式：适合文本阅读和编辑
- HTML 格式：包含图表和样式，适合网页展示

报告结构遵循"三维合一投资决策框架"，包含：
1. 公司基本信息和财务数据概览
2. 三维深度分析（芒格视角、产业专家视角、审计专家视角）
3. 综合评级与投资建议
"""

import logging
from datetime import datetime
from html import escape
from typing import Tuple

from app.services.agents.orchestrator import OrchestrationResult
from app.services.agents.schemas import AgentRole

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    报告生成服务类
    
    负责将分析结果转换为格式化的报告文档。
    
    使用示例:
        generator = ReportGenerator()
        content_md, content_html = await generator.generate(
            company_data=company_data,
            financial_ratios=financial_ratios,
            analysis_result=analysis_result,
            include_charts=True
        )
    """
    
    def __init__(self):
        """初始化报告生成器"""
        pass

    async def generate(
        self,
        company_data: dict,
        financial_ratios: dict,
        analysis_result: str | None = None,
        orchestration_result: OrchestrationResult | None = None,
        include_charts: bool = True,
    ) -> Tuple[str, str]:
        """
        生成分析报告
        
        参数:
            company_data: 公司数据字典
            financial_ratios: 财务比率字典
            analysis_result: 兼容旧流程的分析文本
            orchestration_result: 多 Agent 编排结构化结果
            include_charts: 是否包含图表（仅影响 HTML 格式）
        
        返回:
            Tuple[str, str]: (Markdown 内容, HTML 内容)
        """
        markdown_block = analysis_result or "暂无分析结果。"
        html_block = self._legacy_html_block(markdown_block)

        if orchestration_result is not None:
            markdown_block = self._build_orchestration_markdown(orchestration_result)
            html_block = self._build_orchestration_html(orchestration_result)

        content_md = self._generate_markdown(
            company_data,
            financial_ratios,
            markdown_block,
        )

        content_html = self._generate_html(
            company_data,
            financial_ratios,
            html_block,
            include_charts,
        )
        
        return content_md, content_html

    def _generate_markdown(
        self, company_data: dict, financial_ratios: dict, analysis_result: str
    ) -> str:
        """
        生成 Markdown 格式报告
        
        参数:
            company_data: 公司数据字典
            financial_ratios: 财务比率字典
            analysis_result: LLM 分析结果
        
        返回:
            str: Markdown 格式的报告内容
        """
        company_name = company_data.get("company_name", "未知")
        stock_code = company_data.get("stock_code", "未知")
        
        md = f"""# {company_name}（{stock_code}）深度分析报告

**报告日期**：{datetime.now().strftime("%Y年%m月%d日")}
**分析师**：三维合一顶级投资分析师
**数据来源**：{company_data.get("data_source", "网络搜索")}
**数据日期**：{company_data.get("data_date", "未知")}

---

## 核心财务数据概览

| 指标 | 数值 | 数据来源 | 报告日期 |
|------|------|----------|----------|
| 营业收入 | {self._format_number(company_data.get("revenue"))} | {company_data.get("data_source", "网络搜索")} | {company_data.get("data_date", "未知")} |
| 净利润 | {self._format_number(company_data.get("net_profit"))} | {company_data.get("data_source", "网络搜索")} | {company_data.get("data_date", "未知")} |
| 毛利率 | {self._format_percent(company_data.get("gross_margin"))}% | {company_data.get("data_source", "网络搜索")} | {company_data.get("data_date", "未知")} |
| 资产负债率 | {self._format_percent(company_data.get("asset_liability_ratio"))}% | {company_data.get("data_source", "网络搜索")} | {company_data.get("data_date", "未知")} |
| 经营现金流 | {self._format_number(company_data.get("operating_cash_flow"))} | {company_data.get("data_source", "网络搜索")} | {company_data.get("data_date", "未知")} |
| ROE | {self._format_percent(company_data.get("roe"))}% | {company_data.get("data_source", "网络搜索")} | {company_data.get("data_date", "未知")} |
| 市值 | {self._format_number(company_data.get("market_cap"))} | {company_data.get("data_source", "网络搜索")} | {company_data.get("data_date", "未知")} |
| 市盈率(PE) | {self._format_number(company_data.get("pe_ratio"))} | {company_data.get("data_source", "网络搜索")} | {company_data.get("data_date", "未知")} |
| 市净率(PB) | {self._format_number(company_data.get("pb_ratio"))} | {company_data.get("data_source", "网络搜索")} | {company_data.get("data_date", "未知")} |

---

{analysis_result}

---

## 风险提示

本报告仅供参考，不构成投资建议。投资有风险，入市需谨慎。

## 数据来源汇总

- 数据来源：{company_data.get("data_source", "网络搜索")}
- 数据日期：{company_data.get("data_date", "未知")}
- 报告生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

*本报告由公司分析研报助手自动生成*
"""
        return md

    def _generate_html(
        self,
        company_data: dict,
        financial_ratios: dict,
        analysis_block_html: str,
        include_charts: bool,
    ) -> str:
        """
        生成 HTML 格式报告
        
        参数:
            company_data: 公司数据字典
            financial_ratios: 财务比率字典
            analysis_block_html: 已格式化的 HTML 内容块
            include_charts: 是否包含图表
        
        返回:
            str: HTML 格式的报告内容，包含内联样式和图表脚本
        """
        company_name = company_data.get("company_name", "未知")
        stock_code = company_data.get("stock_code", "未知")
        
        chart_section = ""
        if include_charts:
            chart_section = self._generate_chart_section(company_data, financial_ratios)
        
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{company_name}（{stock_code}）深度分析报告</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        /* 基础样式重置 */
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        /* 页面主体样式 */
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.8;
            color: #333;
            background: #f5f5f5;
        }}
        
        /* 容器样式 */
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        /* 报告头部样式 */
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 20px;
            text-align: center;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            font-size: 2em;
            margin-bottom: 10px;
        }}
        .header .meta {{
            font-size: 0.9em;
            opacity: 0.9;
        }}
        
        /* 卡片样式 */
        .card {{
            background: white;
            border-radius: 10px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .card h2 {{
            color: #667eea;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        
        /* 表格样式 */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}
        th {{
            background: #f8f9fa;
            font-weight: 600;
        }}
        tr:hover {{
            background: #f8f9fa;
        }}
        
        /* 内容区域样式 */
        .content {{
            white-space: pre-wrap;
            line-height: 1.8;
        }}
        .content h3 {{
            color: #333;
            margin: 20px 0 10px;
        }}
        
        /* 图表网格布局 */
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        .chart-container {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .chart-container h3 {{
            margin-bottom: 15px;
            color: #333;
        }}
        
        /* 页脚样式 */
        .footer {{
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 0.9em;
        }}
        
        /* 打印样式 */
        @media print {{
            body {{
                background: white;
            }}
            .card {{
                box-shadow: none;
                border: 1px solid #ddd;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{company_name}（{stock_code}）深度分析报告</h1>
            <div class="meta">
                报告日期：{datetime.now().strftime("%Y年%m月%d日")} | 
                分析师：三维合一顶级投资分析师
            </div>
        </div>

        <div class="card">
            <h2>核心财务数据概览</h2>
            <table>
                <thead>
                    <tr>
                        <th>指标</th>
                        <th>数值</th>
                        <th>数据来源</th>
                        <th>报告日期</th>
                    </tr>
                </thead>
                <tbody>
                    <tr><td>营业收入</td><td>{self._format_number(company_data.get("revenue"))}</td><td>{company_data.get("data_source", "网络搜索")}</td><td>{company_data.get("data_date", "未知")}</td></tr>
                    <tr><td>净利润</td><td>{self._format_number(company_data.get("net_profit"))}</td><td>{company_data.get("data_source", "网络搜索")}</td><td>{company_data.get("data_date", "未知")}</td></tr>
                    <tr><td>毛利率</td><td>{self._format_percent(company_data.get("gross_margin"))}%</td><td>{company_data.get("data_source", "网络搜索")}</td><td>{company_data.get("data_date", "未知")}</td></tr>
                    <tr><td>资产负债率</td><td>{self._format_percent(company_data.get("asset_liability_ratio"))}%</td><td>{company_data.get("data_source", "网络搜索")}</td><td>{company_data.get("data_date", "未知")}</td></tr>
                    <tr><td>经营现金流</td><td>{self._format_number(company_data.get("operating_cash_flow"))}</td><td>{company_data.get("data_source", "网络搜索")}</td><td>{company_data.get("data_date", "未知")}</td></tr>
                    <tr><td>ROE</td><td>{self._format_percent(company_data.get("roe"))}%</td><td>{company_data.get("data_source", "网络搜索")}</td><td>{company_data.get("data_date", "未知")}</td></tr>
                    <tr><td>市值</td><td>{self._format_number(company_data.get("market_cap"))}</td><td>{company_data.get("data_source", "网络搜索")}</td><td>{company_data.get("data_date", "未知")}</td></tr>
                    <tr><td>市盈率(PE)</td><td>{self._format_number(company_data.get("pe_ratio"))}</td><td>{company_data.get("data_source", "网络搜索")}</td><td>{company_data.get("data_date", "未知")}</td></tr>
                    <tr><td>市净率(PB)</td><td>{self._format_number(company_data.get("pb_ratio"))}</td><td>{company_data.get("data_source", "网络搜索")}</td><td>{company_data.get("data_date", "未知")}</td></tr>
                </tbody>
            </table>
        </div>

        {chart_section}

        <div class="card">
            <h2>三维合一分析报告</h2>
            {analysis_block_html}
        </div>

        <div class="card">
            <h2>风险提示</h2>
            <p>本报告仅供参考，不构成投资建议。投资有风险，入市需谨慎。</p>
        </div>

        <div class="footer">
            <p>数据来源：{company_data.get("data_source", "网络搜索")} | 数据日期：{company_data.get("data_date", "未知")}</p>
            <p>本报告由公司分析研报助手自动生成 | 生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </div>
    </div>
</body>
</html>"""
        return html

    def _legacy_html_block(self, analysis_text: str) -> str:
        escaped_text = escape(analysis_text).replace("\n", "<br>")
        return f'<div class="content">{escaped_text}</div>'

    def _build_orchestration_markdown(self, orchestration_result: OrchestrationResult) -> str:
        synthesis = orchestration_result.synthesis_result
        failed_roles = [self._role_display_name(run.role) for run in orchestration_result.role_runs if run.status.value == "failed"]

        lines = [
            "## 多 Agent 综合结论",
            "",
            f"- 最终评分：{synthesis.final_score:.2f}/10",
            f"- 投资结论：{synthesis.investment_decision}",
            f"- 数据充分性：{'不足' if synthesis.insufficient_data else '可用'}",
        ]

        if failed_roles:
            lines.append(f"- 角色缺失：{', '.join(failed_roles)}")

        if synthesis.consensus:
            lines.extend(["", "### 共识要点"])
            lines.extend([f"- {item}" for item in synthesis.consensus[:6]])

        if synthesis.major_risks:
            lines.extend(["", "### 主要风险"])
            lines.extend([f"- {item}" for item in synthesis.major_risks[:6]])

        if synthesis.disagreements:
            lines.extend(["", "### 关键分歧"])
            for item in synthesis.disagreements[:6]:
                lines.append(
                    f"- {item.topic}：芒格={item.munger or '未提供'}；产业={item.industry or '未提供'}；审计={item.audit or '未提供'}"
                )

        lines.extend(["", "## 角色观点", ""])
        for role in (AgentRole.MUNGER, AgentRole.INDUSTRY, AgentRole.AUDIT):
            lines.extend(self._build_role_markdown_lines(orchestration_result, role))

        lines.extend(
            [
                "",
                "## 汇总结论",
                synthesis.report_sections.synthesis or "未提供额外汇总说明。",
            ]
        )

        return "\n".join(lines)

    def _build_role_markdown_lines(
        self,
        orchestration_result: OrchestrationResult,
        role: AgentRole,
    ) -> list[str]:
        role_name = self._role_display_name(role)
        role_run = next((run for run in orchestration_result.role_runs if run.role == role), None)

        if role_run is None:
            return [f"### {role_name}", "- 状态：缺失", "- 结论：未返回角色结果", ""]

        if role_run.result is None:
            return [
                f"### {role_name}",
                "- 状态：失败",
                f"- 结论：{role_run.error_message or '角色执行失败，未返回结构化结果'}",
                "",
            ]

        result = role_run.result
        lines = [
            f"### {role_name}",
            "- 状态：完成",
            f"- 评分：{result.score:.2f}/10",
            f"- 摘要：{result.summary}",
        ]

        if result.risks:
            lines.append(f"- 主要风险：{'；'.join(result.risks[:3])}")
        if result.questions:
            lines.append(f"- 待确认问题：{'；'.join(result.questions[:3])}")

        lines.append("")
        return lines

    def _build_orchestration_html(self, orchestration_result: OrchestrationResult) -> str:
        synthesis = orchestration_result.synthesis_result
        failed_roles = [self._role_display_name(run.role) for run in orchestration_result.role_runs if run.status.value == "failed"]

        blocks = [
            '<div class="content">',
            "<h3>多 Agent 综合结论</h3>",
            "<ul>",
            f"<li>最终评分：{synthesis.final_score:.2f}/10</li>",
            f"<li>投资结论：{escape(synthesis.investment_decision)}</li>",
            f"<li>数据充分性：{'不足' if synthesis.insufficient_data else '可用'}</li>",
        ]

        if failed_roles:
            blocks.append(f"<li>角色缺失：{escape(', '.join(failed_roles))}</li>")

        blocks.append("</ul>")

        if synthesis.consensus:
            blocks.append("<h3>共识要点</h3>")
            blocks.append(self._to_html_list(synthesis.consensus[:6]))

        if synthesis.major_risks:
            blocks.append("<h3>主要风险</h3>")
            blocks.append(self._to_html_list(synthesis.major_risks[:6]))

        if synthesis.disagreements:
            blocks.append("<h3>关键分歧</h3>")
            disagreement_items = [
                (
                    f"{item.topic}：芒格={item.munger or '未提供'}；产业={item.industry or '未提供'}；审计={item.audit or '未提供'}"
                )
                for item in synthesis.disagreements[:6]
            ]
            blocks.append(self._to_html_list(disagreement_items))

        blocks.append("<h3>角色观点</h3>")
        for role in (AgentRole.MUNGER, AgentRole.INDUSTRY, AgentRole.AUDIT):
            blocks.append(self._build_role_html(orchestration_result, role))

        blocks.extend(
            [
                "<h3>汇总结论</h3>",
                f"<p>{escape(synthesis.report_sections.synthesis or '未提供额外汇总说明。')}</p>",
                "</div>",
            ]
        )
        return "".join(blocks)

    def _build_role_html(self, orchestration_result: OrchestrationResult, role: AgentRole) -> str:
        role_name = self._role_display_name(role)
        role_run = next((run for run in orchestration_result.role_runs if run.role == role), None)

        if role_run is None:
            return f"<p><strong>{escape(role_name)}</strong>：缺失（未返回角色结果）</p>"

        if role_run.result is None:
            message = role_run.error_message or "角色执行失败，未返回结构化结果"
            return f"<p><strong>{escape(role_name)}</strong>：失败，{escape(message)}</p>"

        result = role_run.result
        details = [
            f"<strong>{escape(role_name)}</strong>",
            f"评分 {result.score:.2f}/10",
            escape(result.summary),
        ]
        if result.risks:
            details.append(f"风险：{escape('；'.join(result.risks[:3]))}")
        if result.questions:
            details.append(f"待确认：{escape('；'.join(result.questions[:3]))}")
        return f"<p>{' | '.join(details)}</p>"

    @staticmethod
    def _to_html_list(items: list[str]) -> str:
        if not items:
            return "<p>暂无。</p>"
        list_items = "".join([f"<li>{escape(item)}</li>" for item in items])
        return f"<ul>{list_items}</ul>"

    @staticmethod
    def _role_display_name(role: AgentRole) -> str:
        display = {
            AgentRole.MUNGER: "芒格视角",
            AgentRole.INDUSTRY: "产业视角",
            AgentRole.AUDIT: "审计视角",
            AgentRole.SYNTHESIS: "汇总视角",
        }
        return display.get(role, role.value)

    def _generate_chart_section(self, company_data: dict, financial_ratios: dict) -> str:
        """
        生成图表部分的 HTML 和 JavaScript
        
        使用 Chart.js 生成数据可视化图表。
        
        参数:
            company_data: 公司数据字典
            financial_ratios: 财务比率字典
        
        返回:
            str: 包含图表容器和脚本的 HTML 字符串
        """
        return """
        <div class="card">
            <h2>数据可视化</h2>
            <div class="charts-grid">
                <div class="chart-container">
                    <h3>核心财务指标</h3>
                    <canvas id="financialChart"></canvas>
                </div>
                <div class="chart-container">
                    <h3>盈利能力指标</h3>
                    <canvas id="profitabilityChart"></canvas>
                </div>
            </div>
        </div>
        <script>
            // 核心财务指标柱状图
            new Chart(document.getElementById('financialChart'), {
                type: 'bar',
                data: {
                    labels: ['毛利率(%)', 'ROE(%)', '资产负债率(%)'],
                    datasets: [{
                        label: '指标值',
                        data: [""" + f"{company_data.get('gross_margin') or 0}, {company_data.get('roe') or 0}, {company_data.get('asset_liability_ratio') or 0}" + """],
                        backgroundColor: ['#667eea', '#764ba2', '#f093fb'],
                        borderRadius: 5
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        y: { beginAtZero: true }
                    }
                }
            });
            
            // 盈利能力环形图
            new Chart(document.getElementById('profitabilityChart'), {
                type: 'doughnut',
                data: {
                    labels: ['毛利率', '净利率', 'ROE'],
                    datasets: [{
                        data: [""" + f"{company_data.get('gross_margin') or 0}, {financial_ratios.get('net_margin') or 0}, {company_data.get('roe') or 0}" + """],
                        backgroundColor: ['#667eea', '#764ba2', '#f093fb']
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { position: 'bottom' }
                    }
                }
            });
        </script>
        """

    def _format_number(self, value) -> str:
        """
        格式化数字显示
        
        将大数字转换为"亿"或"万"单位。
        
        参数:
            value: 数值
        
        返回:
            str: 格式化后的字符串
        """
        if value is None:
            return "未知"
        try:
            num = float(value)
            if num >= 1e8:
                return f"{num/1e8:.2f}亿"
            elif num >= 1e4:
                return f"{num/1e4:.2f}万"
            else:
                return f"{num:.2f}"
        except:
            return str(value)

    def _format_percent(self, value) -> str:
        """
        格式化百分比显示
        
        参数:
            value: 数值
        
        返回:
            str: 格式化后的字符串
        """
        if value is None:
            return "未知"
        try:
            return f"{float(value):.2f}"
        except:
            return str(value)
