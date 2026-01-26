#!/usr/bin/env python3
"""
八字引擎測試

測試 bazi_engine.py 的核心功能:
- 四柱解析
- 藏干計算
- 五行統計
- 刑沖合會
- 拱夾暗拱
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from scripts.bazi_engine import (
    BaziEngine, Pillar, HiddenStem, Relation,
    TIANGAN, DIZHI, TIANGAN_WUXING, DIZHI_WUXING, DIZHI_CANGGAN
)


# ============================================================
# Test Case 1: 基本四柱解析
# ============================================================

class TestPillarParsing:
    """測試四柱解析"""

    def test_from_ganzhi_valid(self):
        """測試有效干支輸入"""
        engine = BaziEngine.from_ganzhi("甲子", "乙丑", "丙寅", "丁卯")

        assert engine.year.ganzhi == "甲子"
        assert engine.month.ganzhi == "乙丑"
        assert engine.day.ganzhi == "丙寅"
        assert engine.hour.ganzhi == "丁卯"

    def test_from_ganzhi_invalid_gan(self):
        """測試無效天干"""
        with pytest.raises(ValueError, match="無效天干"):
            BaziEngine.from_ganzhi("X子", "乙丑", "丙寅", "丁卯")

    def test_from_ganzhi_invalid_zhi(self):
        """測試無效地支"""
        with pytest.raises(ValueError, match="無效地支"):
            BaziEngine.from_ganzhi("甲X", "乙丑", "丙寅", "丁卯")

    def test_day_master(self):
        """測試日主提取"""
        engine = BaziEngine.from_ganzhi("甲子", "乙丑", "丙寅", "丁卯")
        assert engine.day_master == "丙"

    def test_all_gan_zhi(self):
        """測試所有天干地支列表"""
        engine = BaziEngine.from_ganzhi("甲子", "乙丑", "丙寅", "丁卯")
        assert engine.all_gan == ["甲", "乙", "丙", "丁"]
        assert engine.all_zhi == ["子", "丑", "寅", "卯"]


# ============================================================
# Test Case 2: 藏干計算
# ============================================================

class TestHiddenStems:
    """測試藏干計算"""

    def test_hidden_stems_count(self):
        """測試藏干數量"""
        engine = BaziEngine.from_ganzhi("甲子", "乙丑", "丙寅", "丁卯")
        hidden = engine.compute_hidden_stems()

        # 子: 癸(1), 丑: 己癸辛(3), 寅: 甲丙戊(3), 卯: 乙(1) = 8
        assert len(hidden) == 8

    def test_hidden_stems_zi(self):
        """測試子支藏干 (只有癸)"""
        engine = BaziEngine.from_ganzhi("甲子", "乙丑", "丙寅", "丁卯")
        hidden = engine.compute_hidden_stems()

        zi_hidden = [h for h in hidden if h.zhi == "子"]
        assert len(zi_hidden) == 1
        assert zi_hidden[0].stem == "癸"
        assert zi_hidden[0].role == "本氣"
        assert zi_hidden[0].weight == 1.0

    def test_hidden_stems_chou(self):
        """測試丑支藏干 (己癸辛)"""
        engine = BaziEngine.from_ganzhi("甲子", "乙丑", "丙寅", "丁卯")
        hidden = engine.compute_hidden_stems()

        chou_hidden = [h for h in hidden if h.zhi == "丑"]
        assert len(chou_hidden) == 3
        stems = [h.stem for h in chou_hidden]
        assert stems == ["己", "癸", "辛"]

    def test_hidden_stems_weight(self):
        """測試藏干權重"""
        engine = BaziEngine.from_ganzhi("甲子", "乙丑", "丙寅", "丁卯")
        hidden = engine.compute_hidden_stems()

        chou_hidden = [h for h in hidden if h.zhi == "丑"]
        weights = [h.weight for h in chou_hidden]
        assert weights == [1.0, 0.5, 0.3]  # 本氣、中氣、餘氣


# ============================================================
# Test Case 3: 五行統計
# ============================================================

class TestFiveElements:
    """測試五行統計"""

    def test_five_elements_basic(self):
        """測試基本五行統計 (不含藏干)"""
        # 甲子(木水), 乙丑(木土), 丙寅(火木), 丁卯(火木)
        engine = BaziEngine.from_ganzhi("甲子", "乙丑", "丙寅", "丁卯")
        result = engine.compute_five_elements(include_hidden=False)

        # 天干: 甲(木) 乙(木) 丙(火) 丁(火) = 木2 火2
        # 地支: 子(水) 丑(土) 寅(木) 卯(木) = 水1 土1 木2
        assert result["detail"]["天干"]["木"] == 2
        assert result["detail"]["天干"]["火"] == 2
        assert result["detail"]["地支"]["水"] == 1
        assert result["detail"]["地支"]["土"] == 1
        assert result["detail"]["地支"]["木"] == 2

    def test_five_elements_with_hidden(self):
        """測試含藏干的五行統計"""
        engine = BaziEngine.from_ganzhi("甲子", "乙丑", "丙寅", "丁卯")
        result = engine.compute_five_elements(include_hidden=True)

        # 藏干也應計入
        assert "藏干" in result["detail"]
        assert result["counts"]["金"] > 0  # 丑藏辛金

    def test_missing_element(self):
        """測試缺失五行"""
        # 這組八字缺金: 甲寅 乙卯 丙午 丁巳
        engine = BaziEngine.from_ganzhi("甲寅", "乙卯", "丙午", "丁巳")
        result = engine.compute_five_elements(include_hidden=False)

        # 不含藏干時缺金和水
        # 甲寅(木木), 乙卯(木木), 丙午(火火), 丁巳(火火)
        # 天干: 木木火火, 地支: 木木火火 → 缺金水土
        assert "金" in result["missing"]
        assert "水" in result["missing"]

    def test_dominant_element(self):
        """測試最旺五行"""
        # 木很旺的八字
        engine = BaziEngine.from_ganzhi("甲寅", "乙卯", "甲寅", "乙卯")
        result = engine.compute_five_elements(include_hidden=False)

        assert result["dominant"] == "木"


# ============================================================
# Test Case 4: 刑沖合會關係
# ============================================================

class TestRelations:
    """測試刑沖合會"""

    def test_liuhe(self):
        """測試六合"""
        # 子丑合土
        engine = BaziEngine.from_ganzhi("甲子", "乙丑", "丙寅", "丁卯")
        relations = engine.compute_relations()

        liuhe = [r for r in relations if r.type == "六合"]
        assert len(liuhe) >= 1
        assert any(set(r.elements) == {"子", "丑"} for r in liuhe)

    def test_liuchong(self):
        """測試六沖"""
        # 子午沖
        engine = BaziEngine.from_ganzhi("甲子", "乙丑", "丙午", "丁卯")
        relations = engine.compute_relations()

        liuchong = [r for r in relations if r.type == "六沖"]
        assert len(liuchong) >= 1
        assert any(set(r.elements) == {"子", "午"} for r in liuchong)

    def test_sanhe(self):
        """測試三合局"""
        # 寅午戌三合火
        engine = BaziEngine.from_ganzhi("甲寅", "乙午", "丙戌", "丁卯")
        relations = engine.compute_relations()

        sanhe = [r for r in relations if r.type == "三合"]
        assert len(sanhe) >= 1
        assert sanhe[0].result == "火"

    def test_xing(self):
        """測試刑"""
        # 寅巳刑 (無恩之刑)
        engine = BaziEngine.from_ganzhi("甲寅", "乙巳", "丙申", "丁卯")
        relations = engine.compute_relations()

        xing = [r for r in relations if r.type == "刑"]
        assert len(xing) >= 1

    def test_tiangan_he(self):
        """測試天干合"""
        # 甲己合土
        engine = BaziEngine.from_ganzhi("甲子", "己丑", "丙寅", "丁卯")
        relations = engine.compute_relations()

        tiangan_he = [r for r in relations if r.type == "天干合"]
        assert len(tiangan_he) >= 1
        assert any(set(r.elements) == {"甲", "己"} for r in tiangan_he)

    def test_bansanhe(self):
        """測試半三合"""
        # 寅戌半三合火 (缺午)
        engine = BaziEngine.from_ganzhi("甲寅", "乙丑", "丙戌", "丁卯")
        relations = engine.compute_relations()

        bansanhe = [r for r in relations if r.type == "半三合"]
        assert len(bansanhe) >= 1
        assert bansanhe[0].result == "火"
        assert bansanhe[0].note == "缺午"


# ============================================================
# Test Case 5: 拱夾暗拱
# ============================================================

class TestGongJia:
    """測試拱夾暗拱"""

    def test_angong(self):
        """測試暗拱"""
        # 寅戌暗拱午 (火局)
        engine = BaziEngine.from_ganzhi("甲寅", "乙丑", "丙戌", "丁卯")
        gong_jia = engine.compute_gong_jia_an_gong()

        angong = [g for g in gong_jia if g.type == "暗拱"]
        assert len(angong) >= 1
        assert angong[0].target == "午"
        assert angong[0].result_wuxing == "火"

    def test_jia(self):
        """測試夾"""
        # 寅辰夾卯 (相鄰柱位)
        engine = BaziEngine.from_ganzhi("甲寅", "乙辰", "丙午", "丁未")
        gong_jia = engine.compute_gong_jia_an_gong()

        jia = [g for g in gong_jia if g.type == "夾"]
        assert len(jia) >= 1
        assert jia[0].target == "卯"

    def test_no_gong_when_target_exists(self):
        """測試當拱的目標已存在時不算拱"""
        # 寅戌本應拱午，但午已存在
        engine = BaziEngine.from_ganzhi("甲寅", "乙午", "丙戌", "丁卯")
        gong_jia = engine.compute_gong_jia_an_gong()

        angong = [g for g in gong_jia if g.type == "暗拱" and g.target == "午"]
        assert len(angong) == 0


# ============================================================
# Test Case 6: JSON 輸出格式
# ============================================================

class TestJsonOutput:
    """測試 JSON 輸出格式"""

    def test_json_structure(self):
        """測試 JSON 結構"""
        engine = BaziEngine.from_ganzhi("甲子", "乙丑", "丙寅", "丁卯")
        result = engine.to_json()

        # 檢查頂層結構
        assert "step1" in result
        assert "step2" in result
        assert "step3" in result

    def test_step1_structure(self):
        """測試 Step1 結構"""
        engine = BaziEngine.from_ganzhi("甲子", "乙丑", "丙寅", "丁卯")
        step1 = engine.to_json()["step1"]

        assert "四柱" in step1
        assert "日主" in step1
        assert "藏干" in step1

        assert "年柱" in step1["四柱"]
        assert "月柱" in step1["四柱"]
        assert "日柱" in step1["四柱"]
        assert "時柱" in step1["四柱"]

    def test_step2_structure(self):
        """測試 Step2 結構"""
        engine = BaziEngine.from_ganzhi("甲子", "乙丑", "丙寅", "丁卯")
        step2 = engine.to_json()["step2"]

        assert "counts" in step2
        assert "detail" in step2
        assert "missing" in step2
        assert "dominant" in step2

    def test_step3_structure(self):
        """測試 Step3 結構"""
        engine = BaziEngine.from_ganzhi("甲子", "乙丑", "丙寅", "丁卯")
        step3 = engine.to_json()["step3"]

        assert "relations" in step3
        assert "gong_jia_an_gong" in step3

    def test_json_string_output(self):
        """測試 JSON 字串輸出"""
        engine = BaziEngine.from_ganzhi("甲子", "乙丑", "丙寅", "丁卯")
        json_str = engine.to_json_string()

        # 應該是有效的 JSON
        import json
        parsed = json.loads(json_str)
        assert "step1" in parsed


# ============================================================
# Test Case 7: 邊界情況
# ============================================================

class TestEdgeCases:
    """測試邊界情況"""

    def test_same_pillar(self):
        """測試四柱相同"""
        engine = BaziEngine.from_ganzhi("甲子", "甲子", "甲子", "甲子")
        result = engine.to_json()

        # 應該正常運作
        assert engine.day_master == "甲"
        assert result["step2"]["counts"]["木"] > 0

    def test_all_different(self):
        """測試四柱完全不同"""
        engine = BaziEngine.from_ganzhi("甲子", "丙寅", "戊辰", "庚午")
        relations = engine.compute_relations()

        # 應該正常計算關係
        assert isinstance(relations, list)

    def test_cache_consistency(self):
        """測試快取一致性"""
        engine = BaziEngine.from_ganzhi("甲子", "乙丑", "丙寅", "丁卯")

        # 多次調用應返回相同結果
        hidden1 = engine.compute_hidden_stems()
        hidden2 = engine.compute_hidden_stems()
        assert hidden1 is hidden2

        elements1 = engine.compute_five_elements()
        elements2 = engine.compute_five_elements()
        assert elements1 is elements2


# ============================================================
# 執行測試
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
