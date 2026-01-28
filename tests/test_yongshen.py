#!/usr/bin/env python3
"""
用神引擎測試

測試 yongshen_engine.py 的數據輸出功能。
重構後只測試數據完整性，不測試判斷結果。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from scripts.bazi_engine import BaziEngine
from scripts.geju_engine import GejuEngine
from scripts.yongshen_engine import YongShenEngine, YongShenType, TIAOHUO_REFERENCE


class TestTiaoHuoData:
    """測試調候數據"""

    def test_tiaohuo_reference_completeness(self):
        """測試調候參考表完整性"""
        wuxing = ["木", "火", "土", "金", "水"]
        seasons = ["春", "夏", "秋", "冬"]

        for wx in wuxing:
            assert wx in TIAOHUO_REFERENCE
            for season in seasons:
                assert season in TIAOHUO_REFERENCE[wx]

    def test_tiaohuo_data_structure(self):
        """測試調候數據結構完整性"""
        bazi = BaziEngine.from_ganzhi("己丑", "己巳", "甲子", "辛未")
        yongshen = YongShenEngine(bazi)
        data = yongshen.get_tiaohuo_data()

        # 檢查必要字段
        assert "day_master" in data
        assert "day_wuxing" in data
        assert "yue_zhi" in data
        assert "season" in data
        assert "season_temp" in data
        assert "tiaohuo_reference" in data
        assert "existing_tiaohuo" in data
        assert "tiaohuo_positions" in data
        assert "wuxing_counts" in data

    def test_tiaohuo_reference_content(self):
        """測試調候參考表內容"""
        bazi = BaziEngine.from_ganzhi("己丑", "己巳", "甲子", "辛未")
        yongshen = YongShenEngine(bazi)
        data = yongshen.get_tiaohuo_data()

        ref = data["tiaohuo_reference"]
        assert "primary" in ref
        assert "auxiliary" in ref
        assert "reason" in ref

        # 甲木生於夏月（巳），調候用水
        assert ref["primary"] == "水"

    def test_tiaohuo_data_winter_wood(self):
        """測試冬木調候數據"""
        bazi = BaziEngine.from_ganzhi("甲子", "丙子", "甲寅", "乙丑")
        yongshen = YongShenEngine(bazi)
        data = yongshen.get_tiaohuo_data()

        assert data["season"] == "冬"
        assert data["season_temp"] == "寒"
        assert data["tiaohuo_reference"]["primary"] == "火"

    def test_existing_tiaohuo_detection(self):
        """測試命局中調候五行檢測"""
        bazi = BaziEngine.from_ganzhi("己丑", "己巳", "甲子", "辛未")
        yongshen = YongShenEngine(bazi)
        data = yongshen.get_tiaohuo_data()

        # 檢查 existing_tiaohuo 結構
        existing = data["existing_tiaohuo"]
        for wx, info in existing.items():
            assert "存在" in info
            assert "權重" in info


class TestGejuYongshenData:
    """測試格局用神數據"""

    def test_geju_yongshen_data_structure(self):
        """測試格局用神數據結構完整性"""
        bazi = BaziEngine.from_ganzhi("己丑", "己巳", "甲子", "辛未")
        yongshen = YongShenEngine(bazi)
        data = yongshen.get_geju_yongshen_data()

        # 檢查必要字段
        assert "day_wuxing" in data
        assert "月令主格" in data
        assert "shunni_data" in data
        assert "shishen_wuxing_map" in data
        assert "xiangshen_reference" in data
        assert "zhihua_reference" in data

    def test_shishen_wuxing_map(self):
        """測試十神五行對照表"""
        bazi = BaziEngine.from_ganzhi("己丑", "己巳", "甲子", "辛未")
        yongshen = YongShenEngine(bazi)
        data = yongshen.get_geju_yongshen_data()

        shishen_map = data["shishen_wuxing_map"]
        # 甲日主
        assert shishen_map["比肩"] == "木"
        assert shishen_map["劫財"] == "木"
        assert shishen_map["食神"] == "火"
        assert shishen_map["傷官"] == "火"
        assert shishen_map["偏財"] == "土"
        assert shishen_map["正財"] == "土"

    def test_xiangshen_reference(self):
        """測試順用格相神參考"""
        bazi = BaziEngine.from_ganzhi("己丑", "己巳", "甲子", "辛未")
        yongshen = YongShenEngine(bazi)
        data = yongshen.get_geju_yongshen_data()

        ref = data["xiangshen_reference"]
        assert "正財格" in ref
        assert "正官格" in ref
        assert "食神格" in ref

        # 食神格的相神
        ss_ref = ref["食神格"]
        assert "相神" in ss_ref
        assert "五行" in ss_ref
        assert "作用" in ss_ref

    def test_zhihua_reference(self):
        """測試逆用格制化參考"""
        bazi = BaziEngine.from_ganzhi("己丑", "己巳", "甲子", "辛未")
        yongshen = YongShenEngine(bazi)
        data = yongshen.get_geju_yongshen_data()

        ref = data["zhihua_reference"]
        assert "七殺格" in ref
        assert "傷官格" in ref

        # 七殺格的制化
        qs_ref = ref["七殺格"]
        assert "制化" in qs_ref
        assert "五行" in qs_ref
        assert "作用" in qs_ref


class TestTongguanData:
    """測試通關數據"""

    def test_tongguan_data_structure(self):
        """測試通關數據結構完整性"""
        bazi = BaziEngine.from_ganzhi("己丑", "己巳", "甲子", "辛未")
        yongshen = YongShenEngine(bazi)
        data = yongshen.get_tongguan_data()

        # 檢查必要字段
        assert "wuxing_counts" in data
        assert "duizhi_data" in data
        assert "wuxing_sheng_map" in data
        assert "wuxing_ke_map" in data

    def test_duizhi_data_structure(self):
        """測試對峙數據結構"""
        bazi = BaziEngine.from_ganzhi("己丑", "己巳", "甲子", "辛未")
        yongshen = YongShenEngine(bazi)
        data = yongshen.get_tongguan_data()

        assert len(data["duizhi_data"]) == 5  # 五對剋制關係

        for item in data["duizhi_data"]:
            assert "剋方" in item
            assert "剋方權重" in item
            assert "被剋方" in item
            assert "被剋方權重" in item
            assert "通關五行" in item
            assert "通關五行權重" in item


class TestRizhuStrengthData:
    """測試日主強弱數據"""

    def test_rizhu_strength_data_structure(self):
        """測試日主強弱數據結構完整性"""
        bazi = BaziEngine.from_ganzhi("己丑", "己巳", "甲子", "辛未")
        yongshen = YongShenEngine(bazi)
        data = yongshen.get_rizhu_strength_data()

        # 檢查必要字段
        assert "day_master" in data
        assert "day_wuxing" in data
        assert "de_ling_data" in data
        assert "de_di_list" in data
        assert "de_di_count" in data
        assert "de_shi_list" in data
        assert "de_shi_count" in data
        assert "de_qi_data" in data
        assert "weighted_counts" in data

    def test_de_ling_data(self):
        """測試得令數據"""
        bazi = BaziEngine.from_ganzhi("己丑", "己巳", "甲子", "辛未")
        yongshen = YongShenEngine(bazi)
        data = yongshen.get_rizhu_strength_data()

        de_ling = data["de_ling_data"]
        assert "yue_wuxing" in de_ling
        assert "day_wuxing" in de_ling
        assert "same_wuxing" in de_ling
        assert "sheng_wo_wuxing" in de_ling
        assert "is_sheng" in de_ling

    def test_de_qi_data(self):
        """測試得氣數據"""
        bazi = BaziEngine.from_ganzhi("己丑", "己巳", "甲子", "辛未")
        yongshen = YongShenEngine(bazi)
        data = yongshen.get_rizhu_strength_data()

        de_qi = data["de_qi_data"]
        assert "bijie_weight" in de_qi
        assert "yinxing_weight" in de_qi
        assert "total_support" in de_qi
        assert "guansha_weight" in de_qi
        assert "caixing_weight" in de_qi
        assert "shishang_weight" in de_qi
        assert "total_drain" in de_qi


class TestWuxingRelations:
    """測試五行生剋參考"""

    def test_wuxing_relations_structure(self):
        """測試五行生剋關係結構"""
        bazi = BaziEngine.from_ganzhi("己丑", "己巳", "甲子", "辛未")
        yongshen = YongShenEngine(bazi)
        data = yongshen.get_wuxing_relations()

        # 檢查必要字段
        assert "day_wuxing" in data
        assert "sheng" in data
        assert "ke" in data
        assert "sheng_wo" in data
        assert "ke_wo" in data
        assert "full_sheng_map" in data
        assert "full_ke_map" in data

    def test_wuxing_relations_values(self):
        """測試五行生剋關係值"""
        bazi = BaziEngine.from_ganzhi("己丑", "己巳", "甲子", "辛未")
        yongshen = YongShenEngine(bazi)
        data = yongshen.get_wuxing_relations()

        # 甲日主，木
        assert data["day_wuxing"] == "木"
        assert data["sheng"] == "火"     # 木生火
        assert data["ke"] == "土"        # 木剋土
        assert data["sheng_wo"] == "水"  # 水生木
        assert data["ke_wo"] == "金"     # 金剋木


class TestYongShenOutput:
    """測試用神輸出"""

    def test_to_json_structure(self):
        """測試 JSON 輸出結構"""
        bazi = BaziEngine.from_ganzhi("己丑", "己巳", "甲子", "辛未")
        yongshen = YongShenEngine(bazi)
        result = yongshen.to_json()

        # 檢查頂級字段
        assert "調候數據" in result
        assert "格局用神數據" in result
        assert "通關數據" in result
        assert "日主強弱數據" in result
        assert "五行生剋參考" in result
        assert "六標籤制說明" in result

        # 確認沒有判斷結果
        assert "用神列表" not in result
        assert "喜忌" not in result

    def test_labels_description(self):
        """測試六標籤制說明"""
        bazi = BaziEngine.from_ganzhi("己丑", "己巳", "甲子", "辛未")
        yongshen = YongShenEngine(bazi)
        labels = yongshen.get_labels_description()

        assert "調候" in labels
        assert "格局" in labels
        assert "通關" in labels
        assert "病藥" in labels
        assert "專旺" in labels
        assert "扶抑" in labels


class TestRealCases:
    """測試真實案例"""

    def test_case_c0001_data(self):
        """測試案例 C0001 數據完整性"""
        bazi = BaziEngine.from_ganzhi("己丑", "己巳", "甲子", "辛未")
        geju = GejuEngine(bazi)
        yongshen = YongShenEngine(bazi, geju)

        # 格局數據
        geju_data = geju.to_json()
        assert geju_data["月令數據"]["月令主格"] == "食神格"

        # 調候數據
        tiaohuo = yongshen.get_tiaohuo_data()
        assert tiaohuo["day_wuxing"] == "木"
        assert tiaohuo["season"] == "夏"
        assert tiaohuo["tiaohuo_reference"]["primary"] == "水"

        # 日主強弱數據
        strength = yongshen.get_rizhu_strength_data()
        assert strength["day_master"] == "甲"
        assert len(strength["de_di_list"]) >= 0  # 數據完整性
        assert len(strength["de_shi_list"]) >= 0

    def test_case_qisha_data(self):
        """測試七殺格數據"""
        bazi = BaziEngine.from_ganzhi("甲子", "壬申", "甲寅", "乙丑")
        geju = GejuEngine(bazi)
        yongshen = YongShenEngine(bazi, geju)

        # 格局數據
        geju_data = geju.to_json()
        assert geju_data["月令數據"]["月令主格"] == "七殺格"

        # 格局用神數據應該有七殺格制化參考
        ys_data = yongshen.get_geju_yongshen_data()
        assert "七殺格" in ys_data["zhihua_reference"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
