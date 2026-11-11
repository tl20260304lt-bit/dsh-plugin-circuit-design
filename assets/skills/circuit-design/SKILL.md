---
name: circuit-design
description: Hardware design workflow for schematic capture, PCB layout, BOM management, and DRC/ERC verification. Use when starting a new circuit/PCB project, checking design integrity, or preparing for fabrication. Covers KiCad workflows, BOM validation, and design review checklists.
metadata:
  short-description: 电路设计与 PCB 布局
---

# 电路设计与 PCB 布局

从原理图到 PCB 的完整硬件设计工作流。**核心原则：先冻结需求，再动手画板。**

## 工作流总览

```
S0 规格冻结 → S1 原理图 → S2 布局规划 → S3 布线 → S4 审核 → S5 制板
```

每个阶段有明确的**进入/退出条件**，不满足条件不进入下一阶段。

## S0: 规格冻结（S0-SPEC）

**必须完成**：一份机器可验证的规格书，包含：

| 项目 | 必填 |
|------|------|
| 核心芯片型号、封装 | ✅ |
| PCB 层数、尺寸 | ✅ |
| 电源轨清单（电压/电流） | ✅ |
| 关键接口（USB/Ethernet/DDR） | ✅ |
| 制板厂能力约束 | ✅ |

**不要做的事**：
- 不要在没有规格书的情况下开始画原理图
- 不要边画边改需求
- 不要把口头约定当作规格

## S1: 原理图设计

### 检查清单

- [ ] 所有网络命名一致（不出现 `Net-(U1$Pad1)` 这种默认名）
- [ ] 电源网络使用 Power Port，不直接用导线
- [ ] 未连接引脚明确标记 `Not Connected` 或 `Excluded`
- [ ] ERC（电气规则检查）**零错误**
- [ ] 每个 Sheet 有清晰的标题和端口定义

### BOM 验证

```bash
python "<skill>/scripts/bom_check.py" --bom bom.csv
```

## S2: 布局规划

**先规划，再放置**。布局计划包括：

1. **分区图**：功能模块划分
2. **连接器定位**：接口位置先定，锁死
3. **核心芯片放置**：围绕核心芯片布局
4. **电源树**：DC-DC → LDO → 去耦电容，按电流路径排列

### 布局规则

| 规则 | 要求 |
|------|------|
| 高速信号 | 尽量短，避免过孔 |
| 电源去耦 | 电容紧贴芯片引脚 |
| 热设计 | 大功率器件分散，靠近板边 |
| 安规 | 高压/低压区域隔离 |

## S3: 布线

### 先布关键网络

1. **时钟**：等长、包地、避免跨分割
2. **DDR/高速差分**：按长度匹配组布线
3. **电源**：宽铜皮，多层并联
4. **模拟信号**：远离数字噪声源

### 布线后检查

- [ ] DRC（设计规则检查）**零错误**
- [ ] 所有网络连通（不出现未连接警告）
- [ ] 电源/地铜皮完整，无孤立岛屿

## S4: 设计审核

### 三级审核

| 级别 | 内容 |
|------|------|
| 自审 | 设计者对照规格书逐条检查 |
| 交叉审核 | 另一位工程师独立检查 |
| 独立评审 | 不参与设计的高级工程师终审 |

### 审核重点

- **电源完整性**：去耦电容是否足够，铜皮分割是否合理
- **信号完整性**：阻抗控制、等长、差分对
- **热设计**：温升是否在安全范围内
- **安规**：爬电距离、电气间隙

## S5: 制板准备

### Gerber 导出检查

- [ ] 层数正确（Top/Bottom + 内电层 + 信号层）
- [ ] 钻孔文件完整（NPT + PT）
- [ ] 丝印清晰，极性标记正确
- [ ] 测试点覆盖关键网络

### 文件清单

| 文件 | 用途 |
|------|------|
| Gerber (RS-274X) | 板厂生产 |
| 钻孔文件 (EXCEL) | CNC 钻孔 |
| BOM CSV | 采购买料 |
| 坐标文件 | SMT 贴片 |
| 3D 模型 | 结构装配检查 |

## 约束与注意

- **KiCad 版本**：建议使用 6.x 或 7.x，文件格式不向前兼容
- ** Footprint 库**：优先使用官方库，自定义 footprint 需 3D 模型验证
- **BOM 格式**：CSV  UTF-8 编码，无 BOM 头
- **DRC 规则**：根据板厂能力设置，不要盲目追求最小线宽

## 参考

- `references/design-checklist.md` — 完整设计检查清单
- `references/gerber-checklist.md` — Gerber 导出检查项