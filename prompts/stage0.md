# Stage 0: 原局特徵表

## 概述

Stage 0 是開局掃描，建立原局的完整特徵表，為後續十項主流程提供基礎數據。

## 輸入

```json
{
  "birth_data": {
    "year": 1990,
    "month": 8,
    "day": 15,
    "hour": 14
  },
  "gender": "男"
}
```

或干支輸入：

```json
{
  "bazi": {
    "year_pillar": "己丑",
    "month_pillar": "己巳",
    "day_pillar": "甲子",
    "hour_pillar": "辛未"
  },
  "gender": "男"
}
```

## 執行步驟

### 1. 四柱排盤

調用 `bazi_engine` 取得四柱：

```python
from scripts.bazi_engine import BaziEngine

# 從西曆
bazi = BaziEngine.from_datetime(1990, 8, 15, 14)

# 或從干支
bazi = BaziEngine.from_ganzhi("己丑", "己巳", "甲子", "辛未")
```

### 2. 藏干計算

自動由 `bazi_engine` 計算：

```python
hidden = bazi.compute_hidden_stems()
```

藏干結構：
- 本氣：權重 1.0
- 中氣：權重 0.5
- 餘氣：權重 0.3

### 3. 十神計算

以日主為基準：

```python
shishen = bazi.compute_shishen()
summary = bazi.get_shishen_summary()
```

注意：日主自身標記為「日主」而非「比肩」。

### 4. 旬空計算

以日柱推算：

```python
xunkong = bazi.compute_xunkong()
```

旬空表：
| 旬首 | 空亡 |
|------|------|
| 甲子 | 戌亥 |
| 甲戌 | 申酉 |
| 甲申 | 午未 |
| 甲午 | 辰巳 |
| 甲辰 | 寅卯 |
| 甲寅 | 子丑 |

### 5. 月令主格

調用 `geju_engine`：

```python
from scripts.geju_engine import GejuEngine

geju = GejuEngine(bazi)
zhuge = geju.get_yueling_zhuge()
```

月令主格 = 月支本氣對日主的十神。

## 輸出格式

```json
{
  "stage0": {
    "meta": {
      "engine_version": "1.0",
      "timestamp": "2026-01-26T12:00:00Z"
    },
    "input": {
      "birth_data": {...},
      "gender": "男"
    },
    "四柱": {
      "年柱": {
        "ganzhi": "己丑",
        "gan": "己",
        "zhi": "丑",
        "gan_wuxing": "土",
        "gan_yinyang": "陰",
        "zhi_wuxing": "土",
        "zhi_yinyang": "陰"
      },
      "月柱": {...},
      "日柱": {...},
      "時柱": {...}
    },
    "日主": "甲",
    "藏干": {
      "年支": [
        {"zhi": "丑", "stem": "己", "role": "本氣", "weight": 1.0, "wuxing": "土"},
        {"zhi": "丑", "stem": "癸", "role": "中氣", "weight": 0.5, "wuxing": "水"},
        {"zhi": "丑", "stem": "辛", "role": "餘氣", "weight": 0.3, "wuxing": "金"}
      ],
      "月支": [...],
      "日支": [...],
      "時支": [...]
    },
    "十神": {
      "items": [
        {"position": "年", "layer": "天干", "char": "己", "shishen": "正財", "weight": 1.0},
        ...
      ],
      "summary": {
        "by_position": {...},
        "by_shishen": {...},
        "counts": {"正財": 4, "正官": 2, ...},
        "weighted_counts": {"正財": 4.0, "正官": 1.3, ...}
      }
    },
    "旬空": {
      "day_pillar": "甲子",
      "xun_shou": "甲子",
      "kong_zhi": ["戌", "亥"],
      "kong_positions": [],
      "kong_shishen": []
    },
    "月令主格": {
      "月支": "巳",
      "本氣": "丙",
      "本氣十神": "食神",
      "主格": "食神格",
      "中氣": "戊",
      "餘氣": "庚",
      "透干": false,
      "透干位置": []
    },
    "待查清單": []
  }
}
```

## 待查項目

以下情況需標記到「待查清單」：

1. **時辰不確定**：輸入的時辰有疑義
2. **閏月處理**：農曆閏月的處理方式
3. **夜子時**：23:00-24:00 的日柱歸屬

## 驗證要點

- [ ] 四柱計算正確（對照萬年曆）
- [ ] 藏干與標準表一致
- [ ] 十神以日主為基準計算
- [ ] 旬空以日柱推算
- [ ] 月令主格取月支本氣
