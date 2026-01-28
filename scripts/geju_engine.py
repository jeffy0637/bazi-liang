#!/usr/bin/env python3
"""
格局引擎 (Geju Engine) - 梁派取格四步驟版

實現梁派格局判定系統，依據《子平真詮》體系與梁湘潤先生的實務經驗。

核心方法：determine_main_ge() - 梁派取格四步驟
  第一步：三合三會 + 透干 → 最強，直接定格
  第二步：月令藏干透干（本氣 > 中氣 > 餘氣）
  第三步：月令本氣（無透干時）
  第四步：比劫 → 建祿格/羊刃格轉換

同時提供各類數據供 LLM 做進一步分析：
- 月令數據：月支、藏干、透干情況
- 取格證據：三合三會、天透地藏
- 專旺格數據、從格數據、破格數據等
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
# 格局分類（僅供標識，不做判斷）
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
    ZAGE = "雜格"


# 順用格列表（僅供參考，LLM 判斷用）
SHUNONG_GE = {GeType.ZHENGGUAN, GeType.ZHENGYIN, GeType.SHISHEN, GeType.ZHENGCAI,
              GeType.PIANCAI}

# 逆用格列表（僅供參考，LLM 判斷用）
NIYONG_GE = {GeType.QISHA, GeType.SHANGGUAN, GeType.PIANYIN, GeType.YANGREN}


# ============================================================
# 月令十神對應格局
# ============================================================

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
class QuGeEvidence:
    """取格證據"""
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
class QuGeStep:
    """取格步驟結果"""
    step: int                       # 步驟編號 (1-4)
    name: str                       # 步驟名稱
    result: Dict                    # 檢測結果
    conclusion: str                 # "成立" | "不成立"
    ge_type: Optional[GeType] = None  # 若成立，取得的格局
    jian_ge: Optional[GeType] = None  # 兼格（多干透出時）

    def to_dict(self) -> dict:
        return {
            "步驟": self.step,
            "名稱": self.name,
            "檢測結果": self.result,
            "結論": self.conclusion,
            "取格": self.ge_type.value if self.ge_type else None,
            "兼格": self.jian_ge.value if self.jian_ge else None,
        }


@dataclass
class MainGeResult:
    """主格判定結果"""
    main_ge: GeType                 # 主格
    method: str                     # 取格方法
    steps: List[QuGeStep]           # 四步驟推導過程
    jian_ge: Optional[GeType] = None  # 兼格
    confidence: str = "A"           # 置信度 S/A/B/C

    def to_dict(self) -> dict:
        return {
            "主格": self.main_ge.value,
            "取格方法": self.method,
            "推導過程": [s.to_dict() for s in self.steps],
            "兼格": self.jian_ge.value if self.jian_ge else None,
            "置信度": self.confidence,
        }


# ============================================================
# 建祿/羊刃 定義
# ============================================================

# 日主的臨官位（建祿）
JIANLU_ZHI = {
    "甲": "寅", "乙": "卯", "丙": "巳", "丁": "午", "戊": "巳",
    "己": "午", "庚": "申", "辛": "酉", "壬": "亥", "癸": "子",
}

# 日主的帝旺位（羊刃）
YANGREN_ZHI = {
    "甲": "卯", "乙": "寅", "丙": "午", "丁": "巳", "戊": "午",
    "己": "巳", "庚": "酉", "辛": "申", "壬": "子", "癸": "亥",
}


# ============================================================
# 格局引擎
# ============================================================

class GejuEngine:
    """
    格局引擎 - 梁派取格四步驟

    核心方法 determine_main_ge() 實現梁派取格邏輯：
      第一步：三合三會 + 透干 → 最強，直接定格
      第二步：月令藏干透干（本氣 > 中氣 > 餘氣）
      第三步：月令本氣（無透干時）
      第四步：比劫 → 建祿格/羊刃格轉換

    同時保留原有數據方法供進階分析使用。
    """

    POSITION_NAMES = ["年", "月", "日", "時"]

    def __init__(self, bazi: BaziEngine):
        self.bazi = bazi
        self._yueling_zhuge: Optional[YueLingZhuGe] = None
        self._quge_evidence: Optional[List[QuGeEvidence]] = None
        self._main_ge_result: Optional[MainGeResult] = None

    # ========================================
    # 梁派取格四步驟（核心方法）
    # ========================================

    def determine_main_ge(self) -> MainGeResult:
        """
        梁派取格四步驟

        依據梁湘潤先生《子平教材講義》的取格優先順序：
          第一步：三合三會 + 透干 → 最強
          第二步：月令藏干透干（本氣 > 中氣 > 餘氣）
          第三步：月令本氣（無透干時）
          第四步：比劫 → 建祿格/羊刃格

        Returns:
            MainGeResult: 主格判定結果，包含推導過程
        """
        if self._main_ge_result is not None:
            return self._main_ge_result

        steps: List[QuGeStep] = []
        final_ge: Optional[GeType] = None
        final_method: str = ""
        final_jian_ge: Optional[GeType] = None
        final_confidence: str = "A"

        # 第一步：三合三會 + 透干
        step1 = self._step1_hezhi_tougan()
        steps.append(step1)
        if step1.conclusion == "成立":
            final_ge = step1.ge_type
            final_method = step1.name
            final_confidence = "S"
        else:
            # 第二步：月令藏干透干
            step2 = self._step2_yueling_tougan()
            steps.append(step2)
            if step2.conclusion == "成立":
                final_ge = step2.ge_type
                final_jian_ge = step2.jian_ge
                final_method = step2.name
                final_confidence = "A"
            else:
                # 第二步補充：四見成格（補救方法）
                step2b = self._step2b_sijian()
                steps.append(step2b)
                if step2b.conclusion == "成立":
                    final_ge = step2b.ge_type
                    final_method = step2b.name
                    final_confidence = "B"
                else:
                    # 第三步：月令本氣
                    step3 = self._step3_yueling_benqi()
                    steps.append(step3)
                    final_ge = step3.ge_type
                    final_method = step3.name
                    final_confidence = "B"

        # 第四步：比劫轉換（建祿/羊刃）
        if final_ge in (GeType.JIANLU, GeType.YANGREN):
            step4 = self._step4_bijie_convert(final_ge)
            steps.append(step4)
            # 建祿格/羊刃格維持不變，但標記為外格
            final_method = step4.name

        result = MainGeResult(
            main_ge=final_ge,
            method=final_method,
            steps=steps,
            jian_ge=final_jian_ge,
            confidence=final_confidence,
        )

        self._main_ge_result = result
        return result

    def _step1_hezhi_tougan(self) -> QuGeStep:
        """
        第一步：三合三會 + 透干

        檢查地支是否形成三合局或三會方，且該局五行透出天干。
        """
        day_master = self.bazi.day_master
        all_zhi = self.bazi.all_zhi
        all_gan = self.bazi.all_gan
        zhi_set = set(all_zhi)

        result_data = {
            "三合": [],
            "三會": [],
            "成局五行": None,
            "透干": [],
            "成局十神": None,
        }

        # 檢查三合
        for sanhe_set, wuxing in SANHE.items():
            if sanhe_set <= zhi_set:
                result_data["三合"].append({
                    "地支": list(sanhe_set),
                    "五行": wuxing,
                })

        # 檢查三會
        for sanhui_set, wuxing in SANHUI.items():
            if sanhui_set <= zhi_set:
                result_data["三會"].append({
                    "地支": list(sanhui_set),
                    "五行": wuxing,
                })

        # 若有成局，檢查是否透干
        all_hezhi = result_data["三合"] + result_data["三會"]
        if all_hezhi:
            for hezhi in all_hezhi:
                wuxing = hezhi["五行"]
                # 檢查天干是否有該五行（日主除外）
                for i, gan in enumerate(all_gan):
                    if i == 2:  # 日主不算
                        continue
                    if TIANGAN_WUXING[gan] == wuxing:
                        shishen = SHISHEN_TABLE[day_master][gan]
                        # 比劫不能取格
                        if shishen not in ("比肩", "劫財"):
                            result_data["成局五行"] = wuxing
                            result_data["透干"].append({
                                "天干": gan,
                                "位置": self.POSITION_NAMES[i],
                                "十神": shishen,
                            })
                            result_data["成局十神"] = shishen

        # 判斷結論
        if result_data["成局五行"] and result_data["透干"]:
            shishen = result_data["成局十神"]
            ge_type = YUELING_TO_GE.get(shishen, GeType.ZAGE)
            return QuGeStep(
                step=1,
                name="三合三會+透干",
                result=result_data,
                conclusion="成立",
                ge_type=ge_type,
            )
        else:
            return QuGeStep(
                step=1,
                name="三合三會+透干",
                result=result_data,
                conclusion="不成立",
            )

    def _step2_yueling_tougan(self) -> QuGeStep:
        """
        第二步：月令藏干透干

        檢查月支藏干是否透出天干，優先級：本氣 > 中氣 > 餘氣
        """
        day_master = self.bazi.day_master
        yue_zhi = self.bazi.month.zhi
        canggan = DIZHI_CANGGAN[yue_zhi]
        all_gan = self.bazi.all_gan

        result_data = {
            "月支": yue_zhi,
            "藏干": [],
        }

        # 分析每個藏干的透干情況
        for i, gan in enumerate(canggan):
            role = ["本氣", "中氣", "餘氣"][i] if i < 3 else "餘氣"
            shishen = SHISHEN_TABLE[day_master][gan]

            # 檢查是否透干（日主除外）
            tougan_positions = []
            for j, tg in enumerate(all_gan):
                if j == 2:  # 日主不算
                    continue
                if tg == gan:
                    tougan_positions.append(self.POSITION_NAMES[j])

            result_data["藏干"].append({
                "干": gan,
                "角色": role,
                "十神": shishen,
                "透干": len(tougan_positions) > 0,
                "透干位置": tougan_positions,
            })

        # 按優先級找透干的藏干（本氣 > 中氣 > 餘氣）
        main_ge: Optional[GeType] = None
        jian_ge: Optional[GeType] = None
        first_tougan = None

        for cg_info in result_data["藏干"]:
            if cg_info["透干"]:
                shishen = cg_info["十神"]
                # 比劫不能取格
                if shishen in ("比肩", "劫財"):
                    continue

                ge = YUELING_TO_GE.get(shishen, GeType.ZAGE)
                if first_tougan is None:
                    first_tougan = cg_info
                    main_ge = ge
                elif jian_ge is None:
                    # 多干透出：本氣為主，餘氣為輔
                    jian_ge = ge

        if main_ge:
            return QuGeStep(
                step=2,
                name="月令藏干透干",
                result=result_data,
                conclusion="成立",
                ge_type=main_ge,
                jian_ge=jian_ge,
            )
        else:
            return QuGeStep(
                step=2,
                name="月令藏干透干",
                result=result_data,
                conclusion="不成立",
            )

    def _step3_yueling_benqi(self) -> QuGeStep:
        """
        第三步：月令本氣取格

        無透干時，直接取月令本氣定格。
        """
        day_master = self.bazi.day_master
        yue_zhi = self.bazi.month.zhi
        canggan = DIZHI_CANGGAN[yue_zhi]
        benqi = canggan[0]
        shishen = SHISHEN_TABLE[day_master][benqi]
        ge_type = YUELING_TO_GE.get(shishen, GeType.ZAGE)

        result_data = {
            "月支": yue_zhi,
            "本氣": benqi,
            "本氣十神": shishen,
        }

        return QuGeStep(
            step=3,
            name="月令本氣",
            result=result_data,
            conclusion="成立",
            ge_type=ge_type,
        )

    def _step2b_sijian(self) -> QuGeStep:
        """
        第二步補充：四見成格

        當天不透地不藏時，某種五行在四柱（天干+地支藏干）中出現四次以上，
        可勉強取格。代表事業性質較雜，可能是拼湊起來的行業。

        梁師說明：
        - 將陰陽五行混在一起湊數（如庚辛皆算金）
        - 這類格局代表性格或事業「不定性」或「兼雜」
        """
        from collections import Counter

        day_master = self.bazi.day_master
        all_gan = self.bazi.all_gan
        all_zhi = self.bazi.all_zhi

        result_data = {
            "五行統計": {},
            "達四見": [],
            "說明": "檢查五行（含藏干）是否達四次以上",
        }

        # 統計所有五行（天干 + 地支藏干）
        wuxing_counter: Counter = Counter()

        # 天干五行（日主除外）
        for i, gan in enumerate(all_gan):
            if i == 2:  # 日主不算
                continue
            wuxing_counter[TIANGAN_WUXING[gan]] += 1

        # 地支藏干五行
        for zhi in all_zhi:
            for gan in DIZHI_CANGGAN[zhi]:
                wuxing_counter[TIANGAN_WUXING[gan]] += 1

        result_data["五行統計"] = dict(wuxing_counter)

        # 檢查是否有五行達四見
        sijian_list = []
        for wuxing, count in wuxing_counter.items():
            if count >= 4:
                # 找該五行對日主的十神（取陽干）
                yang_gan = {"木": "甲", "火": "丙", "土": "戊", "金": "庚", "水": "壬"}
                gan = yang_gan.get(wuxing, "甲")
                shishen = SHISHEN_TABLE[day_master][gan]

                # 比劫不能取格
                if shishen in ("比肩", "劫財"):
                    continue

                sijian_list.append({
                    "五行": wuxing,
                    "出現次數": count,
                    "十神": shishen,
                })

        result_data["達四見"] = sijian_list

        if sijian_list:
            # 取最多次數的五行
            best = max(sijian_list, key=lambda x: x["出現次數"])
            shishen = best["十神"]
            ge_type = YUELING_TO_GE.get(shishen, GeType.ZAGE)
            result_data["取格依據"] = f"{best['五行']}見{best['出現次數']}次，取{shishen}"

            return QuGeStep(
                step=2,
                name="四見成格",
                result=result_data,
                conclusion="成立",
                ge_type=ge_type,
            )
        else:
            return QuGeStep(
                step=2,
                name="四見成格",
                result=result_data,
                conclusion="不成立",
            )

    def _step4_bijie_convert(self, current_ge: GeType) -> QuGeStep:
        """
        第四步：比劫轉換

        若取得的格局是比肩(建祿)或劫財(羊刃)，標記為外格。
        """
        day_master = self.bazi.day_master
        yue_zhi = self.bazi.month.zhi

        result_data = {
            "原格局": current_ge.value,
            "日主": day_master,
            "月支": yue_zhi,
        }

        # 判斷是建祿還是羊刃
        if yue_zhi == JIANLU_ZHI.get(day_master):
            result_data["類型"] = "建祿格（臨官位）"
            result_data["說明"] = "月令為日主臨官位，日主極強，須官殺制或食傷洩"
        elif yue_zhi == YANGREN_ZHI.get(day_master):
            result_data["類型"] = "羊刃格（帝旺位）"
            result_data["說明"] = "月令為日主帝旺位，日主極強，須官殺制或食傷洩"
        else:
            result_data["類型"] = "比劫格（外格）"
            result_data["說明"] = "月令藏干比劫當令"

        return QuGeStep(
            step=4,
            name="比劫→外格轉換",
            result=result_data,
            conclusion="成立",
            ge_type=current_ge,
        )

    # ========================================
    # 月令數據
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

    def get_yueling_data(self) -> Dict:
        """
        獲取月令完整數據

        Returns:
            Dict: 月令數據
        """
        zhuge = self.get_yueling_zhuge()
        yue_zhi = zhuge.yue_zhi
        canggan = DIZHI_CANGGAN[yue_zhi]

        # 藏干詳細信息
        canggan_detail = []
        for i, gan in enumerate(canggan):
            role = ["本氣", "中氣", "餘氣"][i] if i < 3 else "餘氣"
            weight = CANGGAN_WEIGHT[i] if i < len(CANGGAN_WEIGHT) else 0.3
            shishen = SHISHEN_TABLE[self.bazi.day_master][gan]
            wuxing = TIANGAN_WUXING[gan]
            canggan_detail.append({
                "干": gan,
                "角色": role,
                "權重": weight,
                "十神": shishen,
                "五行": wuxing,
            })

        return {
            "月支": yue_zhi,
            "月支五行": DIZHI_WUXING[yue_zhi],
            "藏干": canggan_detail,
            "本氣": zhuge.yue_zhi_benqi,
            "本氣十神": zhuge.benqi_shishen,
            "月令主格": zhuge.main_ge.value,
            "透干": zhuge.is_tou_gan,
            "透干位置": zhuge.tou_gan_positions,
        }

    # ========================================
    # 取格證據
    # ========================================

    def get_quge_evidence(self) -> List[Dict]:
        """
        獲取取格證據（三合三會、天透地藏等）

        Returns:
            List[Dict]: 取格證據列表
        """
        if self._quge_evidence is not None:
            return [e.to_dict() for e in self._quge_evidence]

        results = []

        # 1. 檢查天透地藏
        zhuge = self.get_yueling_zhuge()
        if zhuge.is_tou_gan:
            results.append(QuGeEvidence(
                method="天透地藏",
                ge_type=zhuge.main_ge,
                evidence=[
                    f"月支{zhuge.yue_zhi}藏{zhuge.yue_zhi_benqi}",
                    f"{zhuge.yue_zhi_benqi}透於{','.join(zhuge.tou_gan_positions)}",
                ],
                confidence="A",
            ))

        # 2. 檢查三合三會
        zhi_set = set(self.bazi.all_zhi)

        # 三合
        for sanhe_set, result_wx in SANHE.items():
            if sanhe_set <= zhi_set:
                results.append(QuGeEvidence(
                    method="三合成局",
                    ge_type=self._wuxing_to_zhuanwang_ge(result_wx),
                    evidence=[f"三合{result_wx}局：{list(sanhe_set)}"],
                    confidence="S",
                ))

        # 三會
        for sanhui_set, result_wx in SANHUI.items():
            if sanhui_set <= zhi_set:
                results.append(QuGeEvidence(
                    method="三會成方",
                    ge_type=self._wuxing_to_zhuanwang_ge(result_wx),
                    evidence=[f"三會{result_wx}方：{list(sanhui_set)}"],
                    confidence="S",
                ))

        # 3. 檢查四見
        all_chars = self.bazi.all_gan + self.bazi.all_zhi
        from collections import Counter
        counts = Counter(all_chars)

        for char, count in counts.items():
            if count >= 4:
                if char in TIANGAN:
                    shishen = SHISHEN_TABLE[self.bazi.day_master][char]
                    ge_type = YUELING_TO_GE.get(shishen, GeType.ZAGE)
                    results.append(QuGeEvidence(
                        method="四見入格",
                        ge_type=ge_type,
                        evidence=[f"{char}見四次，{shishen}旺"],
                        confidence="A",
                    ))

        self._quge_evidence = results
        return [e.to_dict() for e in results]

    def _wuxing_to_zhuanwang_ge(self, wuxing: str) -> GeType:
        """五行轉專旺格（用於三合三會）"""
        wuxing_ge_map = {
            "木": GeType.QUZHUANG,
            "火": GeType.YANSHANG,
            "土": GeType.JIAGE,
            "金": GeType.CONGGE,
            "水": GeType.RUNXIA,
        }
        return wuxing_ge_map.get(wuxing, GeType.ZAGE)

    # ========================================
    # 專旺格數據（不做結論）
    # ========================================

    def get_zhuanwang_data(self) -> Dict:
        """
        獲取專旺格相關數據

        只提供數據，不做「是否成立」的判斷。
        LLM 根據以下數據 + 規則判斷是否成專旺格。

        Returns:
            Dict: 專旺格相關數據
        """
        day_master = self.bazi.day_master
        day_wuxing = TIANGAN_WUXING[day_master]
        yue_zhi = self.bazi.month.zhi
        yue_wuxing = DIZHI_WUXING[yue_zhi]
        all_zhi = self.bazi.all_zhi
        zhi_set = set(all_zhi)

        # 專旺格當令月支
        ZHUANWANG_MONTHS = {
            "木": {"寅", "卯"},
            "火": {"巳", "午"},
            "土": {"辰", "戌", "丑", "未"},
            "金": {"申", "酉"},
            "水": {"亥", "子"},
        }

        # 月令是否與日主五行匹配
        yueling_match = yue_zhi in ZHUANWANG_MONTHS.get(day_wuxing, set())

        # 地支同五行數量
        zhi_same_wuxing_count = sum(1 for z in all_zhi if DIZHI_WUXING[z] == day_wuxing)

        # 三合成局情況
        has_sanhe_same_wuxing = False
        sanhe_info = None
        for sanhe_set, result_wx in SANHE.items():
            if result_wx == day_wuxing and sanhe_set <= zhi_set:
                has_sanhe_same_wuxing = True
                sanhe_info = list(sanhe_set)
                break

        # 三會成方情況
        has_sanhui_same_wuxing = False
        sanhui_info = None
        for sanhui_set, result_wx in SANHUI.items():
            if result_wx == day_wuxing and sanhui_set <= zhi_set:
                has_sanhui_same_wuxing = True
                sanhui_info = list(sanhui_set)
                break

        # 剋日主的五行
        KE_MAP = {"木": "金", "火": "水", "土": "木", "金": "火", "水": "土"}
        ke_wuxing = KE_MAP.get(day_wuxing, "")

        # 天干中剋日主的字
        ke_wuxing_in_tiangan = []
        for gan in self.bazi.all_gan:
            if TIANGAN_WUXING[gan] == ke_wuxing:
                ke_wuxing_in_tiangan.append(gan)

        # 地支本氣中剋日主的字
        ke_wuxing_in_dizhi_benqi = []
        for zhi in all_zhi:
            benqi = DIZHI_CANGGAN[zhi][0]
            if TIANGAN_WUXING[benqi] == ke_wuxing:
                ke_wuxing_in_dizhi_benqi.append(zhi)

        # 專旺格名稱對照
        ZHUANWANG_NAMES = {
            "木": "曲直格",
            "火": "炎上格",
            "土": "稼穡格",
            "金": "從革格",
            "水": "潤下格",
        }

        return {
            "day_wuxing": day_wuxing,
            "zhuanwang_ge_name": ZHUANWANG_NAMES.get(day_wuxing, ""),
            "yueling_match": yueling_match,
            "yueling_zhi": yue_zhi,
            "yueling_wuxing": yue_wuxing,
            "valid_months": list(ZHUANWANG_MONTHS.get(day_wuxing, set())),
            "zhi_same_wuxing_count": zhi_same_wuxing_count,
            "zhi_same_wuxing_list": [z for z in all_zhi if DIZHI_WUXING[z] == day_wuxing],
            "has_sanhe_same_wuxing": has_sanhe_same_wuxing,
            "sanhe_info": sanhe_info,
            "has_sanhui_same_wuxing": has_sanhui_same_wuxing,
            "sanhui_info": sanhui_info,
            "ke_wuxing": ke_wuxing,
            "ke_wuxing_in_tiangan": ke_wuxing_in_tiangan,
            "ke_wuxing_in_dizhi_benqi": ke_wuxing_in_dizhi_benqi,
        }

    # ========================================
    # 從格數據（不做結論）
    # ========================================

    def get_cong_data(self) -> Dict:
        """
        獲取從格相關數據

        只提供數據，不做「是否成立」的判斷。
        LLM 根據以下數據 + 規則判斷是否從格。

        Returns:
            Dict: 從格相關數據
        """
        day_master = self.bazi.day_master
        shishen_summary = self.bazi.get_shishen_summary()
        weighted = shishen_summary.get("weighted_counts", {})

        # 計算各類十神權重
        bijie_weight = weighted.get("比肩", 0) + weighted.get("劫財", 0)
        yinxing_weight = weighted.get("正印", 0) + weighted.get("偏印", 0)
        rizhu_support_weight = bijie_weight + yinxing_weight

        caixing_weight = weighted.get("正財", 0) + weighted.get("偏財", 0)
        guansha_weight = weighted.get("正官", 0) + weighted.get("七殺", 0)
        qisha_weight = weighted.get("七殺", 0)
        shishang_weight = weighted.get("食神", 0) + weighted.get("傷官", 0)

        # 日主是否有本氣根（地支藏干有比劫且為本氣）
        has_benqi_root = False
        root_positions = []
        for item in self.bazi.compute_shishen():
            if item.layer == "地支藏干" and item.shishen in ["比肩", "劫財"]:
                if item.role == "本氣":
                    has_benqi_root = True
                    root_positions.append(item.position)

        # 日主地支根統計（含非本氣）
        all_roots = []
        for item in self.bazi.compute_shishen():
            if item.layer == "地支藏干" and item.shishen in ["比肩", "劫財"]:
                all_roots.append({
                    "position": item.position,
                    "char": item.char,
                    "role": item.role,
                })

        return {
            "day_master": day_master,
            "has_benqi_root": has_benqi_root,
            "benqi_root_positions": root_positions,
            "all_roots": all_roots,
            "rizhu_support_weight": round(rizhu_support_weight, 2),
            "bijie_weight": round(bijie_weight, 2),
            "yinxing_weight": round(yinxing_weight, 2),
            "caixing_weight": round(caixing_weight, 2),
            "guansha_weight": round(guansha_weight, 2),
            "qisha_weight": round(qisha_weight, 2),
            "shishang_weight": round(shishang_weight, 2),
            "weighted_counts": weighted,
        }

    # ========================================
    # 破格數據（不做結論）
    # ========================================

    def get_poge_data(self) -> Dict:
        """
        獲取破格相關數據

        只提供數據，不做「是否破格」的判斷。
        LLM 根據以下數據 + 格局類型判斷是否破格。

        Returns:
            Dict: 破格相關數據
        """
        zhuge = self.get_yueling_zhuge()
        benqi = zhuge.yue_zhi_benqi
        yue_zhi = zhuge.yue_zhi
        main_ge = zhuge.main_ge

        relations = self.bazi.compute_relations()
        shishen_items = self.bazi.compute_shishen()
        shishen_summary = self.bazi.get_shishen_summary()
        weighted = shishen_summary.get("weighted_counts", {})

        # 1. 月支被沖情況
        yuezhi_chong = []
        for r in relations:
            if r.type == "六沖" and yue_zhi in r.elements:
                chong_element = [e for e in r.elements if e != yue_zhi][0]
                chong_position = [p for p in r.positions if p != "月"][0]
                pos_order = {"年": 0, "月": 1, "日": 2, "時": 3}
                is_later_chong = pos_order.get(chong_position, 0) > 1  # 日或時沖月
                yuezhi_chong.append({
                    "沖元素": chong_element,
                    "沖位置": chong_position,
                    "格局柱後破": is_later_chong,
                })

        # 2. 月支被合情況
        yuezhi_he = []
        for r in relations:
            if r.type == "六合" and yue_zhi in r.elements:
                he_element = [e for e in r.elements if e != yue_zhi][0]
                合化 = r.result
                格神五行 = DIZHI_WUXING[yue_zhi]
                yuezhi_he.append({
                    "合元素": he_element,
                    "合化五行": 合化,
                    "格神五行": 格神五行,
                    "五行變質": 合化 != 格神五行,
                })

        # 3. 官殺混雜數據
        guan_weight = weighted.get("正官", 0)
        sha_weight = weighted.get("七殺", 0)
        guansha_hunza = {
            "guan_weight": round(guan_weight, 2),
            "sha_weight": round(sha_weight, 2),
            "both_present": guan_weight > 0 and sha_weight > 0,
        }

        # 4. 財格見比劫數據
        bijie_weight = weighted.get("比肩", 0) + weighted.get("劫財", 0)
        has_bijie_tougan = any(
            item.shishen in ["比肩", "劫財"] and item.layer == "天干"
            for item in shishen_items
        )
        bijie_tougan_list = [
            {"char": item.char, "position": item.position}
            for item in shishen_items
            if item.shishen in ["比肩", "劫財"] and item.layer == "天干"
        ]
        caige_bijie_data = {
            "bijie_weight": round(bijie_weight, 2),
            "has_bijie_tougan": has_bijie_tougan,
            "bijie_tougan_list": bijie_tougan_list,
        }

        # 5. 印格見財數據
        cai_weight = weighted.get("正財", 0) + weighted.get("偏財", 0)
        has_cai_tougan = any(
            item.shishen in ["正財", "偏財"] and item.layer == "天干"
            for item in shishen_items
        )
        cai_tougan_list = [
            {"char": item.char, "position": item.position}
            for item in shishen_items
            if item.shishen in ["正財", "偏財"] and item.layer == "天干"
        ]
        yinge_cai_data = {
            "cai_weight": round(cai_weight, 2),
            "has_cai_tougan": has_cai_tougan,
            "cai_tougan_list": cai_tougan_list,
        }

        # 6. 食神格見偏印數據
        pianyin_weight = weighted.get("偏印", 0)
        has_pianyin_tougan = any(
            item.shishen == "偏印" and item.layer == "天干"
            for item in shishen_items
        )
        pianyin_tougan_list = [
            {"char": item.char, "position": item.position}
            for item in shishen_items
            if item.shishen == "偏印" and item.layer == "天干"
        ]
        shishengs_pianyin_data = {
            "pianyin_weight": round(pianyin_weight, 2),
            "has_pianyin_tougan": has_pianyin_tougan,
            "pianyin_tougan_list": pianyin_tougan_list,
        }

        # 7. 傷官格見官數據
        has_guan_tougan = any(
            item.shishen == "正官" and item.layer == "天干"
            for item in shishen_items
        )
        guan_tougan_list = [
            {"char": item.char, "position": item.position}
            for item in shishen_items
            if item.shishen == "正官" and item.layer == "天干"
        ]
        shangguange_guan_data = {
            "guan_weight": round(guan_weight, 2),
            "has_guan_tougan": has_guan_tougan,
            "guan_tougan_list": guan_tougan_list,
        }

        # 8. 正官格見傷官數據
        shangguan_weight = weighted.get("傷官", 0)
        has_shangguan_tougan = any(
            item.shishen == "傷官" and item.layer == "天干"
            for item in shishen_items
        )
        shangguan_tougan_list = [
            {"char": item.char, "position": item.position}
            for item in shishen_items
            if item.shishen == "傷官" and item.layer == "天干"
        ]
        zhengguange_shangguan_data = {
            "shangguan_weight": round(shangguan_weight, 2),
            "has_shangguan_tougan": has_shangguan_tougan,
            "shangguan_tougan_list": shangguan_tougan_list,
        }

        # 9. 七殺格制化數據
        shishen_weight = weighted.get("食神", 0)
        yinxing_weight = weighted.get("正印", 0) + weighted.get("偏印", 0)
        qisha_zhihua_data = {
            "qisha_weight": round(sha_weight, 2),
            "shishen_weight": round(shishen_weight, 2),
            "yinxing_weight": round(yinxing_weight, 2),
            "bijie_weight": round(bijie_weight, 2),
        }

        return {
            "月令主格": main_ge.value,
            "月支": yue_zhi,
            "yuezhi_chong": yuezhi_chong,
            "yuezhi_he": yuezhi_he,
            "guansha_hunza": guansha_hunza,
            "caige_bijie_data": caige_bijie_data,
            "yinge_cai_data": yinge_cai_data,
            "shishengs_pianyin_data": shishengs_pianyin_data,
            "shangguange_guan_data": shangguange_guan_data,
            "zhengguange_shangguan_data": zhengguange_shangguan_data,
            "qisha_zhihua_data": qisha_zhihua_data,
        }

    # ========================================
    # 順逆用數據（不做結論）
    # ========================================

    def get_shunni_data(self) -> Dict:
        """
        獲取順逆用相關數據

        只提供數據，不做「順用/逆用」的判斷。
        LLM 根據以下數據 + 規則判斷順逆用。

        Returns:
            Dict: 順逆用相關數據
        """
        zhuge = self.get_yueling_zhuge()
        main_ge = zhuge.main_ge

        # 取格證據
        quge_evidence = self.get_quge_evidence()
        has_sanhe_sanhui = any(
            e["method"] in ["三合成局", "三會成方"]
            for e in quge_evidence
        )

        # 格局分類參考
        is_shunong_ge = main_ge in SHUNONG_GE
        is_niyong_ge = main_ge in NIYONG_GE

        return {
            "月令主格": main_ge.value,
            "has_sanhe_sanhui_chengjv": has_sanhe_sanhui,
            "sanhe_sanhui_evidence": [
                e for e in quge_evidence
                if e["method"] in ["三合成局", "三會成方"]
            ],
            "is_shunong_ge_candidate": is_shunong_ge,
            "is_niyong_ge_candidate": is_niyong_ge,
            "shunong_ge_list": [g.value for g in SHUNONG_GE],
            "niyong_ge_list": [g.value for g in NIYONG_GE],
        }

    # ========================================
    # 完整輸出
    # ========================================

    def to_json(self) -> Dict:
        """
        輸出完整格局數據

        包含：
        - 主格判定：梁派取格四步驟的結果（核心）
        - 月令數據、取格證據等輔助數據
        """
        main_ge_result = self.determine_main_ge()

        return {
            "主格判定": main_ge_result.to_dict(),
            "月令數據": self.get_yueling_data(),
            "取格證據": self.get_quge_evidence(),
            "專旺格數據": self.get_zhuanwang_data(),
            "從格數據": self.get_cong_data(),
            "破格數據": self.get_poge_data(),
            "順逆用數據": self.get_shunni_data(),
        }


# ============================================================
# CLI
# ============================================================

def main():
    import argparse
    import json

    parser = argparse.ArgumentParser(description="格局數據引擎 CLI")
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
