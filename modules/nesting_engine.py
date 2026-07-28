"""2D 钢板套裁排版引擎（Shelf / Bin-Packing）。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple


@dataclass
class SteelPlateItem:
    """待排版钢板零件输入。"""

    id: str
    width_mm: float
    length_mm: float
    thickness_mm: float
    qty: int
    material: str


@dataclass
class PlacedItem:
    """已放置在母板上的零件输出。"""

    id: str
    x: float
    y: float
    width: float
    length: float
    sheet_index: int
    thickness_mm: float
    material: str


@dataclass
class _Shelf:
    """当前母板上的一个货架行。"""

    y: float
    height: float
    x_cursor: float = 0.0
    items: List[PlacedItem] = field(default_factory=list)


class NestingEngine2D:
    """2D 矩形件 Shelf/Bin-Packing 套裁引擎。

    支持长短边旋转适配、货架换行与开启新母板。
    """

    def __init__(
        self,
        stock_width_mm: float = 2200.0,
        stock_length_mm: float = 6000.0,
        margin_mm: float = 10.0,
    ) -> None:
        """初始化套裁引擎。

        Args:
            stock_width_mm: 标准母板宽度（mm），默认 2200。
            stock_length_mm: 标准母板长度（mm），默认 6000。
            margin_mm: 零件间切缝边距（mm），默认 10。
        """
        self.stock_width_mm: float = stock_width_mm
        self.stock_length_mm: float = stock_length_mm
        self.margin_mm: float = margin_mm

    def pack(self, items: List[SteelPlateItem]) -> Dict[str, Any]:
        """对零件列表执行 2D 套裁排版。

        Args:
            items: 待排版零件列表。

        Returns:
            包含 num_sheets、utilization_rate、sheets 的结果字典。
        """
        expanded: List[Tuple[str, float, float, float, str]] = []
        for item in items:
            for i in range(item.qty):
                part_id: str = f"{item.id}-{i + 1}" if item.qty > 1 else item.id
                expanded.append(
                    (
                        part_id,
                        item.width_mm,
                        item.length_mm,
                        item.thickness_mm,
                        item.material,
                    )
                )

        # 按面积从大到小排序，提高货架利用率
        expanded.sort(key=lambda p: p[1] * p[2], reverse=True)

        sheets: List[List[PlacedItem]] = []
        current_shelves: List[_Shelf] = []
        sheet_y_used: float = 0.0

        def open_new_sheet() -> None:
            nonlocal current_shelves, sheet_y_used
            sheets.append([])
            current_shelves = []
            sheet_y_used = 0.0

        if expanded:
            open_new_sheet()

        for part_id, w, l, thickness, material in expanded:
            placed: bool = False
            orientations: List[Tuple[float, float]] = self._orientations(w, l)

            # 优先尝试放入已有货架
            for shelf in current_shelves:
                for ow, ol in orientations:
                    if self._fits_on_shelf(shelf, ow, ol):
                        placed_item: PlacedItem = PlacedItem(
                            id=part_id,
                            x=shelf.x_cursor,
                            y=shelf.y,
                            width=ow,
                            length=ol,
                            sheet_index=len(sheets) - 1,
                            thickness_mm=thickness,
                            material=material,
                        )
                        shelf.items.append(placed_item)
                        sheets[-1].append(placed_item)
                        shelf.x_cursor += ow + self.margin_mm
                        placed = True
                        break
                if placed:
                    break

            if placed:
                continue

            # 尝试在当前母板开启新货架
            for ow, ol in orientations:
                if self._can_open_shelf(sheet_y_used, ol):
                    shelf_y: float = (
                        0.0
                        if not current_shelves
                        else sheet_y_used + self.margin_mm
                    )
                    new_shelf: _Shelf = _Shelf(y=shelf_y, height=ol, x_cursor=0.0)
                    placed_item = PlacedItem(
                        id=part_id,
                        x=0.0,
                        y=shelf_y,
                        width=ow,
                        length=ol,
                        sheet_index=len(sheets) - 1,
                        thickness_mm=thickness,
                        material=material,
                    )
                    new_shelf.items.append(placed_item)
                    new_shelf.x_cursor = ow + self.margin_mm
                    current_shelves.append(new_shelf)
                    sheets[-1].append(placed_item)
                    sheet_y_used = shelf_y + ol
                    placed = True
                    break

            if placed:
                continue

            # 开启新母板
            open_new_sheet()
            ow, ol = self._best_orientation_for_new_sheet(w, l)
            new_shelf = _Shelf(y=0.0, height=ol, x_cursor=0.0)
            placed_item = PlacedItem(
                id=part_id,
                x=0.0,
                y=0.0,
                width=ow,
                length=ol,
                sheet_index=len(sheets) - 1,
                thickness_mm=thickness,
                material=material,
            )
            new_shelf.items.append(placed_item)
            new_shelf.x_cursor = ow + self.margin_mm
            current_shelves.append(new_shelf)
            sheets[-1].append(placed_item)
            sheet_y_used = ol

        num_sheets: int = len(sheets)
        parts_area: float = sum(
            p.width * p.length for sheet in sheets for p in sheet
        )
        stock_area: float = (
            self.stock_width_mm * self.stock_length_mm * num_sheets
            if num_sheets > 0
            else 0.0
        )
        utilization_rate: float = (
            round(parts_area / stock_area * 100.0, 2) if stock_area > 0 else 0.0
        )

        return {
            "num_sheets": num_sheets,
            "utilization_rate": utilization_rate,
            "sheets": sheets,
            "stock_width_mm": self.stock_width_mm,
            "stock_length_mm": self.stock_length_mm,
            "margin_mm": self.margin_mm,
        }

    def _orientations(
        self, width: float, length: float
    ) -> List[Tuple[float, float]]:
        """返回可行的长短边方向（宽×长，对应母板宽×长方向）。

        母板坐标系：X 轴沿 stock_width，Y 轴沿 stock_length。
        """
        opts: List[Tuple[float, float]] = [(width, length)]
        if abs(width - length) > 1e-6:
            opts.append((length, width))
        # 优先选择能贴合母板宽度的方向
        opts.sort(
            key=lambda o: (
                0 if o[0] <= self.stock_width_mm else 1,
                0 if o[1] <= self.stock_length_mm else 1,
                -o[0] * o[1],
            )
        )
        return opts

    def _fits_on_shelf(
        self, shelf: _Shelf, part_w: float, part_l: float
    ) -> bool:
        """判断零件是否可放入指定货架（高度需完全容纳）。"""
        if part_l > shelf.height + 1e-6:
            return False
        if part_w > self.stock_width_mm + 1e-6:
            return False
        remaining_x: float = self.stock_width_mm - shelf.x_cursor
        return part_w <= remaining_x + 1e-6

    def _can_open_shelf(self, sheet_y_used: float, part_l: float) -> bool:
        """判断当前母板剩余长度是否足够开启新货架。"""
        if part_l > self.stock_length_mm + 1e-6:
            return False
        gap: float = 0.0 if sheet_y_used <= 0 else self.margin_mm
        return sheet_y_used + gap + part_l <= self.stock_length_mm + 1e-6

    def _best_orientation_for_new_sheet(
        self, width: float, length: float
    ) -> Tuple[float, float]:
        """为新母板选择能放入的最佳方向。"""
        for ow, ol in self._orientations(width, length):
            if ow <= self.stock_width_mm + 1e-6 and ol <= self.stock_length_mm + 1e-6:
                return ow, ol
        # 无法放入时仍返回原始方向（调用方需保证零件不超母板）
        return width, length
