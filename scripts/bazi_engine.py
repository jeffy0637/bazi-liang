#!/usr/bin/env python3
"""
八字硬計算引擎 (Bazi Hard Computation Engine)

提供可程式驗證的八字基礎計算，確保 LLM 只能做解釋、不能亂編結構。
輸出格式固定，分為 step1/step2/step3 供 eval 驗證使用。
"""

from __future__ import annotations
import json
import argparse
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple, Set
from enum import Enum

# ============================================================
# 基礎常量
# ============================================================

TIANGAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
DIZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

TIANGAN_WUXING = {
    "甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
    "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水"
}

DIZHI_WUXING = {
    "子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土", "巳": "火",
    "午": "火", "未": "土", "申": "金", "酉": "金", "戌": "土", "亥": "水"
}

TIANGAN_YINYANG = {
    "甲": "陽", "乙": "陰", "丙": "陽", "丁": "陰", "戊": "陽",
    "己": "陰", "庚": "陽", "辛": "陰", "壬": "陽", "癸": "陰"
}

DIZHI_YINYANG = {
    "子": "陽", "丑": "陰", "寅": "陽", "卯": "陰", "辰": "陽", "巳": "陰",
    "午": "陽", "未": "陰", "申": "陽", "酉": "陰", "戌": "陽", "亥": "陰"
}

# 地支藏干 (本氣、中氣、餘氣)
DIZHI_CANGGAN = {
    "子": ["癸"],
    "丑": ["己", "癸", "辛"],
    "寅": ["甲", "丙", "戊"],
    "卯": ["乙"],
    "辰": ["戊", "乙", "癸"],
    "巳": ["丙", "戊", "庚"],
    "午": ["丁", "己"],
    "未": ["己", "丁", "乙"],
    "申": ["庚", "壬", "戊"],
    "酉": ["辛"],
    "戌": ["戊", "辛", "丁"],
    "亥": ["壬", "甲"],
}

# 藏干權重 (本氣=1.0, 中氣=0.5, 餘氣=0.3)
CANGGAN_WEIGHT = [1.0, 0.5, 0.3]

# ============================================================
# 地支關係定義
# ============================================================

# 六合
LIUHE = {
    frozenset(["子", "丑"]): "土",
    frozenset(["寅", "亥"]): "木",
    frozenset(["卯", "戌"]): "火",
    frozenset(["辰", "酉"]): "金",
    frozenset(["巳", "申"]): "水",
    frozenset(["午", "未"]): "火",
}

# 六沖
LIUCHONG = {
    frozenset(["子", "午"]),
    frozenset(["丑", "未"]),
    frozenset(["寅", "申"]),
    frozenset(["卯", "酉"]),
    frozenset(["辰", "戌"]),
    frozenset(["巳", "亥"]),
}

# 三合局
SANHE = {
    frozenset(["寅", "午", "戌"]): "火",
    frozenset(["申", "子", "辰"]): "水",
    frozenset(["巳", "酉", "丑"]): "金",
    frozenset(["亥", "卯", "未"]): "木",
}

# 半三合 (缺一支)
BANSANHE = {
    frozenset(["寅", "午"]): ("火", "戌"),
    frozenset(["午", "戌"]): ("火", "寅"),
    frozenset(["寅", "戌"]): ("火", "午"),
    frozenset(["申", "子"]): ("水", "辰"),
    frozenset(["子", "辰"]): ("水", "申"),
    frozenset(["申", "辰"]): ("水", "子"),
    frozenset(["巳", "酉"]): ("金", "丑"),
    frozenset(["酉", "丑"]): ("金", "巳"),
    frozenset(["巳", "丑"]): ("金", "酉"),
    frozenset(["亥", "卯"]): ("木", "未"),
    frozenset(["卯", "未"]): ("木", "亥"),
    frozenset(["亥", "未"]): ("木", "卯"),
}

# 三會方
SANHUI = {
    frozenset(["寅", "卯", "辰"]): "木",
    frozenset(["巳", "午", "未"]): "火",
    frozenset(["申", "酉", "戌"]): "金",
    frozenset(["亥", "子", "丑"]): "水",
}

# 刑 (三刑、自刑)
XING = {
    # 無恩之刑
    frozenset(["寅", "巳"]): "無恩之刑",
    frozenset(["巳", "申"]): "無恩之刑",
    frozenset(["寅", "申"]): "無恩之刑",
    # 持勢之刑
    frozenset(["丑", "戌"]): "持勢之刑",
    frozenset(["戌", "未"]): "持勢之刑",
    frozenset(["丑", "未"]): "持勢之刑",
    # 無禮之刑
    frozenset(["子", "卯"]): "無禮之刑",
}

# 自刑
ZIXING = {"辰", "午", "酉", "亥"}

# 害 (六害)
LIUHAI = {
    frozenset(["子", "未"]),
    frozenset(["丑", "午"]),
    frozenset(["寅", "巳"]),
    frozenset(["卯", "辰"]),
    frozenset(["申", "亥"]),
    frozenset(["酉", "戌"]),
}

# 破
PO = {
    frozenset(["子", "酉"]),
    frozenset(["丑", "辰"]),
    frozenset(["寅", "亥"]),
    frozenset(["卯", "午"]),
    frozenset(["巳", "申"]),
    frozenset(["未", "戌"]),
}

# 天干五合
TIANGAN_WUHE = {
    frozenset(["甲", "己"]): "土",
    frozenset(["乙", "庚"]): "金",
    frozenset(["丙", "辛"]): "水",
    frozenset(["丁", "壬"]): "木",
    frozenset(["戊", "癸"]): "火",
}

# 天干相沖 (對沖)
TIANGAN_CHONG = {
    frozenset(["甲", "庚"]),
    frozenset(["乙", "辛"]),
    frozenset(["丙", "壬"]),
    frozenset(["丁", "癸"]),
}

# 天干相剋
TIANGAN_KE = {
    ("甲", "戊"), ("甲", "己"),  # 木剋土
    ("乙", "戊"), ("乙", "己"),
    ("丙", "庚"), ("丙", "辛"),  # 火剋金
    ("丁", "庚"), ("丁", "辛"),
    ("戊", "壬"), ("戊", "癸"),  # 土剋水
    ("己", "壬"), ("己", "癸"),
    ("庚", "甲"), ("庚", "乙"),  # 金剋木
    ("辛", "甲"), ("辛", "乙"),
    ("壬", "丙"), ("壬", "丁"),  # 水剋火
    ("癸", "丙"), ("癸", "丁"),
}

# ============================================================
# 拱/夾/暗拱 定義
# ============================================================

# 地支序列 (用於判斷夾)
DIZHI_SEQ = {zhi: i for i, zhi in enumerate(DIZHI)}

def get_jia_zhi(zhi1: str, zhi2: str) -> Optional[str]:
    """判斷兩地支是否夾一支 (必須相鄰位置夾中間)"""
    idx1, idx2 = DIZHI_SEQ[zhi1], DIZHI_SEQ[zhi2]
    diff = abs(idx1 - idx2)
    if diff == 2:
        mid_idx = (idx1 + idx2) // 2
        return DIZHI[mid_idx]
    # 跨越子-亥邊界
    if {idx1, idx2} == {0, 10}:
        return "亥"
    if {idx1, idx2} == {1, 11}:
        return "子"
    return None

# 拱合 (暗合局): 兩支夾空形成的虛擬三合
GONG_HE = {
    frozenset(["寅", "戌"]): ("火", "午"),  # 夾午拱火
    frozenset(["申", "辰"]): ("水", "子"),  # 夾子拱水
    frozenset(["巳", "丑"]): ("金", "酉"),  # 夾酉拱金
    frozenset(["亥", "未"]): ("木", "卯"),  # 夾卯拱木
}

# ============================================================
# 數據結構
# ============================================================

@dataclass
class Pillar:
    """單柱 (干支)"""
    gan: str
    zhi: str

    def __post_init__(self):
        if self.gan not in TIANGAN:
            raise ValueError(f"無效天干: {self.gan}")
        if self.zhi not in DIZHI:
            raise ValueError(f"無效地支: {self.zhi}")

    @property
    def ganzhi(self) -> str:
        return f"{self.gan}{self.zhi}"

    @property
    def gan_wuxing(self) -> str:
        return TIANGAN_WUXING[self.gan]

    @property
    def zhi_wuxing(self) -> str:
        return DIZHI_WUXING[self.zhi]

    @property
    def hidden_stems(self) -> List[str]:
        return DIZHI_CANGGAN[self.zhi]

    def to_dict(self) -> dict:
        return {
            "ganzhi": self.ganzhi,
            "gan": self.gan,
            "zhi": self.zhi,
            "gan_wuxing": self.gan_wuxing,
            "gan_yinyang": TIANGAN_YINYANG[self.gan],
            "zhi_wuxing": self.zhi_wuxing,
            "zhi_yinyang": DIZHI_YINYANG[self.zhi],
        }

@dataclass
class HiddenStem:
    """藏干"""
    zhi: str
    stem: str
    role: str  # "本氣", "中氣", "餘氣"
    weight: float
    wuxing: str
    position: str = ""  # "年", "月", "日", "時"

    def to_dict(self) -> dict:
        return {
            "zhi": self.zhi,
            "stem": self.stem,
            "role": self.role,
            "weight": self.weight,
            "wuxing": self.wuxing,
        }

@dataclass
class Relation:
    """干支關係"""
    type: str           # "六合", "六沖", "三合", "三會", "刑", "害", "破", "天干合", "天干沖"
    elements: List[str] # 參與的干/支
    positions: List[str]  # "年", "月", "日", "時"
    result: Optional[str] = None  # 合化結果 / 刑的類型
    note: Optional[str] = None

    def to_dict(self) -> dict:
        d = {
            "type": self.type,
            "elements": self.elements,
            "positions": self.positions,
        }
        if self.result:
            d["result"] = self.result
        if self.note:
            d["note"] = self.note
        return d

@dataclass
class GongJiaAnGong:
    """拱/夾/暗拱"""
    type: str           # "拱", "夾", "暗拱"
    elements: List[str] # 形成拱/夾的兩支
    positions: List[str]
    target: str         # 被拱/夾的支
    result_wuxing: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "elements": self.elements,
            "positions": self.positions,
            "target": self.target,
            "result_wuxing": self.result_wuxing,
        }

# ============================================================
# 主引擎類
# ============================================================

class BaziEngine:
    """
    八字硬計算引擎

    提供 Step0-3 的可程式驗證計算:
    - Step1: 四柱排盤、藏干
    - Step2: 五行統計
    - Step3: 刑沖合會、拱夾暗拱
    """

    POSITION_NAMES = ["年", "月", "日", "時"]

    def __init__(self, year: Pillar, month: Pillar, day: Pillar, hour: Pillar):
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self._pillars = [year, month, day, hour]

        # 快取計算結果
        self._hidden_stems: Optional[List[HiddenStem]] = None
        self._five_elements_with_hidden: Optional[Dict] = None
        self._five_elements_without_hidden: Optional[Dict] = None
        self._relations: Optional[List[Relation]] = None
        self._gong_jia: Optional[List[GongJiaAnGong]] = None

    @classmethod
    def from_ganzhi(cls, year_gz: str, month_gz: str, day_gz: str, hour_gz: str) -> "BaziEngine":
        """從干支字串建立"""
        def parse_gz(gz: str) -> Pillar:
            if len(gz) != 2:
                raise ValueError(f"干支格式錯誤: {gz}")
            return Pillar(gan=gz[0], zhi=gz[1])

        return cls(
            year=parse_gz(year_gz),
            month=parse_gz(month_gz),
            day=parse_gz(day_gz),
            hour=parse_gz(hour_gz),
        )

    @classmethod
    def from_datetime(cls, year: int, month: int, day: int, hour: int) -> "BaziEngine":
        """從西曆日期時間建立 (使用 bazi_calc 的計算邏輯)"""
        from . import bazi_calc

        year_gan, year_zhi = bazi_calc.get_year_ganzhi(year, month, day)
        jieqi_month = bazi_calc.get_jieqi_month(year, month, day)
        month_gan, month_zhi = bazi_calc.get_month_ganzhi(year_gan, jieqi_month)
        day_gan, day_zhi = bazi_calc.get_day_ganzhi(year, month, day)
        hour_gan, hour_zhi = bazi_calc.get_hour_ganzhi(day_gan, hour)

        return cls(
            year=Pillar(bazi_calc.TIANGAN[year_gan], bazi_calc.DIZHI[year_zhi]),
            month=Pillar(bazi_calc.TIANGAN[month_gan], bazi_calc.DIZHI[month_zhi]),
            day=Pillar(bazi_calc.TIANGAN[day_gan], bazi_calc.DIZHI[day_zhi]),
            hour=Pillar(bazi_calc.TIANGAN[hour_gan], bazi_calc.DIZHI[hour_zhi]),
        )

    @property
    def day_master(self) -> str:
        """日主"""
        return self.day.gan

    @property
    def pillars(self) -> List[Pillar]:
        return self._pillars

    @property
    def all_gan(self) -> List[str]:
        """所有天干"""
        return [p.gan for p in self._pillars]

    @property
    def all_zhi(self) -> List[str]:
        """所有地支"""
        return [p.zhi for p in self._pillars]

    # ========================================
    # Step 1: 藏干計算
    # ========================================

    def compute_hidden_stems(self) -> List[HiddenStem]:
        """計算所有藏干"""
        if self._hidden_stems is not None:
            return self._hidden_stems

        result = []
        role_names = ["本氣", "中氣", "餘氣"]

        for idx, pillar in enumerate(self._pillars):
            stems = pillar.hidden_stems
            position = self.POSITION_NAMES[idx]
            for i, stem in enumerate(stems):
                result.append(HiddenStem(
                    zhi=pillar.zhi,
                    stem=stem,
                    role=role_names[i] if i < len(role_names) else "餘氣",
                    weight=CANGGAN_WEIGHT[i] if i < len(CANGGAN_WEIGHT) else 0.3,
                    wuxing=TIANGAN_WUXING[stem],
                    position=position,
                ))

        self._hidden_stems = result
        return result

    # ========================================
    # Step 2: 五行統計
    # ========================================

    def compute_five_elements(self, include_hidden: bool = True) -> Dict:
        """
        計算五行統計

        Returns:
            {
                "counts": {"金": x, "木": x, "水": x, "火": x, "土": x},
                "detail": {
                    "天干": {...},
                    "地支": {...},
                    "藏干": {...}  # if include_hidden
                },
                "missing": [...],  # 缺失的五行
                "dominant": "...", # 最旺的五行
            }
        """
        # 檢查快取
        if include_hidden and self._five_elements_with_hidden is not None:
            return self._five_elements_with_hidden
        if not include_hidden and self._five_elements_without_hidden is not None:
            return self._five_elements_without_hidden

        counts = {"金": 0.0, "木": 0.0, "水": 0.0, "火": 0.0, "土": 0.0}
        detail_gan = {"金": 0, "木": 0, "水": 0, "火": 0, "土": 0}
        detail_zhi = {"金": 0, "木": 0, "水": 0, "火": 0, "土": 0}
        detail_cang = {"金": 0.0, "木": 0.0, "水": 0.0, "火": 0.0, "土": 0.0}

        # 天干五行
        for gan in self.all_gan:
            wx = TIANGAN_WUXING[gan]
            counts[wx] += 1
            detail_gan[wx] += 1

        # 地支五行
        for zhi in self.all_zhi:
            wx = DIZHI_WUXING[zhi]
            counts[wx] += 1
            detail_zhi[wx] += 1

        # 藏干五行
        if include_hidden:
            for hs in self.compute_hidden_stems():
                counts[hs.wuxing] += hs.weight
                detail_cang[hs.wuxing] += hs.weight

        # 缺失五行
        missing = [wx for wx, cnt in counts.items() if cnt == 0]

        # 最旺五行
        dominant = max(counts, key=lambda k: counts[k])

        result = {
            "counts": {k: round(v, 2) for k, v in counts.items()},
            "detail": {
                "天干": detail_gan,
                "地支": detail_zhi,
            },
            "missing": missing,
            "dominant": dominant,
        }

        if include_hidden:
            result["detail"]["藏干"] = {k: round(v, 2) for k, v in detail_cang.items()}
            self._five_elements_with_hidden = result
        else:
            self._five_elements_without_hidden = result

        return result

    # ========================================
    # Step 3: 刑沖合會
    # ========================================

    def compute_relations(self) -> List[Relation]:
        """
        計算所有干支關係: 刑、沖、合、會
        """
        if self._relations is not None:
            return self._relations

        relations = []
        zhi_list = self.all_zhi
        gan_list = self.all_gan
        pos = self.POSITION_NAMES

        # === 地支關係 ===

        # 檢查兩兩組合
        for i in range(4):
            for j in range(i + 1, 4):
                pair = frozenset([zhi_list[i], zhi_list[j]])
                positions = [pos[i], pos[j]]
                elements = [zhi_list[i], zhi_list[j]]

                # 六合
                if pair in LIUHE:
                    relations.append(Relation(
                        type="六合",
                        elements=elements,
                        positions=positions,
                        result=LIUHE[pair],
                    ))

                # 六沖
                if pair in LIUCHONG:
                    relations.append(Relation(
                        type="六沖",
                        elements=elements,
                        positions=positions,
                    ))

                # 刑
                if pair in XING:
                    relations.append(Relation(
                        type="刑",
                        elements=elements,
                        positions=positions,
                        result=XING[pair],
                    ))

                # 害
                if pair in LIUHAI:
                    relations.append(Relation(
                        type="害",
                        elements=elements,
                        positions=positions,
                    ))

                # 破
                if pair in PO:
                    relations.append(Relation(
                        type="破",
                        elements=elements,
                        positions=positions,
                    ))

        # 三合局 (檢查三支組合)
        zhi_set = set(zhi_list)
        for sanhe_set, result_wx in SANHE.items():
            matched = sanhe_set & zhi_set
            if len(matched) == 3:
                # 完整三合
                matched_pos = [pos[i] for i, z in enumerate(zhi_list) if z in sanhe_set]
                relations.append(Relation(
                    type="三合",
                    elements=list(sanhe_set),
                    positions=matched_pos,
                    result=result_wx,
                ))
            elif len(matched) == 2:
                # 半三合
                pair = frozenset(matched)
                if pair in BANSANHE:
                    wx, missing = BANSANHE[pair]
                    matched_pos = [pos[i] for i, z in enumerate(zhi_list) if z in matched]
                    relations.append(Relation(
                        type="半三合",
                        elements=list(matched),
                        positions=matched_pos,
                        result=wx,
                        note=f"缺{missing}",
                    ))

        # 三會方
        for sanhui_set, result_wx in SANHUI.items():
            if sanhui_set <= zhi_set:
                matched_pos = [pos[i] for i, z in enumerate(zhi_list) if z in sanhui_set]
                relations.append(Relation(
                    type="三會",
                    elements=list(sanhui_set),
                    positions=matched_pos,
                    result=result_wx,
                ))

        # 自刑
        for i, zhi in enumerate(zhi_list):
            if zhi in ZIXING:
                # 檢查是否有重複
                if zhi_list.count(zhi) >= 2:
                    dup_pos = [pos[k] for k, z in enumerate(zhi_list) if z == zhi]
                    relations.append(Relation(
                        type="自刑",
                        elements=[zhi, zhi],
                        positions=dup_pos,
                    ))
                    break  # 只記錄一次

        # === 天干關係 ===

        for i in range(4):
            for j in range(i + 1, 4):
                pair = frozenset([gan_list[i], gan_list[j]])
                positions = [pos[i], pos[j]]
                elements = [gan_list[i], gan_list[j]]

                # 天干五合
                if pair in TIANGAN_WUHE:
                    relations.append(Relation(
                        type="天干合",
                        elements=elements,
                        positions=positions,
                        result=TIANGAN_WUHE[pair],
                    ))

                # 天干沖
                if pair in TIANGAN_CHONG:
                    relations.append(Relation(
                        type="天干沖",
                        elements=elements,
                        positions=positions,
                    ))

        self._relations = relations
        return relations

    # ========================================
    # Step 3: 拱/夾/暗拱
    # ========================================

    def compute_gong_jia_an_gong(self) -> List[GongJiaAnGong]:
        """
        計算拱/夾/暗拱

        - 拱: 兩支形成半三合，拱出中間那支
        - 夾: 兩支在地支序列上夾住一支
        - 暗拱: 特定兩支組合形成虛擬三合局
        """
        if self._gong_jia is not None:
            return self._gong_jia

        result = []
        zhi_list = self.all_zhi
        pos = self.POSITION_NAMES
        zhi_set = set(zhi_list)

        # 檢查相鄰柱位的組合 (通常拱夾需要相鄰)
        for i in range(4):
            for j in range(i + 1, 4):
                z1, z2 = zhi_list[i], zhi_list[j]
                pair = frozenset([z1, z2])
                positions = [pos[i], pos[j]]
                elements = [z1, z2]

                # 暗拱 (拱合局)
                if pair in GONG_HE:
                    wx, target = GONG_HE[pair]
                    # 被拱的支不能已存在於命盤中
                    if target not in zhi_set:
                        result.append(GongJiaAnGong(
                            type="暗拱",
                            elements=elements,
                            positions=positions,
                            target=target,
                            result_wuxing=wx,
                        ))

                # 夾 (需要是相鄰位置，且夾的支不在命盤中)
                if abs(i - j) == 1:  # 相鄰柱位
                    jia_target = get_jia_zhi(z1, z2)
                    if jia_target and jia_target not in zhi_set:
                        result.append(GongJiaAnGong(
                            type="夾",
                            elements=elements,
                            positions=positions,
                            target=jia_target,
                            result_wuxing=DIZHI_WUXING[jia_target],
                        ))

        self._gong_jia = result
        return result

    # ========================================
    # 輸出
    # ========================================

    def to_json(self) -> Dict:
        """
        輸出固定格式的 JSON，分為 step1/step2/step3
        """
        hidden = self.compute_hidden_stems()

        return {
            "step1": {
                "四柱": {
                    "年柱": self.year.to_dict(),
                    "月柱": self.month.to_dict(),
                    "日柱": self.day.to_dict(),
                    "時柱": self.hour.to_dict(),
                },
                "日主": self.day_master,
                "藏干": {
                    "年支": [h.to_dict() for h in hidden if h.position == "年"],
                    "月支": [h.to_dict() for h in hidden if h.position == "月"],
                    "日支": [h.to_dict() for h in hidden if h.position == "日"],
                    "時支": [h.to_dict() for h in hidden if h.position == "時"],
                },
            },
            "step2": self.compute_five_elements(include_hidden=True),
            "step3": {
                "relations": [r.to_dict() for r in self.compute_relations()],
                "gong_jia_an_gong": [g.to_dict() for g in self.compute_gong_jia_an_gong()],
            },
        }

    def to_json_string(self, indent: int = 2) -> str:
        """輸出 JSON 字串"""
        return json.dumps(self.to_json(), ensure_ascii=False, indent=indent)


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="八字硬計算引擎 CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
  # 使用干支輸入
  python -m scripts.bazi_engine --year 甲子 --month 乙丑 --day 丙寅 --hour 丁卯

  # 使用西曆日期輸入
  python -m scripts.bazi_engine --datetime 1990 8 15 14
        """
    )

    # 干支輸入
    parser.add_argument("--year", type=str, help="年柱干支，如 甲子")
    parser.add_argument("--month", type=str, help="月柱干支，如 乙丑")
    parser.add_argument("--day", type=str, help="日柱干支，如 丙寅")
    parser.add_argument("--hour", type=str, help="時柱干支，如 丁卯")

    # 西曆輸入
    parser.add_argument("--datetime", nargs=4, type=int, metavar=("YEAR", "MONTH", "DAY", "HOUR"),
                        help="西曆年月日時，如 1990 8 15 14")

    # 輸出選項
    parser.add_argument("--step", type=int, choices=[1, 2, 3],
                        help="只輸出指定步驟 (1=四柱藏干, 2=五行, 3=關係)")
    parser.add_argument("--compact", action="store_true", help="緊湊輸出 (無縮排)")

    args = parser.parse_args()

    # 建立引擎
    if args.datetime:
        engine = BaziEngine.from_datetime(*args.datetime)
    elif args.year and args.month and args.day and args.hour:
        engine = BaziEngine.from_ganzhi(args.year, args.month, args.day, args.hour)
    else:
        parser.print_help()
        return

    # 輸出
    result = engine.to_json()

    if args.step:
        result = result[f"step{args.step}"]

    indent = None if args.compact else 2
    print(json.dumps(result, ensure_ascii=False, indent=indent))


if __name__ == "__main__":
    main()
