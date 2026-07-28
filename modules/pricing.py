"""钢材计价与报价数据组装。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from modules.nesting_engine import SteelPlateItem


@dataclass
class PricingConfig:
    """报价计价参数。"""

    steel_density: float = 7.85  # 吨/m³
    steel_price: float = 4200.0  # 元/吨
    process_fee_per_sheet: float = 350.0  # 元/张
    profit_rate: float = 0.12  # 目标利润率


DEFAULT_PRICING: PricingConfig = PricingConfig()


def ensure_output_dir(output_dir: str = "output") -> Path:
    """自动创建输出目录并返回路径。"""
    path: Path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def make_timestamped_output_paths(
    output_dir: str = "output",
    when: Optional[datetime] = None,
) -> Tuple[Path, Path]:
    """生成带时间后缀的 DXF / DOCX 输出路径。

    文件名示例：
      钢板套裁排版图_20260728_213000.dxf
      钢板套裁报价单_20260728_213000.docx
    """
    stamp: str = (when or datetime.now()).strftime("%Y%m%d_%H%M%S")
    base: Path = ensure_output_dir(output_dir)
    dxf_path: Path = base / f"钢板套裁排版图_{stamp}.dxf"
    docx_path: Path = base / f"钢板套裁报价单_{stamp}.docx"
    return dxf_path, docx_path


def calc_total_weight_ton(
    items: List[SteelPlateItem],
    density: float = DEFAULT_PRICING.steel_density,
) -> float:
    """按钢材密度计算零件总重量（吨）。"""
    volume_m3: float = 0.0
    for item in items:
        volume_m3 += (
            (item.width_mm / 1000.0)
            * (item.length_mm / 1000.0)
            * (item.thickness_mm / 1000.0)
            * item.qty
        )
    return volume_m3 * density


def build_quote_data(
    nesting_result: Dict[str, Any],
    items: List[SteelPlateItem],
    pricing: PricingConfig = DEFAULT_PRICING,
) -> Dict[str, Any]:
    """根据套裁结果与零件列表计算费用并组装报价数据。"""
    weight_ton: float = calc_total_weight_ton(items, pricing.steel_density)
    material_cost: float = weight_ton * pricing.steel_price
    num_sheets: int = int(nesting_result["num_sheets"])
    process_cost: float = num_sheets * pricing.process_fee_per_sheet
    subtotal: float = material_cost + process_cost
    total_with_profit: float = round(subtotal * (1.0 + pricing.profit_rate), 2)

    table_rows: List[List[str]] = []
    for item in items:
        part_vol: float = (
            (item.width_mm / 1000.0)
            * (item.length_mm / 1000.0)
            * (item.thickness_mm / 1000.0)
            * item.qty
        )
        part_weight: float = part_vol * pricing.steel_density
        part_cost: float = part_weight * pricing.steel_price
        table_rows.append(
            [
                f"钢板 {item.id}",
                f"{item.width_mm:.0f}×{item.length_mm:.0f}×{item.thickness_mm:.0f} "
                f"{item.material}",
                f"{item.qty} 件",
                f"{pricing.steel_price:.0f}/吨",
                f"{part_cost:,.2f}",
            ]
        )

    table_rows.append(
        [
            "加工费",
            f"激光/等离子切割 × {num_sheets} 张",
            f"{num_sheets} 张",
            f"{pricing.process_fee_per_sheet:.0f}/张",
            f"{process_cost:,.2f}",
        ]
    )
    table_rows.append(
        [
            "目标利润",
            f"{pricing.profit_rate * 100:.0f}%",
            "—",
            "—",
            f"{subtotal * pricing.profit_rate:,.2f}",
        ]
    )

    return {
        "stock_width_mm": nesting_result["stock_width_mm"],
        "stock_length_mm": nesting_result["stock_length_mm"],
        "num_sheets": num_sheets,
        "utilization_rate": nesting_result["utilization_rate"],
        "weight_ton": round(weight_ton, 4),
        "material_cost": round(material_cost, 2),
        "process_cost": round(process_cost, 2),
        "profit_rate": pricing.profit_rate,
        "total_with_profit": total_with_profit,
        "table_rows": table_rows,
    }
