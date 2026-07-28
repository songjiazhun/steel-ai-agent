"""Steel AI Agent — Streamlit 网页工作台。"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st

from modules.auth import require_demo_login
from modules.cad_generator import CADGenerator
from modules.nesting_engine import NestingEngine2D, SteelPlateItem
from modules.preview import draw_nesting_preview
from modules.pricing import PricingConfig, build_quote_data, make_timestamped_output_paths
from modules.wps_exporter import WPSExporter

DEFAULT_PARTS: List[Dict[str, Any]] = [
    {
        "id": "A",
        "width_mm": 800.0,
        "length_mm": 1200.0,
        "thickness_mm": 12.0,
        "qty": 4,
        "material": "Q235B",
    },
    {
        "id": "B",
        "width_mm": 600.0,
        "length_mm": 900.0,
        "thickness_mm": 12.0,
        "qty": 5,
        "material": "Q235B",
    },
    {
        "id": "C",
        "width_mm": 400.0,
        "length_mm": 1500.0,
        "thickness_mm": 12.0,
        "qty": 3,
        "material": "Q235B",
    },
]


def _dataframe_to_items(df: pd.DataFrame) -> List[SteelPlateItem]:
    """将编辑表格转为 SteelPlateItem 列表。"""
    items: List[SteelPlateItem] = []
    for _, row in df.iterrows():
        part_id: str = str(row.get("id", "")).strip()
        if not part_id:
            continue
        qty: int = int(row["qty"])
        if qty <= 0:
            continue
        width: float = float(row["width_mm"])
        length: float = float(row["length_mm"])
        thickness: float = float(row["thickness_mm"])
        if width <= 0 or length <= 0 or thickness <= 0:
            continue
        items.append(
            SteelPlateItem(
                id=part_id,
                width_mm=width,
                length_mm=length,
                thickness_mm=thickness,
                qty=qty,
                material=str(row.get("material", "Q235B")).strip() or "Q235B",
            )
        )
    return items


def _run_pipeline(
    items: List[SteelPlateItem],
    stock_width_mm: float,
    stock_length_mm: float,
    margin_mm: float,
    pricing: PricingConfig,
) -> Dict[str, Any]:
    """执行套裁 → 报价 → 导出文件。"""
    engine: NestingEngine2D = NestingEngine2D(
        stock_width_mm=stock_width_mm,
        stock_length_mm=stock_length_mm,
        margin_mm=margin_mm,
    )
    nesting_result: Dict[str, Any] = engine.pack(items)
    quote_data: Dict[str, Any] = build_quote_data(
        nesting_result, items, pricing=pricing
    )

    output_dir_paths = make_timestamped_output_paths("output")
    dxf_path: Path = output_dir_paths[0]
    docx_path: Path = output_dir_paths[1]
    CADGenerator.generate_nesting_dxf(nesting_result, str(dxf_path))
    WPSExporter.generate_wps_report(quote_data, str(docx_path))

    return {
        "nesting": nesting_result,
        "quote": quote_data,
        "dxf_path": dxf_path,
        "docx_path": docx_path,
    }


def main() -> None:
    """Streamlit 页面入口。"""
    st.set_page_config(
        page_title="Steel AI Agent",
        page_icon="🧱",
        layout="wide",
    )
    if not require_demo_login():
        return

    st.title("Steel AI Agent")
    st.caption("钢板 2D 套裁 · CAD 出图 · WPS 报价 · 客户演示版")

    with st.sidebar:
        st.header("母板与切缝")
        stock_width_mm: float = st.number_input(
            "母板宽度 (mm)", min_value=100.0, value=2200.0, step=100.0
        )
        stock_length_mm: float = st.number_input(
            "母板长度 (mm)", min_value=100.0, value=6000.0, step=100.0
        )
        margin_mm: float = st.number_input(
            "切缝边距 (mm)", min_value=0.0, value=10.0, step=1.0
        )

        st.header("计价参数")
        steel_price: float = st.number_input(
            "钢价 (元/吨)", min_value=0.0, value=4200.0, step=50.0
        )
        process_fee: float = st.number_input(
            "加工费 (元/张)", min_value=0.0, value=350.0, step=10.0
        )
        profit_pct: float = st.number_input(
            "目标利润 (%)", min_value=0.0, value=12.0, step=1.0
        )
        steel_density: float = st.number_input(
            "钢材密度 (吨/m³)", min_value=0.1, value=7.85, step=0.01, format="%.2f"
        )

    st.subheader("零件清单")
    st.caption("可直接编辑表格：增删行、修改规格与数量。")
    if "parts_df" not in st.session_state:
        st.session_state.parts_df = pd.DataFrame(DEFAULT_PARTS)

    edited_df: pd.DataFrame = st.data_editor(
        st.session_state.parts_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "id": st.column_config.TextColumn("零件编号", required=True),
            "width_mm": st.column_config.NumberColumn(
                "宽度 mm", min_value=1.0, step=10.0, format="%.1f"
            ),
            "length_mm": st.column_config.NumberColumn(
                "长度 mm", min_value=1.0, step=10.0, format="%.1f"
            ),
            "thickness_mm": st.column_config.NumberColumn(
                "厚度 mm", min_value=0.1, step=1.0, format="%.1f"
            ),
            "qty": st.column_config.NumberColumn(
                "数量", min_value=1, step=1, format="%d"
            ),
            "material": st.column_config.TextColumn("材质"),
        },
        key="parts_editor",
    )
    st.session_state.parts_df = edited_df

    run_clicked: bool = st.button("开始套裁并生成报价", type="primary")

    if run_clicked:
        items: List[SteelPlateItem] = _dataframe_to_items(edited_df)
        if not items:
            st.error("请至少填写一行有效零件（编号、尺寸、数量均需大于 0）。")
            return

        pricing: PricingConfig = PricingConfig(
            steel_density=steel_density,
            steel_price=steel_price,
            process_fee_per_sheet=process_fee,
            profit_rate=profit_pct / 100.0,
        )
        with st.spinner("正在套裁、出图与生成报价单…"):
            try:
                result: Dict[str, Any] = _run_pipeline(
                    items=items,
                    stock_width_mm=stock_width_mm,
                    stock_length_mm=stock_length_mm,
                    margin_mm=margin_mm,
                    pricing=pricing,
                )
                st.session_state.last_result = result
            except Exception as exc:  # noqa: BLE001
                st.error(f"运行失败：{exc}")
                return

    result_data: Optional[Dict[str, Any]] = st.session_state.get("last_result")
    if not result_data:
        st.info("填写零件与参数后，点击上方按钮开始计算。")
        return

    nesting: Dict[str, Any] = result_data["nesting"]
    quote: Dict[str, Any] = result_data["quote"]
    dxf_path: Path = result_data["dxf_path"]
    docx_path: Path = result_data["docx_path"]

    st.success("套裁完成")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("用板张数", f"{quote['num_sheets']} 张")
    m2.metric("利用率", f"{quote['utilization_rate']:.2f}%")
    m3.metric("总重量", f"{quote['weight_ton']:.4f} 吨")
    m4.metric("最终报价", f"¥{quote['total_with_profit']:,.2f}")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**费用明细**")
        st.write(
            f"- 材料费：¥{quote['material_cost']:,.2f}\n"
            f"- 加工费：¥{quote['process_cost']:,.2f}\n"
            f"- 利润率：{quote['profit_rate'] * 100:.0f}%"
        )
        st.dataframe(
            pd.DataFrame(
                quote["table_rows"],
                columns=["项目", "规格/说明", "数量", "单价(元)", "金额(元)"],
            ),
            use_container_width=True,
            hide_index=True,
        )

    with c2:
        st.markdown("**排版预览**")
        fig = draw_nesting_preview(nesting)
        st.pyplot(fig, clear_figure=True)

    st.subheader("下载文件")
    d1, d2 = st.columns(2)
    with d1:
        st.download_button(
            label="下载 DXF 排版图",
            data=dxf_path.read_bytes(),
            file_name=dxf_path.name,
            mime="application/dxf",
        )
    with d2:
        st.download_button(
            label="下载 WPS 报价单",
            data=docx_path.read_bytes(),
            file_name=docx_path.name,
            mime=(
                "application/vnd.openxmlformats-officedocument"
                ".wordprocessingml.document"
            ),
        )

    st.caption(f"文件同时保存在：`{dxf_path.resolve().parent}`")


if __name__ == "__main__":
    main()
