# Steel AI Agent 开发任务清单 (TASK.md)

本项目旨在实现钢材行业的 **AI CAD画图 + 2D排版套裁 + WPS报价单自动生成** 的全流程自动化。

---

## 📋 Step 1: 项目基础结构初始化

**目标：** 初始化项目目录与依赖配置文件。

**给 Cursor 的提示词：**
> 请帮我初始化项目结构和依赖配置文件：
> 1. 创建目录结构：`modules/` 和 `output/`。
> 2. 创建 `requirements.txt`，包含：
>    - `ezdxf>=1.1.0`
>    - `python-docx>=0.8.11`
>    - `openpyxl>=3.1.0`
> 3. 创建 `README.md` 说明项目基本功能。

---

## 🧩 Step 2: 2D 钢板套裁排版引擎开发

**目标：** 在 `modules/nesting_engine.py` 中实现 2D 矩形件 Shelf/Bin-Packing 套裁算法。

**给 Cursor 的提示词：**
> 请在 `modules/nesting_engine.py` 中编写 2D 钢板排版套裁引擎。
>
> 需求细节：
> 1. 使用 `@dataclass` 定义输入类 `SteelPlateItem` (id, width_mm, length_mm, thickness_mm, qty, material)。
> 2. 使用 `@dataclass` 定义输出类 `PlacedItem` (id, x, y, width, length, sheet_index, thickness_mm, material)。
> 3. 实现 `NestingEngine2D` 类：
>    - 构造参数支持标准母板尺寸（默认 `2200.0`mm x `6000.0`mm）与切缝边距 `margin_mm`（默认 `10.0`mm）。
>    - 实现 `pack(items: List[SteelPlateItem]) -> Dict[str, Any]` 方法。
>    - 排版逻辑：包含长短边适配判断、货架换行与开启新母板逻辑。
>    - 返回字典包含：`num_sheets` (用板张数)、`utilization_rate` (综合套裁利用率 %)、`sheets` (分板的已排零件列表)。
> 4. 添加完整 Type Hints 类型声明和函数注释。

---

## 🎨 Step 3: CAD 图纸绘制模块开发

**目标：** 在 `modules/cad_generator.py` 中使用 `ezdxf` 绘制包含多图层与标注的矢量 DXF 图纸。

**给 Cursor 的提示词：**
> 请参考 `@modules/nesting_engine.py` 的数据结构，在 `modules/cad_generator.py` 中编写 CAD 图纸生成器。
>
> 需求细节：
> 1. 创建类 `CADGenerator`，包含静态方法 `generate_nesting_dxf(nesting_data: dict, output_path: str)`。
> 2. 使用 `ezdxf.new(dxfversion="AC1027")` 新建 AutoCAD 2013 兼容格式图纸。
> 3. 创建专用图层：
>    - `0_STOCK_BORDER`（颜色 1 红色，母板外框）
>    - `0_PARTS`（颜色 3 绿色，零件边框）
>    - `0_TEXT`（颜色 2 黄色，文字标注）
> 4. 遍历多张母板排版结果：沿 Y 轴平移绘制每张大板，并在每张板内部按 (x, y) 绘制每个零件及其 ID 和规格文本。

---

## 📄 Step 4: WPS 商务报价单导出模块开发

**目标：** 在 `modules/wps_exporter.py` 中使用 `python-docx` 生成能用 WPS Office 完美打开的报价单。

**给 Cursor 的提示词：**
> 请参考 `@modules/nesting_engine.py` 的输出，在 `modules/wps_exporter.py` 中编写 WPS 报价单导出模块。
>
> 需求细节：
> 1. 创建类 `WPSExporter`，包含静态方法 `generate_wps_report(quote_data: dict, output_path: str)`。
> 2. 排版样式：
>    - 页边距设为 0.8 英寸。
>    - 居中主标题：“钢材套裁排版与智能化报价单”（字号 20pt、深蓝色 `0F4C81`）。
>    - 一、排版分析段落（列出母板规格、用板张数、利用率高亮显示）。
>    - 二、结算明细表格：创建 5 列表格，使用 XML 函数设置表头单元格背景色为 `0F4C81`，文字加粗变白。
>    - 结尾右对齐输出最终含税与利润的总报价（红字加粗）。

---

## 🚀 Step 5: 主流程整合与自动化测试

**目标：** 在 `main.py` 中串联所有模块，实现一键运行出图和出单。

**给 Cursor 的提示词：**
> 请读取 `@modules/` 目录下的所有模块，编写 `main.py` 主程序入口。
>
> 需求细节：
> 1. 自动创建 `output/` 文件夹。
> 2. 构造一组测试零件数据（3 种不同规格的 12mm 厚 Q235B 钢板）。
> 3. 调用 `NestingEngine2D` 进行套裁计算。
> 4. 计算费用：
>    - 钢材密度按 `7.85` 吨/m³ 计算材料总重量和材料费（钢价 `4200` 元/吨）。
>    - 加工费按 `350` 元/张计算。
>    - 加上 `12%` 目标利润。
> 5. 调用 `CADGenerator` 生成 `output/钢板套裁排版图.dxf`。
> 6. 调用 `WPSExporter` 生成 `output/钢板套裁报价单.docx`。
> 7. 在终端打印清晰的运行成功日志。

---

## ✅ 验收与调试检查清单

- [ ] 在终端运行 `python main.py` 无任何报错。
- [ ] `output/` 目录下生成 `钢板套裁排版图.dxf` 且可以用 CAD 软件查看。
- [ ] `output/` 目录下生成 `钢板套裁报价单.docx` 且可以用 WPS 打开，样式与表格无错乱。