"""Steel AI Agent 主程序入口：套裁 → CAD 出图 → WPS 报价。"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from modules.cad_generator import CADGenerator
from modules.nesting_engine import NestingEngine2D, SteelPlateItem
from modules.pricing import (
    DEFAULT_PRICING,
    PricingConfig,
    build_quote_data,
    ensure_output_dir,
    make_timestamped_output_paths,
)
from modules.wps_exporter import WPSExporter

# 兼容旧测试 / 外部引用
STEEL_DENSITY: float = DEFAULT_PRICING.steel_density
STEEL_PRICE: float = DEFAULT_PRICING.steel_price
PROCESS_FEE_PER_SHEET: float = DEFAULT_PRICING.process_fee_per_sheet
PROFIT_RATE: float = DEFAULT_PRICING.profit_rate


def build_test_items() -> List[SteelPlateItem]:
    """构造一组测试零件（3 种规格，12mm 厚 Q235B）。"""
    return [
        SteelPlateItem(
            id="A",
            width_mm=800.0,
            length_mm=1200.0,
            thickness_mm=12.0,
            qty=4,
            material="Q235B",
        ),
        SteelPlateItem(
            id="B",
            width_mm=600.0,
            length_mm=900.0,
            thickness_mm=12.0,
            qty=5,
            material="Q235B",
        ),
        SteelPlateItem(
            id="C",
            width_mm=400.0,
            length_mm=1500.0,
            thickness_mm=12.0,
            qty=3,
            material="Q235B",
        ),
    ]


def main() -> None:
    """串联套裁、CAD 出图与 WPS 报价的一键主流程。"""
    print("=" * 56)
    print("  Steel AI Agent — 钢板套裁 / CAD / 报价 一键运行")
    print("=" * 56)

    output_dir: Path = ensure_output_dir("output")
    print(f"[1/5] 输出目录就绪: {output_dir.resolve()}")

    items: List[SteelPlateItem] = build_test_items()
    total_qty: int = sum(i.qty for i in items)
    print(f"[2/5] 测试零件: {len(items)} 种规格，共 {total_qty} 件（12mm Q235B）")

    engine: NestingEngine2D = NestingEngine2D(
        stock_width_mm=2200.0,
        stock_length_mm=6000.0,
        margin_mm=10.0,
    )
    nesting_result: Dict[str, Any] = engine.pack(items)
    print(
        f"[3/5] 套裁完成: 用板 {nesting_result['num_sheets']} 张，"
        f"利用率 {nesting_result['utilization_rate']:.2f}%"
    )

    pricing: PricingConfig = DEFAULT_PRICING
    quote_data: Dict[str, Any] = build_quote_data(
        nesting_result, items, pricing=pricing
    )
    print(
        f"[4/5] 费用核算: 重量 {quote_data['weight_ton']:.4f} 吨，"
        f"最终报价 ¥{quote_data['total_with_profit']:,.2f}"
    )

    dxf_path, docx_path = make_timestamped_output_paths(str(output_dir))
    CADGenerator.generate_nesting_dxf(nesting_result, str(dxf_path))
    print(f"      ✓ CAD 图纸: {dxf_path}")

    WPSExporter.generate_wps_report(quote_data, str(docx_path))
    print(f"      ✓ WPS 报价: {docx_path}")

    print("[5/5] 全部完成")
    print("-" * 56)
    print("运行成功！请查看 output/ 目录下的 DXF 与 DOCX 文件。")
    print("=" * 56)


if __name__ == "__main__":
    main()
