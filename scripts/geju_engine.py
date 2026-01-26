#!/usr/bin/env python3
"""
格局引擎 (Geju Engine)

實現梁派格局判斷系統，包含：
- 月令主格（底盤）
- 取格四法
- 順用/逆用判定
- 破格檢測

梁派核心理念：格=月令當令，不必透干亦成立。
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Set
from enum import Enum

from .bazi_engine import (
    BaziEngine, TIANGAN, DIZHI, DIZHI_CANGGAN, CANGGAN_WEIGHT,
    SHISHEN_TABLE, SHISHEN_NAMES, TIANGAN_WUXING, DIZHI_WUXING,
    SANHE, SANHUI, LIUCHONG
)


# ============================================================
# 格局分類
# ============================================================

class GeType(Enum):
    """格局類型"""
    # 八正格（順用）
    ZHENGCAI = "正財格"
    PIANCAI = "偏財格"
    ZHENGGUAN = "正官格"
    QISHA = "七殺格"      # 也稱偏官格
    ZHENGYIN = "正印格"
    PIANYIN = "偏印格"    # 也稱梟神格
    SHISHEN = "食神格"
    SHANGGUAN = "傷官格"

    # 特殊格
    JIANLU = "建祿格"     # 月令見比肩
    YANGREN = "羊刃格"    # 月令見劫財

    # 從格/專旺格
    CONGCAI = "從財格"
    CONGSHA = "從殺格"
    CONGER = "從兒格"     # 從食傷
    CONGWANG = "從旺格"
    QUZHUANG = "曲直格"   # 木專旺
    YANSHANG = "炎上格"   # 火專旺
    JIAGE = "稼穡格"      # 土專旺
    CONGGE = "從革格"     # 金專旺
    RUNXIA = "潤下格"     # 水專旺

    # 雜格
    HUAQI = "化氣格"
    ZAGE = "雜格"


# 順用格（用正神）：官、印、食、財
SHUNONG_GE = {GeType.ZHENGGUAN, GeType.ZHENGYIN, GeType.SHISHEN, GeType.ZHENGCAI,
              GeType.PIANCAI}  # 偏財也可順用

# 逆用格（用煞制化）：殺、傷、梟、刃
NIYONG_GE = {GeType.QISHA, GeType.SHANGGUAN, GeType.PIANYIN, GeType.YANGREN}


# ============================================================
# 月令十神對應格局
# ============================================================

# 月令本氣十神 -> 格局
YUELING_TO_GE = {
    "正財": GeType.ZHENGCAI,
    "偏財": GeType.PIANCAI,
    "正官": GeType.ZHENGGUAN,
    "七殺": GeType.QISHA,
    "正印": GeType.ZHENGYIN,
    "偏印": GeType.PIANYIN,
    "食神": GeType.SHISHEN,
    "傷官": GeType.SHANGGUAN,
    "比肩": GeType.JIANLU,
    "劫財": GeType.YANGREN,
}


# ============================================================
# 數據結構
# ============================================================

@dataclass
class YueLingZhuGe:
    """月令主格信息"""
    yue_zhi: str                    # 月支
    yue_zhi_benqi: str              # 月支本氣
    benqi_shishen: str              # 本氣十神
    main_ge: GeType                 # 主格
    zhong_qi: Optional[str] = None  # 中氣
    yu_qi: Optional[str] = None     # 餘氣
    is_tou_gan: bool = False        # 是否透干顯化
    tou_gan_positions: List[str] = field(default_factory=list)  # 透干位置

    def to_dict(self) -> dict:
        return {
            "月支": self.yue_zhi,
            "本氣": self.yue_zhi_benqi,
            "本氣十神": self.benqi_shishen,
            "主格": self.main_ge.value,
            "中氣": self.zhong_qi,
            "餘氣": self.yu_qi,
            "透干": self.is_tou_gan,
            "透干位置": self.tou_gan_positions,
        }


@dataclass
class QuGeResult:
    """取格結果"""
    method: str                     # 取格方式
    ge_type: GeType                 # 格局類型
    evidence: List[str]             # 證據
    confidence: str = "B"           # S/A/B/C 四級

    def to_dict(self) -> dict:
        return {
            "method": self.method,
            "ge_type": self.ge_type.value,
            "evidence": self.evidence,
            "confidence": self.confidence,
        }


@dataclass
class PoGeResult:
    """破格結果"""
    is_poge: bool                   # 是否破格
    po_type: Optional[str] = None   # 破格類型
    po_element: Optional[str] = None  # 破格元素
    po_position: Optional[str] = None  # 破格位置
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = {"is_poge": self.is_poge}
        if self.is_poge:
            d["po_type"] = self.po_type
            d["po_element"] = self.po_element
            d["po_position"] = self.po_position
            d["notes"] = self.notes
        return d


# ============================================================
# 格局引擎
# ============================================================

class GejuEngine:
    """
    格局引擎

    實現梁派格局判斷，核心步驟：
    1. 確定月令主格（底盤）
    2. 檢查取格四法
    3. 判定順用/逆用
    4. 檢測破格
    """

    def __init__(self, bazi: BaziEngine):
        self.bazi = bazi
        self._yueling_zhuge: Optional[YueLingZhuGe] = None
        self._quge_results: Optional[List[QuGeResult]] = None
        self._poge_result: Optional[PoGeResult] = None

    # ========================================
    # 月令主格
    # ========================================

    def get_yueling_zhuge(self) -> YueLingZhuGe:
        """
        獲取月令主格（底盤）

        梁派定義：格=月令當令，月支藏干本氣對日主的十神即為格。
        不必透干亦可成格，透干只是「顯化」。

        Returns:
            YueLingZhuGe: 月令主格信息
        """
        if self._yueling_zhuge is not None:
            return self._yueling_zhuge

        day_master = self.bazi.day_master
        yue_zhi = self.bazi.month.zhi
        canggan = DIZHI_CANGGAN[yue_zhi]

        # 本氣（第一個藏干）
        benqi = canggan[0]
        benqi_shishen = SHISHEN_TABLE[day_master][benqi]
        main_ge = YUELING_TO_GE.get(benqi_shishen, GeType.ZAGE)

        # 中氣、餘氣
        zhong_qi = canggan[1] if len(canggan) > 1 else None
        yu_qi = canggan[2] if len(canggan) > 2 else None

        # 檢查是否透干
        is_tou = False
        tou_positions = []
        all_gan = self.bazi.all_gan
        pos_names = self.bazi.POSITION_NAMES

        for i, gan in enumerate(all_gan):
            if i == 2:  # 日主不算
                continue
            if gan == benqi:
                is_tou = True
                tou_positions.append(pos_names[i])

        result = YueLingZhuGe(
            yue_zhi=yue_zhi,
            yue_zhi_benqi=benqi,
            benqi_shishen=benqi_shishen,
            main_ge=main_ge,
            zhong_qi=zhong_qi,
            yu_qi=yu_qi,
            is_tou_gan=is_tou,
            tou_gan_positions=tou_positions,
        )

        self._yueling_zhuge = result
        return result

    # ========================================
    # 取格四法
    # ========================================

    def check_quge_sifa(self) -> List[QuGeResult]:
        """
        檢查取格四法

        梁派取格四法：
        1. 天透地藏：月支藏干透於天干
        2. 三合三會：地支三合或三會成局
        3. 四見入格：同一字見四次（透干）或四根（不透）
        4. 陰陽相見：特殊混格情況

        Returns:
            List[QuGeResult]: 取格結果列表
        """
        if self._quge_results is not None:
            return self._quge_results

        results = []

        # 1. 檢查天透地藏
        ttdz_result = self._check_tian_tou_di_cang()
        if ttdz_result:
            results.append(ttdz_result)

        # 2. 檢查三合三會
        shsj_results = self._check_sanhe_sanhui()
        results.extend(shsj_results)

        # 3. 檢查四見
        sijian_result = self._check_sijian()
        if sijian_result:
            results.append(sijian_result)

        self._quge_results = results
        return results

    def _check_tian_tou_di_cang(self) -> Optional[QuGeResult]:
        """檢查天透地藏"""
        zhuge = self.get_yueling_zhuge()

        if zhuge.is_tou_gan:
            return QuGeResult(
                method="天透地藏",
                ge_type=zhuge.main_ge,
                evidence=[
                    f"月支{zhuge.yue_zhi}藏{zhuge.yue_zhi_benqi}",
                    f"{zhuge.yue_zhi_benqi}透於{','.join(zhuge.tou_gan_positions)}",
                ],
                confidence="A",
            )
        return None

    def _check_sanhe_sanhui(self) -> List[QuGeResult]:
        """檢查三合三會成局"""
        results = []
        zhi_set = set(self.bazi.all_zhi)

        # 三合
        for sanhe_set, result_wx in SANHE.items():
            if sanhe_set <= zhi_set:
                ge_type = self._wuxing_to_ge(result_wx)
                results.append(QuGeResult(
                    method="三合成局",
                    ge_type=ge_type,
                    evidence=[f"三合{result_wx}局：{list(sanhe_set)}"],
                    confidence="S",  # 三合成局是 S 級證據
                ))

        # 三會
        for sanhui_set, result_wx in SANHUI.items():
            if sanhui_set <= zhi_set:
                ge_type = self._wuxing_to_ge(result_wx)
                results.append(QuGeResult(
                    method="三會成方",
                    ge_type=ge_type,
                    evidence=[f"三會{result_wx}方：{list(sanhui_set)}"],
                    confidence="S",  # 三會成方也是 S 級
                ))

        return results

    def _check_sijian(self) -> Optional[QuGeResult]:
        """檢查四見（同字四次）"""
        all_chars = self.bazi.all_gan + self.bazi.all_zhi

        from collections import Counter
        counts = Counter(all_chars)

        for char, count in counts.items():
            if count >= 4:
                if char in TIANGAN:
                    shishen = SHISHEN_TABLE[self.bazi.day_master][char]
                    ge_type = YUELING_TO_GE.get(shishen, GeType.ZAGE)
                    return QuGeResult(
                        method="四見入格",
                        ge_type=ge_type,
                        evidence=[f"{char}見四次，{shishen}旺"],
                        confidence="A",
                    )
        return None

    def _wuxing_to_ge(self, wuxing: str) -> GeType:
        """五行轉格局（用於三合三會）"""
        day_master = self.bazi.day_master
        day_wuxing = TIANGAN_WUXING[day_master]

        # 根據五行生剋關係判斷格局
        # 簡化處理：三合三會成局通常歸為專旺或從格
        wuxing_ge_map = {
            "木": GeType.QUZHUANG,
            "火": GeType.YANSHANG,
            "土": GeType.JIAGE,
            "金": GeType.CONGGE,
            "水": GeType.RUNXIA,
        }
        return wuxing_ge_map.get(wuxing, GeType.ZAGE)

    # ========================================
    # 順用/逆用
    # ========================================

    def judge_shunni(self) -> Dict:
        """
        判斷順用/逆用

        梁派定義：
        - 順用：官、印、食、財 → 用相神護格
        - 逆用：殺、傷、梟、刃 → 需制化
        - 三合三會成局一律逆用

        Returns:
            {
                "shunni": "順用" | "逆用",
                "main_ge": str,
                "reason": str,
                "yongshen_direction": str  # 用神方向提示
            }
        """
        zhuge = self.get_yueling_zhuge()
        main_ge = zhuge.main_ge

        # 檢查是否有三合三會成局
        quge_results = self.check_quge_sifa()
        has_chenuju = any(r.method in ["三合成局", "三會成方"] for r in quge_results)

        if has_chenuju:
            return {
                "shunni": "逆用",
                "main_ge": main_ge.value,
                "reason": "三合/三會成局，一律逆用",
                "yongshen_direction": "需制化或引泄",
            }

        if main_ge in SHUNONG_GE:
            return {
                "shunni": "順用",
                "main_ge": main_ge.value,
                "reason": f"{main_ge.value}為順用格",
                "yongshen_direction": "護格、助格",
            }
        elif main_ge in NIYONG_GE:
            return {
                "shunni": "逆用",
                "main_ge": main_ge.value,
                "reason": f"{main_ge.value}為逆用格",
                "yongshen_direction": "制化、引泄",
            }
        else:
            return {
                "shunni": "待定",
                "main_ge": main_ge.value,
                "reason": "特殊格局，需進一步分析",
                "yongshen_direction": "視具體情況",
            }

    # ========================================
    # 破格檢測
    # ========================================

    def check_poge(self) -> PoGeResult:
        """
        檢測破格

        破格類型：
        1. 沖破：格神被沖
        2. 合去：格神被合走
        3. 傷格：不利元素傷害格神

        梁派：破格先後（格局柱後破加重）

        Returns:
            PoGeResult: 破格結果
        """
        if self._poge_result is not None:
            return self._poge_result

        zhuge = self.get_yueling_zhuge()
        benqi = zhuge.yue_zhi_benqi
        yue_zhi = zhuge.yue_zhi
        main_ge = zhuge.main_ge

        notes = []
        is_poge = False
        po_type = None
        po_element = None
        po_position = None

        # 1. 檢查月支被沖
        relations = self.bazi.compute_relations()
        for r in relations:
            if r.type == "六沖" and yue_zhi in r.elements:
                is_poge = True
                po_type = "沖破"
                po_element = [e for e in r.elements if e != yue_zhi][0]
                po_position = [p for p in r.positions if p != "月"][0]
                notes.append(f"月支{yue_zhi}被{po_element}沖")

                # 檢查破格先後
                pos_order = {"年": 0, "月": 1, "日": 2, "時": 3}
                if pos_order.get(po_position, 0) > 1:  # 日或時沖月
                    notes.append("格局柱後破，加重")
                break

        # 2. 檢查格神被合
        if not is_poge:
            for r in relations:
                if r.type == "六合" and yue_zhi in r.elements:
                    # 合不一定破格，看是否合化成異類
                    合化 = r.result
                    格神五行 = DIZHI_WUXING[yue_zhi]
                    if 合化 != 格神五行:
                        is_poge = True
                        po_type = "合去"
                        po_element = [e for e in r.elements if e != yue_zhi][0]
                        notes.append(f"月支{yue_zhi}與{po_element}合化{合化}，格神變質")
                        break

        # 3. 檢查傷格（簡化版：正官格見傷官）
        if not is_poge and main_ge == GeType.ZHENGGUAN:
            shishen_items = self.bazi.compute_shishen()
            for item in shishen_items:
                if item.shishen == "傷官" and item.layer == "天干":
                    is_poge = True
                    po_type = "傷格"
                    po_element = item.char
                    po_position = item.position
                    notes.append(f"正官格見傷官（{item.char}在{item.position}）")
                    break

        result = PoGeResult(
            is_poge=is_poge,
            po_type=po_type,
            po_element=po_element,
            po_position=po_position,
            notes=notes,
        )

        self._poge_result = result
        return result

    # ========================================
    # 完整輸出
    # ========================================

    def to_json(self) -> Dict:
        """輸出完整格局分析"""
        return {
            "月令主格": self.get_yueling_zhuge().to_dict(),
            "取格四法": [r.to_dict() for r in self.check_quge_sifa()],
            "順逆用": self.judge_shunni(),
            "破格檢測": self.check_poge().to_dict(),
        }


# ============================================================
# CLI
# ============================================================

def main():
    import argparse
    import json

    parser = argparse.ArgumentParser(description="格局引擎 CLI")
    parser.add_argument("--year", type=str, required=True, help="年柱干支")
    parser.add_argument("--month", type=str, required=True, help="月柱干支")
    parser.add_argument("--day", type=str, required=True, help="日柱干支")
    parser.add_argument("--hour", type=str, required=True, help="時柱干支")

    args = parser.parse_args()

    bazi = BaziEngine.from_ganzhi(args.year, args.month, args.day, args.hour)
    engine = GejuEngine(bazi)

    result = engine.to_json()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
