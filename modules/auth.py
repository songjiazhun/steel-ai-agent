"""演示环境简易口令登录。"""

from __future__ import annotations

from typing import Optional

import streamlit as st


def _expected_password() -> Optional[str]:
    """从 Streamlit secrets 读取演示口令；未配置则返回 None（本地免登录）。"""
    try:
        return str(st.secrets["demo_password"])
    except Exception:  # noqa: BLE001
        return None


def require_demo_login() -> bool:
    """演示登录门禁。

    - 未配置 `demo_password`：直接放行（本地开发方便）
    - 已配置：必须输入正确口令后才能进入

    Returns:
        True 表示已通过，可渲染主页面。
    """
    expected: Optional[str] = _expected_password()
    if not expected:
        return True

    if st.session_state.get("authenticated") is True:
        with st.sidebar:
            if st.button("退出登录", use_container_width=True):
                st.session_state.authenticated = False
                st.rerun()
        return True

    st.title("Steel AI Agent")
    st.caption("客户演示环境 · 请输入访问口令")
    with st.form("demo_login_form"):
        password: str = st.text_input("访问口令", type="password")
        submitted: bool = st.form_submit_button("进入演示", type="primary")
        if submitted:
            if password == expected:
                st.session_state.authenticated = True
                st.rerun()
            st.error("口令错误，请重试。")
    st.info("这是受保护的演示环境，口令由部署方提供。")
    return False
