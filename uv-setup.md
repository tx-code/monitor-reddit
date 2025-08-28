# UV环境配置指南

本项目已配置支持uv依赖管理工具。以下是使用uv的快速指南：

## 安装uv

```bash
# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## 项目设置

```bash
# 同步项目依赖
uv sync

# 同步开发依赖（包含测试和打包工具）
uv sync --dev
```

## 常用命令

### 运行程序
```bash
# 运行主程序
uv run python main.py

# 运行Web界面
uv run python start_web.py

# 运行测试
uv run pytest

# 运行快速测试
uv run python test_quick.py
```

### 依赖管理
```bash
# 添加新依赖
uv add requests

# 添加开发依赖
uv add --dev pytest

# 移除依赖
uv remove package_name

# 列出依赖
uv list
```

### 打包构建
```bash
# 使用uv环境打包（推荐）
uv run python build_uv.py

# 或使用混合模式打包
uv run python build_exe.py

# 仅设置uv环境
uv run python build_uv.py --setup-only
```

## 项目结构

```
reddit-monitor/
├── pyproject.toml      # uv项目配置
├── .python-version     # Python版本指定
├── build_uv.py         # uv专用打包脚本
├── build_exe.py        # 兼容打包脚本
└── ...
```

## 优势

使用uv的优势：
- **更快的依赖解析**: 比pip快10-100倍
- **锁文件**: 确保依赖版本一致性
- **虚拟环境管理**: 自动创建和管理虚拟环境
- **更好的错误信息**: 更清晰的依赖冲突提示
- **跨平台一致性**: 统一的开发体验

## 迁移现有项目

如果你已经在使用pip/venv：

```bash
# 1. 安装uv
# 2. 在项目目录运行
uv sync --dev

# 3. 之后使用uv命令替代pip
# 旧: pip install package
# 新: uv add package

# 旧: python script.py 
# 新: uv run python script.py
```

## 故障排除

### 常见问题

1. **uv命令不存在**
   - 确保uv已安装并在PATH中
   - 重启终端或重新加载shell配置

2. **依赖解析失败**
   - 检查pyproject.toml中的依赖约束
   - 尝试 `uv sync --reinstall`

3. **虚拟环境问题**
   - 删除 `.venv` 目录重新同步
   - `uv sync --reinstall`

### 获取帮助

```bash
# 查看uv帮助
uv --help

# 查看特定命令帮助
uv sync --help
uv add --help
```