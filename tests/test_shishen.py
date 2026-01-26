#!/usr/bin/env python3
"""
十神計算測試

測試 bazi_engine.py 的十神計算功能。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from scripts.bazi_engine import BaziEngine, SHISHEN_TABLE


class TestShiShenCalculation:
    """測試十神計算"""

    def test_shishen_table_completeness(self):
        """測試十神表完整性（10日主 x 10天干）"""
        tiangan = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]

        for day_master in tiangan:
            assert day_master in SHISHEN_TABLE
            for gan in tiangan:
                assert gan in SHISHEN_TABLE[day_master]

    def test_shishen_self_is_bijian(self):
        """測試同干為比肩"""
        for gan in ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]:
            assert SHISHEN_TABLE[gan][gan] == "比肩"

    def test_shishen_basic_case(self):
        """測試基本案例（甲日主）"""
        # 甲日主的十神
        assert SHISHEN_TABLE["甲"]["甲"] == "比肩"
        assert SHISHEN_TABLE["甲"]["乙"] == "劫財"
        assert SHISHEN_TABLE["甲"]["丙"] == "食神"
        assert SHISHEN_TABLE["甲"]["丁"] == "傷官"
        assert SHISHEN_TABLE["甲"]["戊"] == "偏財"
        assert SHISHEN_TABLE["甲"]["己"] == "正財"
        assert SHISHEN_TABLE["甲"]["庚"] == "七殺"
        assert SHISHEN_TABLE["甲"]["辛"] == "正官"
        assert SHISHEN_TABLE["甲"]["壬"] == "偏印"
        assert SHISHEN_TABLE["甲"]["癸"] == "正印"

    def test_compute_shishen_case_c0001(self):
        """測試案例 C0001: 己丑/己巳/甲子/辛未"""
        engine = BaziEngine.from_ganzhi("己丑", "己巳", "甲子", "辛未")
        shishen_items = engine.compute_shishen()

        # 應有 14 個項目（4天干 + 10藏干）
        assert len(shishen_items) == 14

        # 檢查天干十神
        gan_items = [s for s in shishen_items if s.layer == "天干"]
        assert len(gan_items) == 4

        # 年干己 = 正財
        year_gan = [s for s in gan_items if s.position == "年"][0]
        assert year_gan.char == "己"
        assert year_gan.shishen == "正財"

        # 月干己 = 正財
        month_gan = [s for s in gan_items if s.position == "月"][0]
        assert month_gan.char == "己"
        assert month_gan.shishen == "正財"

        # 日干甲 = 日主
        day_gan = [s for s in gan_items if s.position == "日"][0]
        assert day_gan.char == "甲"
        assert day_gan.shishen == "日主"

        # 時干辛 = 正官
        hour_gan = [s for s in gan_items if s.position == "時"][0]
        assert hour_gan.char == "辛"
        assert hour_gan.shishen == "正官"

    def test_shishen_summary(self):
        """測試十神統計摘要"""
        engine = BaziEngine.from_ganzhi("己丑", "己巳", "甲子", "辛未")
        summary = engine.get_shishen_summary()

        # 檢查結構
        assert "by_position" in summary
        assert "by_shishen" in summary
        assert "counts" in summary
        assert "weighted_counts" in summary

        # 正財應該很多（己在年月時）
        assert summary["counts"]["正財"] == 4
        assert summary["weighted_counts"]["正財"] == 4.0

    def test_hidden_stem_shishen(self):
        """測試藏干十神"""
        engine = BaziEngine.from_ganzhi("己丑", "己巳", "甲子", "辛未")
        shishen_items = engine.compute_shishen()

        # 藏干項目
        cang_items = [s for s in shishen_items if s.layer == "地支藏干"]
        assert len(cang_items) == 10  # 丑3 + 巳3 + 子1 + 未3 = 10

        # 日支子藏癸 = 正印
        day_cang = [s for s in cang_items if s.position == "日"]
        assert len(day_cang) == 1
        assert day_cang[0].char == "癸"
        assert day_cang[0].shishen == "正印"

    def test_shishen_weight(self):
        """測試十神權重"""
        engine = BaziEngine.from_ganzhi("己丑", "己巳", "甲子", "辛未")
        shishen_items = engine.compute_shishen()

        # 天干權重應為 1.0
        gan_items = [s for s in shishen_items if s.layer == "天干"]
        for item in gan_items:
            assert item.weight == 1.0

        # 藏干權重：本氣1.0, 中氣0.5, 餘氣0.3
        cang_items = [s for s in shishen_items if s.layer == "地支藏干"]
        benqi_items = [s for s in cang_items if s.role == "本氣"]
        for item in benqi_items:
            assert item.weight == 1.0


class TestShiShenEdgeCases:
    """測試十神邊界情況"""

    def test_all_same_gan(self):
        """測試四柱天干相同"""
        engine = BaziEngine.from_ganzhi("甲子", "甲午", "甲申", "甲寅")
        shishen_items = engine.compute_shishen()

        gan_items = [s for s in shishen_items if s.layer == "天干"]
        # 除了日主，其他都是比肩
        bijian_count = sum(1 for s in gan_items if s.shishen == "比肩")
        rizhu_count = sum(1 for s in gan_items if s.shishen == "日主")
        assert bijian_count == 3
        assert rizhu_count == 1

    def test_cache_consistency(self):
        """測試快取一致性"""
        engine = BaziEngine.from_ganzhi("己丑", "己巳", "甲子", "辛未")

        # 多次調用應返回相同結果
        shishen1 = engine.compute_shishen()
        shishen2 = engine.compute_shishen()
        assert shishen1 is shishen2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
