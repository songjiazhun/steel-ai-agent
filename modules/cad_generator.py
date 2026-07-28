"""CAD / DXF 套裁图纸生成模块。"""

from __future__ import annotations

from typing import Any, Dict, List

import ezdxf
from ezdxf.document import Drawing
from ezdxf.layouts import Modelspace

from modules.nesting_engine import PlacedItem


class CADGenerator:
    """基于 ezdxf 的套裁排版 DXF 图纸生成器。"""

    LAYER_STOCK: str = "0_STOCK_BORDER"
    LAYER_PARTS: str = "0_PARTS"
    LAYER_TEXT: str = "0_TEXT"

    @staticmethod
    def generate_nesting_dxf(nesting_data: dict, output_path: str) -> None:
        """根据套裁结果生成多图层 DXF 图纸。

        Args:
            nesting_data: NestingEngine2D.pack() 返回的排版结果字典。
            output_path: DXF 文件输出路径。
        """
        doc: Drawing = ezdxf.new(dxfversion="AC1027")
        CADGenerator._setup_layers(doc)
        msp: Modelspace = doc.modelspace()

        stock_w: float = float(nesting_data.get("stock_width_mm", 2200.0))
        stock_l: float = float(nesting_data.get("stock_length_mm", 6000.0))
        sheets: List[List[PlacedItem]] = nesting_data.get("sheets", [])
        gap_between_sheets: float = 500.0

        for sheet_idx, placed_list in enumerate(sheets):
            # 沿 Y 轴平移绘制每张母板
            offset_y: float = sheet_idx * (stock_l + gap_between_sheets)

            # 母板外框
            msp.add_lwpolyline(
                [
                    (0.0, offset_y),
                    (stock_w, offset_y),
                    (stock_w, offset_y + stock_l),
                    (0.0, offset_y + stock_l),
                ],
                close=True,
                dxfattribs={"layer": CADGenerator.LAYER_STOCK},
            )

            # 母板标题
            msp.add_text(
                f"Sheet #{sheet_idx + 1}  {stock_w:.0f}x{stock_l:.0f} mm",
                dxfattribs={
                    "layer": CADGenerator.LAYER_TEXT,
                    "height": 80.0,
                    "insert": (0.0, offset_y + stock_l + 50.0),
                },
            )

            for part in placed_list:
                CADGenerator._draw_part(msp, part, offset_y)

        doc.saveas(output_path)

    @staticmethod
    def _setup_layers(doc: Drawing) -> None:
        """创建专用图层并设置颜色。"""
        doc.layers.add(CADGenerator.LAYER_STOCK, color=1)  # 红色
        doc.layers.add(CADGenerator.LAYER_PARTS, color=3)  # 绿色
        doc.layers.add(CADGenerator.LAYER_TEXT, color=2)  # 黄色

    @staticmethod
    def _draw_part(msp: Modelspace, part: PlacedItem, offset_y: float) -> None:
        """在模型空间绘制单个零件边框与标注。"""
        x: float = part.x
        y: float = part.y + offset_y
        w: float = part.width
        l: float = part.length

        msp.add_lwpolyline(
            [
                (x, y),
                (x + w, y),
                (x + w, y + l),
                (x, y + l),
            ],
            close=True,
            dxfattribs={"layer": CADGenerator.LAYER_PARTS},
        )

        label: str = f"{part.id}\n{w:.0f}x{l:.0f}"
        text_height: float = min(40.0, max(12.0, min(w, l) * 0.08))
        msp.add_text(
            label,
            dxfattribs={
                "layer": CADGenerator.LAYER_TEXT,
                "height": text_height,
                "insert": (x + w * 0.05, y + l * 0.4),
            },
        )
