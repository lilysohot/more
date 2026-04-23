"""
Skills Package

提供各种数据采集 Skill，包括：
- Tushare: 股票财务数据采集

使用示例：
    from skills import get_tushare_skill
    
    skill = await get_tushare_skill()
    data = await skill.collect_all("600089")
"""

from .tushare_skill import TushareSkill, get_tushare_skill

__all__ = ["TushareSkill", "get_tushare_skill"]
