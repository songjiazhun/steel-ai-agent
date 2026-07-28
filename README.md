# Steel AI Agent

钢材行业 **AI CAD 画图 + 2D 排版套裁 + WPS 报价单自动生成** 全流程自动化系统。

## 功能概览

| 模块 | 说明 |
|------|------|
| Web 工作台 | Streamlit 页面：改零件/母板/单价，一键套裁并下载结果 |
| 演示口令 | 线上可配置访问口令，方便给客户演示 |
| 2D 套裁引擎 | Shelf / Bin-Packing 算法，自动计算钢板排版 |
| CAD 出图 | 基于 `ezdxf` 生成多图层 DXF 矢量图纸 |
| WPS 报价 | 基于 `python-docx` 导出可在 WPS Office 打开的商务报价单 |

## 目录结构

```
steel-ai-agent/
├── app.py                  # Streamlit 网页入口（推荐）
├── main.py                 # 命令行一键演示入口
├── modules/
│   ├── auth.py             # 演示口令登录
│   ├── nesting_engine.py
│   ├── cad_generator.py
│   ├── wps_exporter.py
│   ├── pricing.py
│   └── preview.py
├── .streamlit/             # 线上主题与 secrets 示例
├── output/
├── tests/
├── requirements.txt
└── TASK.md
```

## 快速开始（本地）

```bash
cd /Users/songjiazhun/steel-ai-agent
pip3 install -r requirements.txt
python3 -m streamlit run app.py
```

本地默认**不需要登录**。若要本地也验证口令：

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# 编辑 secrets.toml，取消注释并设置 demo_password
```

### 命令行演示

```bash
python3 main.py
```

## 部署线上（给客户演示）

推荐用 **Streamlit Community Cloud**（免费、有公网链接）：

1. 把本仓库推到 GitHub（公开或私有均可）
2. 打开 [https://share.streamlit.io](https://share.streamlit.io) 用 GitHub 登录
3. New app → 选择仓库，Main file 填 `app.py`
4. 在 App settings → Secrets 写入：

```toml
demo_password = "给你客户的演示口令"
```

5. Deploy 完成后把链接和口令发给客户即可

说明：这是演示级口令保护，不是完整账号体系；正式商用再考虑多用户与权限。

## 运行测试

```bash
python3 -m unittest discover -s tests -v
```

输出文件带时间后缀，例如：

- `钢板套裁排版图_20260728_213000.dxf`
- `钢板套裁报价单_20260728_213000.docx`

## 图层标准（CAD）

| 图层名 | 颜色 | 用途 |
|--------|------|------|
| `0_STOCK_BORDER` | 红色 (1) | 大板外框 |
| `0_PARTS` | 绿色 (3) | 零件边框 |
| `0_TEXT` | 黄色 (2) | 文字标注 |
