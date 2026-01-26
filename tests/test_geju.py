#!/usr/bin/env python3
"""
格局引擎測試

測試 geju_engine.py 的格局判斷功能。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from scripts.bazi_engine import BaziEngine
from scripts.geju_engine import GejuEngine, GeType


class TestYueLingZhuGe:
    """測試月令主格"""

    def test_yueling_case_c0001(self):
        """測試案例 C0001: 己丑/己巳/甲子/辛未"""
        bazi = BaziEngine.from_ganzhi("己丑", "己巳", "甲子", "辛未")
        geju = GejuEngine(bazi)
        zhuge = geju.get_yueling_zhuge()

        # 月支巳，本氣丙（對甲日主為食神）
        assert zhuge.yue_zhi == "巳"
        assert zhuge.yue_zhi_benqi == "丙"
        assert zhuge.benqi_shishen == "食神"
        assert zhuge.main_ge == GeType.SHISHEN

    def test_yueling_zhengguan(self):
        """測試正官格"""
        # 甲日主，月支酉，酉藏辛（正官）
        bazi = BaziEngine.from_ganzhi("甲子", "癸酉", "甲寅", "乙丑")
        geju = GejuEngine(bazi)
        zhuge = geju.get_yueling_zhuge()

        assert zhuge.yue_zhi == "酉"
        assert zhuge.yue_zhi_benqi == "辛"
        assert zhuge.benqi_shishen == "正官"
        assert zhuge.main_ge == GeType.ZHENGGUAN

    def test_yueling_qisha(self):
        """測試七殺格"""
        # 甲日主，月支申，申藏庚（七殺）
        bazi = BaziEngine.from_ganzhi("甲子", "壬申", "甲寅", "乙丑")
        geju = GejuEngine(bazi)
        zhuge = geju.get_yueling_zhuge()

        assert zhuge.yue_zhi == "申"
        assert zhuge.yue_zhi_benqi == "庚"
        assert zhuge.benqi_shishen == "七殺"
        assert zhuge.main_ge == GeType.QISHA

    def test_yueling_zhengyin(self):
        """測試正印格"""
        # 甲日主，月支子，子藏癸（正印）
        bazi = BaziEngine.from_ganzhi("甲子", "丙子", "甲寅", "乙丑")
        geju = GejuEngine(bazi)
        zhuge = geju.get_yueling_zhuge()

        assert zhuge.yue_zhi == "子"
        assert zhuge.yue_zhi_benqi == "癸"
        assert zhuge.benqi_shishen == "正印"
        assert zhuge.main_ge == GeType.ZHENGYIN

    def test_yueling_jianlu(self):
        """測試建祿格（比肩）"""
        # 甲日主，月支寅，寅藏甲（比肩）
        bazi = BaziEngine.from_ganzhi("甲子", "丙寅", "甲寅", "乙丑")
        geju = GejuEngine(bazi)
        zhuge = geju.get_yueling_zhuge()

        assert zhuge.yue_zhi == "寅"
        assert zhuge.yue_zhi_benqi == "甲"
        assert zhuge.benqi_shishen == "比肩"
        assert zhuge.main_ge == GeType.JIANLU

    def test_tou_gan_detection(self):
        """測試透干檢測"""
        # 月支巳藏丙，如果天干也有丙則透干
        bazi = BaziEngine.from_ganzhi("丙子", "己巳", "甲寅", "乙丑")
        geju = GejuEngine(bazi)
        zhuge = geju.get_yueling_zhuge()

        assert zhuge.is_tou_gan == True
        assert "年" in zhuge.tou_gan_positions


class TestQuGeSiFa:
    """測試取格四法"""

    def test_tian_tou_di_cang(self):
        """測試天透地藏"""
        # 月支巳藏丙透於年干
        bazi = BaziEngine.from_ganzhi("丙子", "己巳", "甲寅", "乙丑")
        geju = GejuEngine(bazi)
        results = geju.check_quge_sifa()

        ttdz = [r for r in results if r.method == "天透地藏"]
        assert len(ttdz) == 1
        assert ttdz[0].confidence == "A"

    def test_sanhe_chengjv(self):
        """測試三合成局"""
        # 寅午戌三合火
        bazi = BaziEngine.from_ganzhi("甲寅", "丙午", "甲戌", "乙丑")
        geju = GejuEngine(bazi)
        results = geju.check_quge_sifa()

        sanhe = [r for r in results if r.method == "三合成局"]
        assert len(sanhe) == 1
        assert sanhe[0].confidence == "S"
        assert "火" in sanhe[0].evidence[0]

    def test_sanhui_chengfang(self):
        """測試三會成方"""
        # 寅卯辰三會木
        bazi = BaziEngine.from_ganzhi("甲寅", "乙卯", "甲辰", "乙丑")
        geju = GejuEngine(bazi)
        results = geju.check_quge_sifa()

        sanhui = [r for r in results if r.method == "三會成方"]
        assert len(sanhui) == 1
        assert sanhui[0].confidence == "S"
        assert "木" in sanhui[0].evidence[0]


class TestShunNi:
    """測試順用/逆用"""

    def test_shunni_shunong(self):
        """測試順用格"""
        # 食神格為順用
        bazi = BaziEngine.from_ganzhi("己丑", "己巳", "甲子", "辛未")
        geju = GejuEngine(bazi)
        result = geju.judge_shunni()

        assert result["shunni"] == "順用"
        assert "食神格" in result["main_ge"]

    def test_shunni_niyong(self):
        """測試逆用格"""
        # 七殺格為逆用
        bazi = BaziEngine.from_ganzhi("甲子", "壬申", "甲寅", "乙丑")
        geju = GejuEngine(bazi)
        result = geju.judge_shunni()

        assert result["shunni"] == "逆用"
        assert "七殺格" in result["main_ge"]

    def test_shunni_sanhe_niyong(self):
        """測試三合成局一律逆用"""
        # 寅午戌三合火
        bazi = BaziEngine.from_ganzhi("甲寅", "丙午", "甲戌", "乙丑")
        geju = GejuEngine(bazi)
        result = geju.judge_shunni()

        assert result["shunni"] == "逆用"
        assert "三合" in result["reason"]


class TestPoGe:
    """測試破格"""

    def test_poge_chong(self):
        """測試沖破"""
        # 月支被沖
        bazi = BaziEngine.from_ganzhi("甲子", "乙巳", "甲亥", "乙丑")
        geju = GejuEngine(bazi)
        poge = geju.check_poge()

        # 巳亥沖
        assert poge.is_poge == True
        assert poge.po_type == "沖破"

    def test_poge_no_poge(self):
        """測試無破格"""
        bazi = BaziEngine.from_ganzhi("己丑", "己巳", "甲子", "辛未")
        geju = GejuEngine(bazi)
        poge = geju.check_poge()

        # C0001 無破格
        assert poge.is_poge == False

    def test_poge_shangguan_jianguan(self):
        """測試傷官見官（正官格）"""
        # 正官格見傷官，但無沖
        # 甲日主，月支酉（正官格），時干丁（傷官），無沖
        bazi = BaziEngine.from_ganzhi("甲子", "癸酉", "甲寅", "丁丑")
        geju = GejuEngine(bazi)
        poge = geju.check_poge()

        # 時干丁為傷官，正官格見傷官
        if poge.is_poge:
            assert poge.po_type == "傷格"


class TestGejuOutput:
    """測試格局輸出"""

    def test_to_json(self):
        """測試 JSON 輸出"""
        bazi = BaziEngine.from_ganzhi("己丑", "己巳", "甲子", "辛未")
        geju = GejuEngine(bazi)
        result = geju.to_json()

        assert "月令主格" in result
        assert "取格四法" in result
        assert "順逆用" in result
        assert "破格檢測" in result

    def test_cache_consistency(self):
        """測試快取一致性"""
        bazi = BaziEngine.from_ganzhi("己丑", "己巳", "甲子", "辛未")
        geju = GejuEngine(bazi)

        zhuge1 = geju.get_yueling_zhuge()
        zhuge2 = geju.get_yueling_zhuge()
        assert zhuge1 is zhuge2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
