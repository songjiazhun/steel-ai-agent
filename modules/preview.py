"""套裁结果 2D 预览图绘制。"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties
from matplotlib.patches import Rectangle

from modules.nesting_engine import PlacedItem

# macOS / Windows / Linux（含 Streamlit Cloud）常见中文字体
_CJK_FONT_CANDIDATES: List[str] = [
    "Noto Sans CJK SC",
    "Noto Sans CJK JP",
    "Noto Serif CJK SC",
    "Source Han Sans SC",
    "PingFang SC",
    "Hiragino Sans GB",
    "Heiti SC",
    "STHeiti",
    "Songti SC",
    "Arial Unicode MS",
    "Microsoft YaHei",
    "SimHei",
    "WenQuanYi Micro Hei",
]

_LINUX_FONT_DIRS: List[str] = [
    "/usr/share/fonts/opentype/noto",
    "/usr/share/fonts/truetype/noto",
    "/usr/share/fonts/noto-cjk",
    "/usr/share/fonts/truetype/wqy",
]


def _register_linux_cjk_fonts() -> None:
    """把系统 apt 安装的 Noto CJK 字体注册进 Matplotlib（Streamlit Cloud）。"""
    for dir_path in _LINUX_FONT_DIRS:
        root = Path(dir_path)
        if not root.is_dir():
            continue
        for font_file in root.rglob("*"):
            if font_file.suffix.lower() not in {".ttf", ".otf", ".ttc"}:
                continue
            try:
                font_manager.fontManager.addfont(str(font_file))
            except (OSError, RuntimeError, ValueError):
                continue


@lru_cache(maxsize=1)
def _resolve_cjk_font() -> Optional[FontProperties]:
    """解析本机可用的中文字体，供 Matplotlib 绘制中文。"""
    _register_linux_cjk_fonts()
    available_names: set[str] = {f.name for f in font_manager.fontManager.ttflist}
    for name in _CJK_FONT_CANDIDATES:
        if name in available_names:
            # 用 family 而不是 ttc 文件路径，避免 PingFang.ttc 选错子字体
            prop = FontProperties(family=name)
            plt.rcParams["font.family"] = "sans-serif"
            plt.rcParams["font.sans-serif"] = [name, "DejaVu Sans"]
            plt.rcParams["axes.unicode_minus"] = False
            return prop

    # 按文件名再扫一遍（部分环境 name 注册不完整）
    path_keywords: List[str] = [
        "NotoSansCJK",
        "NotoSerifCJK",
        "SourceHanSans",
        "PingFang",
        "Hiragino Sans GB",
        "STHeiti",
        "Songti",
        "Arial Unicode",
        "msyh",
        "simhei",
        "wqy",
    ]
    for font in font_manager.fontManager.ttflist:
        path_lower: str = font.fname.lower()
        if any(
            k.lower() in path_lower or k.lower() in font.name.lower()
            for k in path_keywords
        ):
            prop = FontProperties(fname=font.fname)
            plt.rcParams["font.sans-serif"] = [font.name, "DejaVu Sans"]
            plt.rcParams["axes.unicode_minus"] = False
            return prop
    return None


def draw_nesting_preview(nesting_data: Dict[str, Any]) -> Figure:
    """根据套裁结果绘制母板排版预览图。

    Args:
        nesting_data: NestingEngine2D.pack() 返回结果。

    Returns:
        Matplotlib Figure，可供 Streamlit 展示。
    """
    font_prop: Optional[FontProperties] = _resolve_cjk_font()

    stock_w: float = float(nesting_data.get("stock_width_mm", 2200.0))
    stock_l: float = float(nesting_data.get("stock_length_mm", 6000.0))
    sheets: List[List[PlacedItem]] = nesting_data.get("sheets", [])
    num_sheets: int = max(len(sheets), 1)

    fig: Figure
    axes_arr: Any
    fig, axes_arr = plt.subplots(
        1,
        num_sheets,
        figsize=(4.5 * num_sheets, 7.5),
        squeeze=False,
    )
    axes: List[Axes] = list(axes_arr[0])

    colors: List[str] = [
        "#2E7D32",
        "#1565C0",
        "#E65100",
        "#6A1B9A",
        "#00838F",
        "#C62828",
    ]

    for sheet_idx, ax in enumerate(axes):
        ax.set_xlim(-50, stock_w + 50)
        ax.set_ylim(-50, stock_l + 150)
        ax.set_aspect("equal")
        ax.set_xlabel("宽度 (mm)", fontproperties=font_prop)
        ax.set_ylabel("长度 (mm)", fontproperties=font_prop)
        ax.set_title(f"母板 #{sheet_idx + 1}", fontproperties=font_prop)
        ax.add_patch(
            Rectangle(
                (0, 0),
                stock_w,
                stock_l,
                fill=False,
                edgecolor="#C62828",
                linewidth=2.0,
            )
        )

        if sheet_idx >= len(sheets):
            continue

        for i, part in enumerate(sheets[sheet_idx]):
            color: str = colors[i % len(colors)]
            ax.add_patch(
                Rectangle(
                    (part.x, part.y),
                    part.width,
                    part.length,
                    facecolor=color,
                    edgecolor="#1B5E20",
                    alpha=0.55,
                    linewidth=1.0,
                )
            )
            cx: float = part.x + part.width / 2.0
            cy: float = part.y + part.length / 2.0
            # 用 ASCII x，避免部分字体缺 × 字形
            label: str = f"{part.id}\n{part.width:.0f}x{part.length:.0f}"
            ax.text(
                cx,
                cy,
                label,
                ha="center",
                va="center",
                fontsize=7,
                color="white",
                fontproperties=font_prop,
            )

    fig.suptitle(
        "钢板套裁排版预览",
        fontsize=14,
        fontproperties=font_prop,
    )
    fig.tight_layout()
    return fig
