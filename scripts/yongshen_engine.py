#!/usr/bin/env python3
"""
用神引擎 (Yongshen Engine)

實現梁派用神系統，六標籤制：
1. 調候用神：寒暖燥濕調節
2. 格局用神：護格、助格
3. 通關用神：化解對峙
4. 病藥用神：去病得藥
5. 專旺用神：順勢引泄
6. 扶抑喜忌：日主強弱調節

梁派禁忌：禁用百分比，只用定性描述。
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Set
from enum import Enum

from .bazi_engine import (
    BaziEngine, TIANGAN, DIZHI, TIANGAN_WUXING, DIZHI_WUXING,
    SHISHEN_TABLE, TIANGAN_YINYANG, DIZHI_YINYANG
)
from .geju_engine import GejuEngine, GeType, SHUNONG_GE, NIYONG_GE


# ============================================================
# 調候常量
# ============================================================

# 月支季節
ZHI_SEASON = {
    "寅": "春", "卯": "春", "辰": "春",
    "巳": "夏", "午": "夏", "未": "夏",
    "申": "秋", "酉": "秋", "戌": "秋",
    "亥": "冬", "子": "冬", "丑": "冬",
}

# 季節寒暖
SEASON_TEMP = {
    "春": "溫",
    "夏": "熱",
    "秋": "涼",
    "冬": "寒",
}

# 調候用神表（簡化版：日主 + 季節 → 調候用神）
# 格式：TIAOHUO_TABLE[日主五行][季節] = (主調候, 輔調候, 理由)
TIAOHUO_TABLE = {
    "木": {
        "春": ("水", "火", "春木需水滋養，火暖之"),
        "夏": ("水", None, "夏木焦枯，急需水潤"),
        "秋": ("水", "火", "秋木凋零，水生之火暖之"),
        "冬": ("火", "水", "冬木寒凍，火暖為先"),
    },
    "火": {
        "春": ("木", None, "春火得木生旺"),
        "夏": ("水", "金", "夏火太旺，水制金洩"),
        "秋": ("木", None, "秋火衰弱，木生之"),
        "冬": ("木", None, "冬火弱極，木生火暖"),
    },
    "土": {
        "春": ("火", None, "春土虛浮，火生之"),
        "夏": ("水", None, "夏土燥烈，水潤之"),
        "秋": ("火", None, "秋土洩氣，火生之"),
        "冬": ("火", None, "冬土寒凍，火暖之"),
    },
    "金": {
        "春": ("土", None, "春金休囚，土生之"),
        "夏": ("水", "土", "夏金熔化，水冷土生"),
        "秋": ("火", "水", "秋金太旺，火制水洩"),
        "冬": ("火", "土", "冬金寒凝，火暖土生"),
    },
    "水": {
        "春": ("金", None, "春水洩氣，金生之"),
        "夏": ("金", "水", "夏水枯涸，金生水助"),
        "秋": ("金", None, "秋水得金生旺"),
        "冬": ("火", "木", "冬水寒凝，火暖木洩"),
    },
}


# ============================================================
# 數據結構
# ============================================================

class YongShenType(Enum):
    """用神類型"""
    TIAOHUO = "調候用神"
    GEJU = "格局用神"
    TONGGUAN = "通關用神"
    BINGYAO = "病藥用神"
    ZHUANWANG = "專旺用神"
    FUYI = "扶抑喜忌"


@dataclass
class YongShenItem:
    """用神項目"""
    type: YongShenType
    wuxing: str                     # 用神五行
    priority: int                   # 優先級 (1-6)
    reason: str                     # 取用理由
    is_primary: bool = True         # 是否主用神
    auxiliary: Optional[str] = None # 輔助用神五行

    def to_dict(self) -> dict:
        d = {
            "type": self.type.value,
            "wuxing": self.wuxing,
            "priority": self.priority,
            "reason": self.reason,
            "is_primary": self.is_primary,
        }
        if self.auxiliary:
            d["auxiliary"] = self.auxiliary
        return d


@dataclass
class XiJiResult:
    """喜忌結果"""
    xi: List[str]                   # 喜神五行
    ji: List[str]                   # 忌神五行
    xian: List[str]                 # 閒神五行
    chou: Optional[str] = None      # 仇神五行
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "喜": self.xi,
            "忌": self.ji,
            "閒": self.xian,
            "仇": self.chou,
            "notes": self.notes,
        }


# ============================================================
# 用神引擎
# ============================================================

class YongShenEngine:
    """
    用神引擎

    實現梁派六標籤制用神系統。

    取用神順序：
    1. 調候（寒暖燥濕優先）
    2. 格局（護格助格）
    3. 通關（化解對峙）
    4. 病藥（去病得藥）
    5. 專旺（順勢引泄）
    6. 扶抑（強弱調節）
    """

    LABELS = [
        YongShenType.TIAOHUO,
        YongShenType.GEJU,
        YongShenType.TONGGUAN,
        YongShenType.BINGYAO,
        YongShenType.ZHUANWANG,
        YongShenType.FUYI,
    ]

    def __init__(self, bazi: BaziEngine, geju: Optional[GejuEngine] = None):
        self.bazi = bazi
        self.geju = geju or GejuEngine(bazi)

        self._yongshen_list: Optional[List[YongShenItem]] = None
        self._xiji_result: Optional[XiJiResult] = None

    # ========================================
    # 調候用神
    # ========================================

    def get_tiaohuo_yongshen(self) -> YongShenItem:
        """
        獲取調候用神

        梁派兩層調候：
        - 第一層：日主對月令（基本寒暖燥濕）
        - 第二層：格局對月令（格神需要的調候）

        Returns:
            YongShenItem: 調候用神
        """
        day_master = self.bazi.day_master
        day_wuxing = TIANGAN_WUXING[day_master]
        yue_zhi = self.bazi.month.zhi
        season = ZHI_SEASON[yue_zhi]

        # 第一層：日主調候
        tiaohuo_info = TIAOHUO_TABLE.get(day_wuxing, {}).get(season)

        if tiaohuo_info:
            primary, auxiliary, reason = tiaohuo_info
            return YongShenItem(
                type=YongShenType.TIAOHUO,
                wuxing=primary,
                priority=1,
                reason=f"日主{day_master}（{day_wuxing}）生於{season}月（{yue_zhi}），{reason}",
                is_primary=True,
                auxiliary=auxiliary,
            )
        else:
            return YongShenItem(
                type=YongShenType.TIAOHUO,
                wuxing="待定",
                priority=1,
                reason="調候情況需進一步分析",
                is_primary=True,
            )

    # ========================================
    # 格局用神
    # ========================================

    def get_geju_yongshen(self) -> YongShenItem:
        """
        獲取格局用神

        順用格：護格、助格
        逆用格：制化、引泄

        Returns:
            YongShenItem: 格局用神
        """
        shunni = self.geju.judge_shunni()
        zhuge = self.geju.get_yueling_zhuge()
        main_ge = zhuge.main_ge

        if shunni["shunni"] == "順用":
            # 順用格用相神護格
            yongshen_wuxing = self._get_xiangshen_wuxing(main_ge)
            reason = f"{main_ge.value}順用，取{yongshen_wuxing}為相神護格"
        elif shunni["shunni"] == "逆用":
            # 逆用格需制化
            yongshen_wuxing = self._get_zhihua_wuxing(main_ge)
            reason = f"{main_ge.value}逆用，取{yongshen_wuxing}制化"
        else:
            yongshen_wuxing = "待定"
            reason = "格局特殊，需進一步分析"

        return YongShenItem(
            type=YongShenType.GEJU,
            wuxing=yongshen_wuxing,
            priority=2,
            reason=reason,
        )

    def _get_xiangshen_wuxing(self, ge_type: GeType) -> str:
        """獲取相神五行（順用格）"""
        # 簡化版：根據格局返回相神
        xiangshen_map = {
            GeType.ZHENGCAI: "食神五行",  # 財格用食傷生財
            GeType.PIANCAI: "食神五行",
            GeType.ZHENGGUAN: "財五行",   # 官格用財生官
            GeType.ZHENGYIN: "官五行",    # 印格用官生印
            GeType.SHISHEN: "財五行",     # 食神格用財洩食
        }

        # 返回對應的五行（這裡簡化處理，實際需要根據日主計算）
        day_wuxing = TIANGAN_WUXING[self.bazi.day_master]
        wuxing_cycle = ["木", "火", "土", "金", "水"]
        idx = wuxing_cycle.index(day_wuxing)

        if ge_type in [GeType.ZHENGCAI, GeType.PIANCAI]:
            # 財格用食傷（我生者）
            return wuxing_cycle[(idx + 1) % 5]
        elif ge_type == GeType.ZHENGGUAN:
            # 官格用財（我剋者）
            return wuxing_cycle[(idx + 2) % 5]
        elif ge_type == GeType.ZHENGYIN:
            # 印格用官（剋我者）
            return wuxing_cycle[(idx + 4) % 5]
        elif ge_type == GeType.SHISHEN:
            # 食神格用財
            return wuxing_cycle[(idx + 2) % 5]
        else:
            return "待定"

    def _get_zhihua_wuxing(self, ge_type: GeType) -> str:
        """獲取制化五行（逆用格）"""
        day_wuxing = TIANGAN_WUXING[self.bazi.day_master]
        wuxing_cycle = ["木", "火", "土", "金", "水"]
        idx = wuxing_cycle.index(day_wuxing)

        if ge_type == GeType.QISHA:
            # 七殺格用食神制殺
            return wuxing_cycle[(idx + 1) % 5]
        elif ge_type == GeType.SHANGGUAN:
            # 傷官格用印制傷
            return wuxing_cycle[(idx + 3) % 5]
        elif ge_type == GeType.PIANYIN:
            # 偏印格用財制梟
            return wuxing_cycle[(idx + 2) % 5]
        elif ge_type == GeType.YANGREN:
            # 羊刃格用官殺制刃
            return wuxing_cycle[(idx + 4) % 5]
        else:
            return "待定"

    # ========================================
    # 通關用神
    # ========================================

    def get_tongguan_yongshen(self) -> Optional[YongShenItem]:
        """
        獲取通關用神

        當兩行對峙時，取中間五行通關。
        例如：金木對峙，取水通關。

        Returns:
            Optional[YongShenItem]: 通關用神（無對峙則返回 None）
        """
        five_elements = self.bazi.compute_five_elements(include_hidden=True)
        counts = five_elements["counts"]

        # 檢查對峙情況（兩行都強，且相剋）
        wuxing_list = ["木", "火", "土", "金", "水"]
        ke_pairs = [
            ("木", "土"),  # 木剋土
            ("火", "金"),  # 火剋金
            ("土", "水"),  # 土剋水
            ("金", "木"),  # 金剋木
            ("水", "火"),  # 水剋火
        ]

        for ke, bei_ke in ke_pairs:
            if counts[ke] >= 3 and counts[bei_ke] >= 3:
                # 找通關五行（被剋者生者）
                bei_ke_idx = wuxing_list.index(bei_ke)
                tongguan = wuxing_list[(bei_ke_idx + 1) % 5]

                return YongShenItem(
                    type=YongShenType.TONGGUAN,
                    wuxing=tongguan,
                    priority=3,
                    reason=f"{ke}與{bei_ke}對峙，取{tongguan}通關",
                )

        return None

    # ========================================
    # 綜合分析
    # ========================================

    def compute_all_yongshen(self) -> List[YongShenItem]:
        """
        計算所有用神

        按優先級返回用神列表。

        Returns:
            List[YongShenItem]: 用神列表
        """
        if self._yongshen_list is not None:
            return self._yongshen_list

        result = []

        # 1. 調候用神
        result.append(self.get_tiaohuo_yongshen())

        # 2. 格局用神
        result.append(self.get_geju_yongshen())

        # 3. 通關用神
        tongguan = self.get_tongguan_yongshen()
        if tongguan:
            result.append(tongguan)

        # 4-6. 其他用神類型（簡化版，標記為待實現）
        # 病藥、專旺、扶抑需要更複雜的判斷

        self._yongshen_list = result
        return result

    def compute_xiji(self) -> XiJiResult:
        """
        計算喜忌

        根據用神反推喜忌神。

        Returns:
            XiJiResult: 喜忌結果
        """
        if self._xiji_result is not None:
            return self._xiji_result

        yongshen_list = self.compute_all_yongshen()
        wuxing_list = ["木", "火", "土", "金", "水"]

        xi = []
        ji = []
        xian = []
        notes = []

        # 用神五行及其生者為喜
        for ys in yongshen_list:
            if ys.wuxing != "待定" and ys.wuxing not in xi:
                xi.append(ys.wuxing)
                # 生用神者也喜
                idx = wuxing_list.index(ys.wuxing)
                sheng_wuxing = wuxing_list[(idx + 4) % 5]  # 生我者
                if sheng_wuxing not in xi:
                    xi.append(sheng_wuxing)

        # 剋用神者為忌
        for ys_wuxing in xi:
            if ys_wuxing == "待定":
                continue
            idx = wuxing_list.index(ys_wuxing)
            ke_wuxing = wuxing_list[(idx + 2) % 5]  # 剋我者
            if ke_wuxing not in ji and ke_wuxing not in xi:
                ji.append(ke_wuxing)

        # 其餘為閒
        for wx in wuxing_list:
            if wx not in xi and wx not in ji:
                xian.append(wx)

        result = XiJiResult(
            xi=xi,
            ji=ji,
            xian=xian,
            notes=notes,
        )

        self._xiji_result = result
        return result

    # ========================================
    # 輸出
    # ========================================

    def to_json(self) -> Dict:
        """輸出用神分析結果"""
        return {
            "用神列表": [ys.to_dict() for ys in self.compute_all_yongshen()],
            "喜忌": self.compute_xiji().to_dict(),
            "六標籤制說明": {
                "調候": "寒暖燥濕調節，冬夏極端時優先",
                "格局": "護格助格，根據順逆用決定",
                "通關": "化解對峙，兩行皆強時使用",
                "病藥": "去病得藥，有病方需藥",
                "專旺": "順勢引泄，從格專旺時使用",
                "扶抑": "強弱調節，日主過旺過弱時使用",
            },
        }


# ============================================================
# CLI
# ============================================================

def main():
    import argparse
    import json

    parser = argparse.ArgumentParser(description="用神引擎 CLI")
    parser.add_argument("--year", type=str, required=True, help="年柱干支")
    parser.add_argument("--month", type=str, required=True, help="月柱干支")
    parser.add_argument("--day", type=str, required=True, help="日柱干支")
    parser.add_argument("--hour", type=str, required=True, help="時柱干支")

    args = parser.parse_args()

    bazi = BaziEngine.from_ganzhi(args.year, args.month, args.day, args.hour)
    engine = YongShenEngine(bazi)

    result = engine.to_json()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
