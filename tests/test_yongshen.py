#!/usr/bin/env python3
"""
用神引擎測試

測試 yongshen_engine.py 的用神系統。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from scripts.bazi_engine import BaziEngine
from scripts.geju_engine import GejuEngine
from scripts.yongshen_engine import YongShenEngine, YongShenType, TIAOHUO_TABLE


class TestTiaoHuo:
    """測試調候用神"""

    def test_tiaohuo_table_completeness(self):
        """測試調候表完整性"""
        wuxing = ["木", "火", "土", "金", "水"]
        seasons = ["春", "夏", "秋", "冬"]

        for wx in wuxing:
            assert wx in TIAOHUO_TABLE
            for season in seasons:
                assert season in TIAOHUO_TABLE[wx]

    def test_tiaohuo_case_c0001(self):
        """測試案例 C0001: 甲日主生於夏月（巳）"""
        bazi = BaziEngine.from_ganzhi("己丑", "己巳", "甲子", "辛未")
        yongshen = YongShenEngine(bazi)
        tiaohuo = yongshen.get_tiaohuo_yongshen()

        # 甲木生於夏月（巳），調候用水
        assert tiaohuo.type == YongShenType.TIAOHUO
        assert tiaohuo.wuxing == "水"
        assert tiaohuo.priority == 1

    def test_tiaohuo_winter_wood(self):
        """測試冬木調候"""
        # 甲日主生於冬月（子），調候用火
        bazi = BaziEngine.from_ganzhi("甲子", "丙子", "甲寅", "乙丑")
        yongshen = YongShenEngine(bazi)
        tiaohuo = yongshen.get_tiaohuo_yongshen()

        assert tiaohuo.wuxing == "火"
        assert "冬" in tiaohuo.reason

    def test_tiaohuo_summer_metal(self):
        """測試夏金調候"""
        # 庚日主生於夏月（午），調候用水
        bazi = BaziEngine.from_ganzhi("甲子", "庚午", "庚申", "乙丑")
        yongshen = YongShenEngine(bazi)
        tiaohuo = yongshen.get_tiaohuo_yongshen()

        assert tiaohuo.wuxing == "水"
        assert "夏" in tiaohuo.reason


class TestGejuYongShen:
    """測試格局用神"""

    def test_geju_yongshen_shunong(self):
        """測試順用格用神"""
        # 食神格順用
        bazi = BaziEngine.from_ganzhi("己丑", "己巳", "甲子", "辛未")
        yongshen = YongShenEngine(bazi)
        geju_ys = yongshen.get_geju_yongshen()

        assert geju_ys.type == YongShenType.GEJU
        assert geju_ys.priority == 2
        assert "順用" in geju_ys.reason

    def test_geju_yongshen_niyong(self):
        """測試逆用格用神"""
        # 七殺格逆用
        bazi = BaziEngine.from_ganzhi("甲子", "壬申", "甲寅", "乙丑")
        yongshen = YongShenEngine(bazi)
        geju_ys = yongshen.get_geju_yongshen()

        assert "逆用" in geju_ys.reason or "制化" in geju_ys.reason


class TestTongGuan:
    """測試通關用神"""

    def test_tongguan_no_conflict(self):
        """測試無對峙情況"""
        bazi = BaziEngine.from_ganzhi("己丑", "己巳", "甲子", "辛未")
        yongshen = YongShenEngine(bazi)
        tongguan = yongshen.get_tongguan_yongshen()

        # C0001 無明顯對峙，可能無通關用神
        # 根據實際五行分布判斷
        # 這裡只檢查返回類型
        if tongguan:
            assert tongguan.type == YongShenType.TONGGUAN


class TestXiJi:
    """測試喜忌"""

    def test_xiji_basic(self):
        """測試基本喜忌"""
        bazi = BaziEngine.from_ganzhi("己丑", "己巳", "甲子", "辛未")
        yongshen = YongShenEngine(bazi)
        xiji = yongshen.compute_xiji()

        # 喜用神五行
        assert len(xiji.xi) > 0

        # 忌剋用神五行
        assert len(xiji.ji) > 0

        # 五行分類完整
        total = len(xiji.xi) + len(xiji.ji) + len(xiji.xian)
        # 可能有重複分配，但至少應有分類
        assert total >= 3

    def test_xiji_water_in_xi(self):
        """測試調候用水在喜神中"""
        bazi = BaziEngine.from_ganzhi("己丑", "己巳", "甲子", "辛未")
        yongshen = YongShenEngine(bazi)
        xiji = yongshen.compute_xiji()

        # 調候用水，水應在喜
        assert "水" in xiji.xi


class TestYongShenIntegration:
    """測試用神系統整合"""

    def test_compute_all_yongshen(self):
        """測試計算所有用神"""
        bazi = BaziEngine.from_ganzhi("己丑", "己巳", "甲子", "辛未")
        yongshen = YongShenEngine(bazi)
        all_ys = yongshen.compute_all_yongshen()

        # 至少有調候和格局用神
        assert len(all_ys) >= 2

        # 檢查優先級
        priorities = [ys.priority for ys in all_ys]
        assert 1 in priorities  # 調候
        assert 2 in priorities  # 格局

    def test_to_json(self):
        """測試 JSON 輸出"""
        bazi = BaziEngine.from_ganzhi("己丑", "己巳", "甲子", "辛未")
        yongshen = YongShenEngine(bazi)
        result = yongshen.to_json()

        assert "用神列表" in result
        assert "喜忌" in result
        assert "六標籤制說明" in result

    def test_cache_consistency(self):
        """測試快取一致性"""
        bazi = BaziEngine.from_ganzhi("己丑", "己巳", "甲子", "辛未")
        yongshen = YongShenEngine(bazi)

        all_ys1 = yongshen.compute_all_yongshen()
        all_ys2 = yongshen.compute_all_yongshen()
        assert all_ys1 is all_ys2


class TestRealCases:
    """測試真實案例"""

    def test_case_c0001_full(self):
        """完整測試案例 C0001"""
        bazi = BaziEngine.from_ganzhi("己丑", "己巳", "甲子", "辛未")
        geju = GejuEngine(bazi)
        yongshen = YongShenEngine(bazi, geju)

        # 格局分析
        zhuge = geju.get_yueling_zhuge()
        assert zhuge.main_ge.value == "食神格"

        # 用神分析
        tiaohuo = yongshen.get_tiaohuo_yongshen()
        assert tiaohuo.wuxing == "水"

        # 書中記載：調候用癸水（日支子中藏）
        # 我們的系統正確識別了調候用水

        # 喜忌
        xiji = yongshen.compute_xiji()
        assert "水" in xiji.xi


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
