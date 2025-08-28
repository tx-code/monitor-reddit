# Reddit监控系统

一个基于Python的网站内容监控工具，支持GUI和Web界面。

## 快速开始

### 1. 安装uv
```bash
# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. 设置项目
```bash
# 克隆项目后
cd reddit-monitor

# 同步依赖
uv sync --dev
```

### 3. 运行程序
```bash
# 方式1：使用便捷脚本
python run.py

# 方式2：直接运行
uv run python main.py

# 方式3：仅Web界面
uv run python start_web.py
```

## 主要功能

- ✅ **网站内容监控** - 定期检查网站内容变化
- ✅ **双界面支持** - GUI桌面界面 + Web浏览器界面
- ✅ **配置管理** - 灵活的监控目标和间隔设置
- ✅ **数据分析** - 内容变化历史和统计分析
- ✅ **日志系统** - 完整的操作日志记录

## 开发命令

```bash
# 运行测试
uv run pytest

# 快速测试
uv run python test_quick.py

# 打包exe
uv run python build_exe.py

# 仅设置环境
uv run python build_exe.py --setup-only

# 清理构建文件
uv run python build_exe.py --clean
```

## 项目结构

```
reddit-monitor/
├── main.py              # 主程序（GUI界面）
├── start_web.py         # Web界面启动
├── run.py               # 统一启动脚本
├── build_exe.py         # 打包脚本
├── pyproject.toml       # uv项目配置
├── reddit_monitor.py    # 核心监控逻辑
├── config_manager.py    # 配置管理
├── web_interface.py     # Web界面
├── data_analyzer.py     # 数据分析
├── templates/           # Web模板
└── tests/              # 测试文件
```

## 依赖管理

本项目使用[uv](https://github.com/astral-sh/uv)管理依赖：

- **运行时依赖**: requests, flask
- **开发依赖**: pytest, pytest-mock, pytest-cov  
- **构建依赖**: pyinstaller, pillow

所有依赖在 `pyproject.toml` 中定义。

## 打包分发

```bash
# 完整打包流程
uv run python build_exe.py

# 输出文件
release/
├── RedditMonitor.exe                    # 可执行文件
├── 使用说明.txt                         # 用户说明
└── RedditMonitor_v1.0_YYYYMMDD.zip     # 分发包
```

生成的exe文件可在没有Python环境的Windows系统上直接运行。

## 系统要求

- Python 3.8+（开发）
- Windows 7/8/10/11（运行exe）
- 网络连接（监控功能）

## 许可证

MIT License