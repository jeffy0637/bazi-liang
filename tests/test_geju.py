#!/usr/bin/env python3
"""
格局引擎測試

測試 geju_engine.py 的數據輸出功能。
重構後只測試數據完整性，不測試判斷結果。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from scripts.bazi_engine import BaziEngine
from scripts.geju_engine import GejuEngine, GeType


class TestYueLingZhuGe:
    """測試月令主格數據"""

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


class TestYueLingData:
    """測試月令數據完整性"""

    def test_yueling_data_structure(self):
        """測試月令數據結構完整性"""
        bazi = BaziEngine.from_ganzhi("己丑", "己巳", "甲子", "辛未")
        geju = GejuEngine(bazi)
        data = geju.get_yueling_data()

        # 檢查必要字段
        assert "月支" in data
        assert "月支五行" in data
        assert "藏干" in data
        assert "本氣" in data
        assert "本氣十神" in data
        assert "月令主格" in data
        assert "透干" in data
        assert "透干位置" in data

    def test_canggan_detail(self):
        """測試藏干詳細信息"""
        bazi = BaziEngine.from_ganzhi("己丑", "己巳", "甲子", "辛未")
        geju = GejuEngine(bazi)
        data = geju.get_yueling_data()

        # 藏干應該是列表
        assert isinstance(data["藏干"], list)
        assert len(data["藏干"]) > 0

        # 每個藏干應該有完整信息
        for cg in data["藏干"]:
            assert "干" in cg
            assert "角色" in cg
            assert "權重" in cg
            assert "十神" in cg
            assert "五行" in cg


class TestQuGeEvidence:
    """測試取格證據"""

    def test_tian_tou_di_cang(self):
        """測試天透地藏證據"""
        # 月支巳藏丙透於年干
        bazi = BaziEngine.from_ganzhi("丙子", "己巳", "甲寅", "乙丑")
        geju = GejuEngine(bazi)
        evidence = geju.get_quge_evidence()

        ttdz = [e for e in evidence if e["method"] == "天透地藏"]
        assert len(ttdz) == 1
        assert ttdz[0]["confidence"] == "A"

    def test_sanhe_evidence(self):
        """測試三合成局證據"""
        # 寅午戌三合火
        bazi = BaziEngine.from_ganzhi("甲寅", "丙午", "甲戌", "乙丑")
        geju = GejuEngine(bazi)
        evidence = geju.get_quge_evidence()

        sanhe = [e for e in evidence if e["method"] == "三合成局"]
        assert len(sanhe) == 1
        assert sanhe[0]["confidence"] == "S"
        assert "火" in sanhe[0]["evidence"][0]

    def test_sanhui_evidence(self):
        """測試三會成方證據"""
        # 寅卯辰三會木
        bazi = BaziEngine.from_ganzhi("甲寅", "乙卯", "甲辰", "乙丑")
        geju = GejuEngine(bazi)
        evidence = geju.get_quge_evidence()

        sanhui = [e for e in evidence if e["method"] == "三會成方"]
        assert len(sanhui) == 1
        assert sanhui[0]["confidence"] == "S"
        assert "木" in sanhui[0]["evidence"][0]


class TestZhuanwangData:
    """測試專旺格數據"""

    def test_zhuanwang_data_structure(self):
        """測試專旺格數據結構完整性"""
        bazi = BaziEngine.from_ganzhi("甲寅", "丙寅", "甲辰", "乙卯")
        geju = GejuEngine(bazi)
        data = geju.get_zhuanwang_data()

        # 檢查必要字段
        assert "day_wuxing" in data
        assert "zhuanwang_ge_name" in data
        assert "yueling_match" in data
        assert "zhi_same_wuxing_count" in data
        assert "has_sanhe_same_wuxing" in data
        assert "has_sanhui_same_wuxing" in data
        assert "ke_wuxing" in data
        assert "ke_wuxing_in_tiangan" in data
        assert "ke_wuxing_in_dizhi_benqi" in data

    def test_zhuanwang_data_values(self):
        """測試專旺格數據值"""
        # 甲木生於寅月
        bazi = BaziEngine.from_ganzhi("甲寅", "丙寅", "甲辰", "乙卯")
        geju = GejuEngine(bazi)
        data = geju.get_zhuanwang_data()

        assert data["day_wuxing"] == "木"
        assert data["zhuanwang_ge_name"] == "曲直格"
        assert data["yueling_match"] == True
        assert data["ke_wuxing"] == "金"


class TestCongData:
    """測試從格數據"""

    def test_cong_data_structure(self):
        """測試從格數據結構完整性"""
        bazi = BaziEngine.from_ganzhi("己丑", "己巳", "甲子", "辛未")
        geju = GejuEngine(bazi)
        data = geju.get_cong_data()

        # 檢查必要字段
        assert "day_master" in data
        assert "has_benqi_root" in data
        assert "benqi_root_positions" in data
        assert "all_roots" in data
        assert "rizhu_support_weight" in data
        assert "bijie_weight" in data
        assert "yinxing_weight" in data
        assert "caixing_weight" in data
        assert "guansha_weight" in data
        assert "qisha_weight" in data
        assert "shishang_weight" in data
        assert "weighted_counts" in data


class TestPogeData:
    """測試破格數據"""

    def test_poge_data_structure(self):
        """測試破格數據結構完整性"""
        bazi = BaziEngine.from_ganzhi("己丑", "己巳", "甲子", "辛未")
        geju = GejuEngine(bazi)
        data = geju.get_poge_data()

        # 檢查必要字段
        assert "月令主格" in data
        assert "月支" in data
        assert "yuezhi_chong" in data
        assert "yuezhi_he" in data
        assert "guansha_hunza" in data
        assert "caige_bijie_data" in data
        assert "yinge_cai_data" in data
        assert "shishengs_pianyin_data" in data
        assert "shangguange_guan_data" in data
        assert "zhengguange_shangguan_data" in data
        assert "qisha_zhihua_data" in data

    def test_poge_chong_data(self):
        """測試沖破數據"""
        # 月支被沖
        bazi = BaziEngine.from_ganzhi("甲子", "乙巳", "甲亥", "乙丑")
        geju = GejuEngine(bazi)
        data = geju.get_poge_data()

        # 巳亥沖
        assert len(data["yuezhi_chong"]) > 0
        chong = data["yuezhi_chong"][0]
        assert "沖元素" in chong
        assert "沖位置" in chong
        assert "格局柱後破" in chong

    def test_guansha_hunza_data(self):
        """測試官殺混雜數據"""
        bazi = BaziEngine.from_ganzhi("己丑", "己巳", "甲子", "辛未")
        geju = GejuEngine(bazi)
        data = geju.get_poge_data()

        hunza = data["guansha_hunza"]
        assert "guan_weight" in hunza
        assert "sha_weight" in hunza
        assert "both_present" in hunza


class TestShunniData:
    """測試順逆用數據"""

    def test_shunni_data_structure(self):
        """測試順逆用數據結構完整性"""
        bazi = BaziEngine.from_ganzhi("己丑", "己巳", "甲子", "辛未")
        geju = GejuEngine(bazi)
        data = geju.get_shunni_data()

        # 檢查必要字段
        assert "月令主格" in data
        assert "has_sanhe_sanhui_chengjv" in data
        assert "sanhe_sanhui_evidence" in data
        assert "is_shunong_ge_candidate" in data
        assert "is_niyong_ge_candidate" in data
        assert "shunong_ge_list" in data
        assert "niyong_ge_list" in data

    def test_shunni_sanhe_detection(self):
        """測試三合成局檢測"""
        # 寅午戌三合火
        bazi = BaziEngine.from_ganzhi("甲寅", "丙午", "甲戌", "乙丑")
        geju = GejuEngine(bazi)
        data = geju.get_shunni_data()

        assert data["has_sanhe_sanhui_chengjv"] == True
        assert len(data["sanhe_sanhui_evidence"]) > 0


class TestGejuOutput:
    """測試格局輸出"""

    def test_to_json_structure(self):
        """測試 JSON 輸出結構"""
        bazi = BaziEngine.from_ganzhi("己丑", "己巳", "甲子", "辛未")
        geju = GejuEngine(bazi)
        result = geju.to_json()

        # 檢查頂級字段
        assert "主格判定" in result
        assert "月令數據" in result
        assert "取格證據" in result
        assert "專旺格數據" in result
        assert "從格數據" in result
        assert "破格數據" in result
        assert "順逆用數據" in result

        # 檢查主格判定結構
        main_ge = result["主格判定"]
        assert "主格" in main_ge
        assert "取格方法" in main_ge
        assert "推導過程" in main_ge
        assert "置信度" in main_ge

    def test_cache_consistency(self):
        """測試快取一致性"""
        bazi = BaziEngine.from_ganzhi("己丑", "己巳", "甲子", "辛未")
        geju = GejuEngine(bazi)

        zhuge1 = geju.get_yueling_zhuge()
        zhuge2 = geju.get_yueling_zhuge()
        assert zhuge1 is zhuge2


class TestDetermineMainGe:
    """測試梁派取格四步驟"""

    def test_step1_sanhe_tougan(self):
        """測試第一步：三合成局 + 透干"""
        # 寅午戌三合火局，天干丙火透出
        # 丙日主，寅午戌三合火，但丙是比肩不取格
        # 改用甲日主：寅午戌三合火，天干有丙（食神）
        bazi = BaziEngine.from_ganzhi("丙寅", "甲午", "甲戌", "乙丑")
        geju = GejuEngine(bazi)
        result = geju.determine_main_ge()

        assert result.method == "三合三會+透干"
        assert result.main_ge.value == "食神格"
        assert result.confidence == "S"

    def test_step1_sanhui_tougan(self):
        """測試第一步：三會成方 + 透干"""
        # 寅卯辰三會木方，天干甲木透出
        # 丙日主：寅卯辰三會木，甲透出（偏印）
        # 注意：乙也透出了，乙對丙是正印
        bazi = BaziEngine.from_ganzhi("甲寅", "丁卯", "丙辰", "甲申")
        geju = GejuEngine(bazi)
        result = geju.determine_main_ge()

        assert result.method == "三合三會+透干"
        assert result.main_ge.value == "偏印格"
        assert result.confidence == "S"

    def test_step2_yueling_tougan_benqi(self):
        """測試第二步：月令本氣透干"""
        # 甲日生於酉月（酉藏辛金），天干透辛（正官）
        bazi = BaziEngine.from_ganzhi("辛丑", "丁酉", "甲寅", "乙丑")
        geju = GejuEngine(bazi)
        result = geju.determine_main_ge()

        assert result.method == "月令藏干透干"
        assert result.main_ge.value == "正官格"
        assert result.confidence == "A"

    def test_step2_yueling_tougan_zhongqi(self):
        """測試第二步：月令中氣透干"""
        # 甲日生於丑月（丑藏己癸辛），本氣己土不透，中氣癸水透出（正印）
        bazi = BaziEngine.from_ganzhi("癸卯", "乙丑", "甲寅", "乙丑")
        geju = GejuEngine(bazi)
        result = geju.determine_main_ge()

        assert result.method == "月令藏干透干"
        assert result.main_ge.value == "正印格"
        assert result.confidence == "A"

    def test_step2_jian_ge(self):
        """測試兼格：本氣和餘氣都透"""
        # 甲日生於申月（申藏庚壬戊），庚透（七殺）又壬透（偏印）
        bazi = BaziEngine.from_ganzhi("庚子", "壬申", "甲寅", "乙丑")
        geju = GejuEngine(bazi)
        result = geju.determine_main_ge()

        assert result.main_ge.value == "七殺格"
        assert result.jian_ge is not None
        assert result.jian_ge.value == "偏印格"

    def test_step3_yueling_benqi(self):
        """測試第三步：月令本氣取格（無透干）"""
        # 丙日生於酉月，辛金（正財）不透
        bazi = BaziEngine.from_ganzhi("甲子", "丁酉", "丙寅", "戊子")
        geju = GejuEngine(bazi)
        result = geju.determine_main_ge()

        assert result.method == "月令本氣"
        assert result.main_ge.value == "正財格"
        assert result.confidence == "B"

    def test_step4_jianlu(self):
        """測試第四步：建祿格"""
        # 甲日生於寅月，寅藏甲（比肩）→ 建祿格
        # 確保天干沒有透出非比劫的十神
        bazi = BaziEngine.from_ganzhi("甲子", "甲寅", "甲子", "甲子")
        geju = GejuEngine(bazi)
        result = geju.determine_main_ge()

        assert result.main_ge.value == "建祿格"
        # 應有第四步轉換記錄
        step4_exists = any(s.name == "比劫→外格轉換" for s in result.steps)
        assert step4_exists

    def test_step4_yangren(self):
        """測試第四步：羊刃格"""
        # 甲日生於卯月，卯藏乙（劫財）→ 羊刃格
        # 確保天干沒有透出非比劫的十神
        bazi = BaziEngine.from_ganzhi("甲子", "乙卯", "甲子", "甲子")
        geju = GejuEngine(bazi)
        result = geju.determine_main_ge()

        assert result.main_ge.value == "羊刃格"

    def test_推導過程_structure(self):
        """測試推導過程結構完整性"""
        bazi = BaziEngine.from_ganzhi("己丑", "己巳", "甲子", "辛未")
        geju = GejuEngine(bazi)
        result = geju.determine_main_ge()

        assert len(result.steps) >= 1
        for step in result.steps:
            step_dict = step.to_dict()
            assert "步驟" in step_dict
            assert "名稱" in step_dict
            assert "檢測結果" in step_dict
            assert "結論" in step_dict


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
