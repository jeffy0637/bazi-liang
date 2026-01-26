# 八字命理 - 梁派 Bazi Mingli Liang

> **注意：本專案目前尚在建立中，功能與文件可能隨時變動。**

基於**梁湘潤**體系的八字命理 AI 技能。強調系統化的論命流程，以可驗證、可回溯的方式進行命理分析。

## 梁派特色

- **流程優先**：Step1 五行全不全 → Step2 刑沖合會 → Step3 拱/夾/暗拱，依序執行不跳步
- **可驗證規則**：每個結論可回溯至規則 ID，而非僅憑案例
- **不確定性標註**：逐步建立論證鏈，明確標示信心程度

## 專案結構

```
bazi-mingli-liang/
├── SKILL.md                      # 核心技能指南
├── ETHICS.md                     # 倫理準則
├── README.md                     # 本文件
├── references/
│   ├── liang-system.md           # 梁系論命流程規格
│   ├── liang-gongjia.md          # 梁派拱/夾規則
│   ├── tiangan-dizhi.md          # 天干地支基礎
│   ├── wuxing-shengke.md         # 五行生剋詳解
│   ├── shishen.md                # 十神定義與應用
│   ├── rizhu-qiangruo.md         # 日主強弱判斷
│   ├── yongshen.md               # 用神喜忌法則
│   ├── dayun-liunian.md          # 大運流年推算
│   ├── geju-fenxi.md             # 格局分析總論
│   ├── hunyin-ganqing.md         # 婚姻感情專論
│   ├── shiye-caiyun.md           # 事業財運專論
│   └── jiankang.md               # 健康疾病專論
└── scripts/
    └── bazi_calc.py              # Python 排盤工具
```

## 梁系論命流程

| 步驟 | 內容 | 說明 |
|------|------|------|
| Step 0 | 排盤校驗 | 四柱、藏干、十神、五行分布 |
| Step 1 | 五行是否全 | 含支藏，標註缺失影響 |
| Step 2 | 刑沖合會 | 描述結構，不先下吉凶 |
| Step 3 | 拱/夾/暗拱 | 檢查危險組合 |
| Step 4 | 十神定位 | 性格/行為傾向 |
| Step 5 | 格局與職業 | 能力結構分析 |
| Step 6 | 調候 | 寒暖燥濕調節 |
| Step 7 | 流年/大運 | 結構性波動 |

詳見 [liang-system.md](references/liang-system.md)

## 倫理準則

- **中立客觀**：吉凶並陳，不迎合期望
- **責任界限**：僅供參考，不替代專業諮詢
- **語言規範**：使用「可能」「傾向」等非絕對用語
- **尊重隱私**：未經同意不分析他人命盤

詳見 [ETHICS.md](ETHICS.md)
