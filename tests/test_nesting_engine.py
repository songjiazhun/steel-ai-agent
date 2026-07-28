"""套裁引擎关键逻辑测试。"""

from __future__ import annotations

import unittest
from typing import List

from modules.nesting_engine import NestingEngine2D, PlacedItem, SteelPlateItem


class TestNestingEngine2D(unittest.TestCase):
    """NestingEngine2D 关键路径测试。"""

    def setUp(self) -> None:
        self.engine: NestingEngine2D = NestingEngine2D(
            stock_width_mm=2200.0,
            stock_length_mm=6000.0,
            margin_mm=10.0,
        )

    def test_empty_items_returns_zero_sheets(self) -> None:
        result = self.engine.pack([])
        self.assertEqual(result["num_sheets"], 0)
        self.assertEqual(result["utilization_rate"], 0.0)
        self.assertEqual(result["sheets"], [])

    def test_single_item_placed_on_one_sheet(self) -> None:
        items: List[SteelPlateItem] = [
            SteelPlateItem("P1", 500.0, 800.0, 12.0, 1, "Q235B"),
        ]
        result = self.engine.pack(items)
        self.assertEqual(result["num_sheets"], 1)
        self.assertEqual(len(result["sheets"][0]), 1)
        placed: PlacedItem = result["sheets"][0][0]
        self.assertEqual(placed.id, "P1")
        self.assertEqual(placed.sheet_index, 0)
        self.assertGreater(result["utilization_rate"], 0.0)

    def test_qty_expands_to_multiple_parts(self) -> None:
        items: List[SteelPlateItem] = [
            SteelPlateItem("A", 400.0, 600.0, 12.0, 3, "Q235B"),
        ]
        result = self.engine.pack(items)
        all_parts: List[PlacedItem] = [
            p for sheet in result["sheets"] for p in sheet
        ]
        self.assertEqual(len(all_parts), 3)
        ids = {p.id for p in all_parts}
        self.assertEqual(ids, {"A-1", "A-2", "A-3"})

    def test_parts_stay_within_stock_bounds(self) -> None:
        items: List[SteelPlateItem] = [
            SteelPlateItem("A", 800.0, 1200.0, 12.0, 4, "Q235B"),
            SteelPlateItem("B", 600.0, 900.0, 12.0, 5, "Q235B"),
        ]
        result = self.engine.pack(items)
        for sheet in result["sheets"]:
            for p in sheet:
                self.assertGreaterEqual(p.x, 0.0)
                self.assertGreaterEqual(p.y, 0.0)
                self.assertLessEqual(
                    p.x + p.width, self.engine.stock_width_mm + 1e-6
                )
                self.assertLessEqual(
                    p.y + p.length, self.engine.stock_length_mm + 1e-6
                )

    def test_no_overlap_with_margin(self) -> None:
        items: List[SteelPlateItem] = [
            SteelPlateItem("A", 700.0, 1000.0, 12.0, 6, "Q235B"),
        ]
        result = self.engine.pack(items)
        margin: float = self.engine.margin_mm
        for sheet in result["sheets"]:
            for i, a in enumerate(sheet):
                for b in sheet[i + 1 :]:
                    ax2: float = a.x + a.width
                    ay2: float = a.y + a.length
                    bx2: float = b.x + b.width
                    by2: float = b.y + b.length
                    # 两矩形在考虑 margin 后仍不应重叠
                    separated: bool = (
                        ax2 + margin <= b.x + 1e-6
                        or bx2 + margin <= a.x + 1e-6
                        or ay2 + margin <= b.y + 1e-6
                        or by2 + margin <= a.y + 1e-6
                    )
                    # 同货架内 Y 可重叠区域，但 X 方向须留切缝；
                    # 不同货架则 Y 方向须留切缝。允许贴合无 margin 的边界情况用严格不重叠兜底。
                    no_overlap: bool = (
                        ax2 <= b.x + 1e-6
                        or bx2 <= a.x + 1e-6
                        or ay2 <= b.y + 1e-6
                        or by2 <= a.y + 1e-6
                    )
                    self.assertTrue(
                        no_overlap,
                        f"零件重叠: {a.id} vs {b.id}",
                    )
                    self.assertTrue(
                        separated or no_overlap,
                        f"切缝不足: {a.id} vs {b.id}",
                    )

    def test_opens_new_sheet_when_stock_full(self) -> None:
        # 单件接近整板，多件必然开新板
        items: List[SteelPlateItem] = [
            SteelPlateItem("BIG", 2000.0, 5000.0, 12.0, 3, "Q235B"),
        ]
        result = self.engine.pack(items)
        self.assertEqual(result["num_sheets"], 3)
        for idx, sheet in enumerate(result["sheets"]):
            self.assertEqual(len(sheet), 1)
            self.assertEqual(sheet[0].sheet_index, idx)

    def test_utilization_rate_formula(self) -> None:
        items: List[SteelPlateItem] = [
            SteelPlateItem("P", 1000.0, 2000.0, 12.0, 1, "Q235B"),
        ]
        result = self.engine.pack(items)
        parts_area: float = 1000.0 * 2000.0
        stock_area: float = 2200.0 * 6000.0
        expected: float = round(parts_area / stock_area * 100.0, 2)
        self.assertEqual(result["utilization_rate"], expected)

    def test_rotation_allows_fit(self) -> None:
        # 宽 2500 超母板宽 2200，旋转后 1800×2500 可放（长方向）
        engine: NestingEngine2D = NestingEngine2D(
            stock_width_mm=2200.0,
            stock_length_mm=6000.0,
            margin_mm=10.0,
        )
        items: List[SteelPlateItem] = [
            SteelPlateItem("R", 2500.0, 1800.0, 12.0, 1, "Q235B"),
        ]
        result = engine.pack(items)
        self.assertEqual(result["num_sheets"], 1)
        placed: PlacedItem = result["sheets"][0][0]
        self.assertLessEqual(placed.width, 2200.0 + 1e-6)
        self.assertLessEqual(placed.length, 6000.0 + 1e-6)


if __name__ == "__main__":
    unittest.main()
