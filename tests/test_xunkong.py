#!/usr/bin/env python3
"""
旬空計算測試

測試 bazi_engine.py 的旬空（空亡）計算功能。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from scripts.bazi_engine import (
    BaziEngine, XUNKONG_TABLE, JIAZI_60, get_xun_shou
)


class TestXunKongBasics:
    """測試旬空基礎功能"""

    def test_xunkong_table_completeness(self):
        """測試旬空表完整性（6旬）"""
        assert len(XUNKONG_TABLE) == 6
        expected_xun = ["甲子", "甲戌", "甲申", "甲午", "甲辰", "甲寅"]
        for xun in expected_xun:
            assert xun in XUNKONG_TABLE

    def test_xunkong_values(self):
        """測試旬空值"""
        assert XUNKONG_TABLE["甲子"] == ("戌", "亥")
        assert XUNKONG_TABLE["甲戌"] == ("申", "酉")
        assert XUNKONG_TABLE["甲申"] == ("午", "未")
        assert XUNKONG_TABLE["甲午"] == ("辰", "巳")
        assert XUNKONG_TABLE["甲辰"] == ("寅", "卯")
        assert XUNKONG_TABLE["甲寅"] == ("子", "丑")

    def test_jiazi_60_completeness(self):
        """測試六十甲子表完整性"""
        assert len(JIAZI_60) == 60
        assert JIAZI_60[0] == "甲子"
        assert JIAZI_60[59] == "癸亥"

    def test_get_xun_shou(self):
        """測試旬首查找"""
        # 甲子旬
        assert get_xun_shou("甲子") == "甲子"
        assert get_xun_shou("乙丑") == "甲子"
        assert get_xun_shou("癸酉") == "甲子"

        # 甲戌旬
        assert get_xun_shou("甲戌") == "甲戌"
        assert get_xun_shou("癸未") == "甲戌"

        # 甲寅旬
        assert get_xun_shou("甲寅") == "甲寅"
        assert get_xun_shou("癸亥") == "甲寅"

    def test_get_xun_shou_invalid(self):
        """測試無效干支"""
        with pytest.raises(ValueError):
            get_xun_shou("甲丑")  # 無效組合


class TestXunKongCalculation:
    """測試旬空計算"""

    def test_xunkong_case_c0001(self):
        """測試案例 C0001: 己丑/己巳/甲子/辛未，日柱甲子"""
        engine = BaziEngine.from_ganzhi("己丑", "己巳", "甲子", "辛未")
        xunkong = engine.compute_xunkong()

        # 甲子旬空戌亥
        assert xunkong.day_pillar == "甲子"
        assert xunkong.xun_shou == "甲子"
        assert xunkong.kong_zhi == ("戌", "亥")

        # 四柱地支：丑巳子未，無戌亥
        assert xunkong.kong_positions == []
        assert xunkong.kong_shishen == []

    def test_xunkong_with_kong_position(self):
        """測試有落空柱位的情況"""
        # 甲午旬空辰巳，如果有辰或巳支則落空
        engine = BaziEngine.from_ganzhi("甲辰", "乙巳", "甲午", "丙寅")
        xunkong = engine.compute_xunkong()

        # 甲午旬空辰巳
        assert xunkong.xun_shou == "甲午"
        assert xunkong.kong_zhi == ("辰", "巳")

        # 年支辰、月支巳都落空
        assert "年" in xunkong.kong_positions
        assert "月" in xunkong.kong_positions
        assert len(xunkong.kong_positions) == 2

    def test_xunkong_jiayin_xun(self):
        """測試甲寅旬"""
        # 甲寅旬空子丑
        engine = BaziEngine.from_ganzhi("己丑", "癸酉", "甲寅", "辛未")
        xunkong = engine.compute_xunkong()

        assert xunkong.xun_shou == "甲寅"
        assert xunkong.kong_zhi == ("子", "丑")

        # 年支丑落空
        assert "年" in xunkong.kong_positions

    def test_xunkong_cache(self):
        """測試旬空快取"""
        engine = BaziEngine.from_ganzhi("己丑", "己巳", "甲子", "辛未")

        xunkong1 = engine.compute_xunkong()
        xunkong2 = engine.compute_xunkong()
        assert xunkong1 is xunkong2


class TestXunKongAllXun:
    """測試所有六旬"""

    @pytest.mark.parametrize("day_pillar,expected_xun,expected_kong", [
        ("甲子", "甲子", ("戌", "亥")),
        ("乙丑", "甲子", ("戌", "亥")),
        ("甲戌", "甲戌", ("申", "酉")),
        ("甲申", "甲申", ("午", "未")),
        ("甲午", "甲午", ("辰", "巳")),
        ("甲辰", "甲辰", ("寅", "卯")),
        ("甲寅", "甲寅", ("子", "丑")),
    ])
    def test_all_xun(self, day_pillar, expected_xun, expected_kong):
        """測試所有旬首"""
        # 構造有效四柱（年月時隨意，日柱指定）
        engine = BaziEngine.from_ganzhi("甲子", "乙丑", day_pillar, "丁卯")
        xunkong = engine.compute_xunkong()

        assert xunkong.xun_shou == expected_xun
        assert xunkong.kong_zhi == expected_kong


class TestXunKongShiShen:
    """測試旬空對十神的影響"""

    def test_kong_shishen_detection(self):
        """測試落空十神檢測"""
        # 甲辰旬空寅卯，假設有寅或卯支
        engine = BaziEngine.from_ganzhi("甲寅", "乙卯", "甲辰", "丁卯")
        xunkong = engine.compute_xunkong()

        # 空亡寅卯
        assert xunkong.kong_zhi == ("寅", "卯")

        # 年支寅、月支卯、時支卯落空
        assert "年" in xunkong.kong_positions
        assert "月" in xunkong.kong_positions
        assert "時" in xunkong.kong_positions

        # 落空的十神
        # 寅藏甲丙戊，卯藏乙
        # 甲日主：甲=比肩，丙=食神，戊=偏財，乙=劫財
        assert "比肩" in xunkong.kong_shishen or "劫財" in xunkong.kong_shishen


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
