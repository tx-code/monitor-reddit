# Reddit 在线人数监控系统 v2.0

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/streamlit-1.40+-red.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

一个基于 Streamlit 的现代化 Reddit 在线人数监控系统，提供实时数据可视化和智能分析功能。

## ✨ 主要特性

- 🎯 **实时监控**: 持续监控 Reddit 子版块的在线人数变化
- 📊 **数据可视化**: 丰富的图表和仪表盘展示监控数据
- 🔍 **智能分析**: 趋势分析、异常检测和活动模式识别
- ⚙️ **灵活配置**: 支持自定义监控间隔和目标子版块
- 📱 **现代界面**: 基于 Streamlit 的响应式 Web 界面
- 📈 **数据导出**: 支持 CSV 和 JSON 格式数据导出
- 🔄 **后台运行**: 支持后台监控进程，不影响界面操作

## 🚀 快速开始

### 安装依赖

使用 uv (推荐):
```bash
# 安装项目依赖
uv sync

# 激活虚拟环境
uv shell
```

或使用 pip:
```bash
pip install -r requirements.txt
```

### 启动应用

```bash
# 方法1: 使用启动脚本
python scripts/run_app.py

# 方法2: 直接运行 Streamlit
streamlit run src/ui/app.py

# 方法3: 使用项目命令 (安装后)
reddit-monitor
```

### 开始监控

1. 打开浏览器访问 `http://localhost:8501`
2. 在侧边栏配置监控参数:
   - 选择或输入 Reddit 子版块 URL
   - 设置检查间隔 (建议 5-15 分钟)
   - 配置数据存储目录
3. 点击 "保存配置" 然后 "开始" 启动监控
4. 查看实时数据和分析图表

## 📁 项目结构

```
monitor-reddit/
├── src/                          # 源代码目录
│   ├── core/                     # 核心功能模块
│   │   ├── config_manager.py     # 配置管理
│   │   ├── reddit_monitor.py     # Reddit监控核心
│   │   └── data_analyzer.py      # 数据分析
│   ├── ui/                       # 用户界面模块
│   │   ├── app.py               # Streamlit主应用
│   │   └── components/          # UI组件
│   │       ├── dashboard.py     # 仪表板组件
│   │       ├── charts.py        # 图表组件
│   │       └── config_panel.py  # 配置面板
│   └── utils/                    # 工具模块
│       ├── logger.py            # 日志工具
│       └── validators.py        # 验证工具
├── scripts/                      # 脚本目录
│   ├── run_app.py               # 应用启动脚本
│   └── background_monitor.py    # 后台监控脚本
├── config/                       # 配置文件目录
│   └── default_config.json      # 默认配置
├── data/                         # 数据存储目录
├── logs/                         # 日志目录
└── tests/                        # 测试目录
```

## 🔧 配置选项

### 监控配置
- **URL**: Reddit 子版块完整 URL
- **检查间隔**: 监控频率 (1-1440 分钟)
- **数据目录**: 监控数据存储路径
- **连续模式**: 启用智能调度和时间恢复

### 预设子版块
系统提供常用子版块预设:
- r/Python - Python 编程社区
- r/programming - 编程技术讨论
- r/technology - 科技新闻讨论
- r/datascience - 数据科学社区
- r/MachineLearning - 机器学习研究
- r/webdev - Web 开发社区

## 📊 功能模块

### 1. 实时监控仪表板
- 当前在线人数和变化趋势
- 总成员数统计
- 监控成功率和数据质量指标
- 最近活动记录

### 2. 数据可视化
- **时间序列图**: 在线人数变化趋势
- **活动模式图**: 24小时活动规律
- **分布图**: 在线人数分布统计
- **变化分析图**: 数据变化幅度分析

### 3. 数据分析
- 趋势分析和模式识别
- 异常检测 (基于标准差)
- 成长指标计算
- 活动高峰时段识别

### 4. 数据管理
- CSV/JSON 格式数据导出
- 数据质量检查
- 历史数据查看
- 配置备份和恢复

## 🛠️ 高级用法

### 后台监控模式

```bash
# 启动后台监控
python scripts/background_monitor.py

# 查看监控状态
python scripts/background_monitor.py --status

# 停止后台监控
python scripts/background_monitor.py --stop
```

### 命令行工具

```bash
# 查看帮助
reddit-monitor --help

# 启动Web界面
reddit-monitor

# 启动后台监控
reddit-monitor-bg
```

### 数据分析脚本

```python
from src.core.data_analyzer import DataAnalyzer

# 创建分析器
analyzer = DataAnalyzer("data")

# 生成分析报告
report = analyzer.generate_report()
print(report)

# 导出分析结果
analyzer.export_analysis("analysis_report.json")
```

## 🔍 故障排除

### 常见问题

1. **无法获取数据**
   - 检查网络连接
   - 验证 Reddit URL 是否正确
   - 查看日志文件获取详细错误信息

2. **监控自动停止**
   - 检查 `logs/` 目录中的日志文件
   - 确认系统资源充足
   - 检查配置文件是否正确

3. **数据不更新**
   - 点击"手动检查"按钮测试
   - 检查监控间隔设置
   - 确认后台进程运行状态

4. **界面显示异常**
   - 刷新浏览器页面
   - 检查 Streamlit 版本兼容性
   - 查看浏览器控制台错误信息

### 日志文件位置
- 应用日志: `logs/reddit_monitor_YYYYMMDD.log`
- 后台监控日志: `logs/background_monitor.log`

## 🤝 贡献指南

1. Fork 本项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- [Streamlit](https://streamlit.io/) - 现代化 Web 应用框架
- [Plotly](https://plotly.com/) - 交互式图表库
- [pandas](https://pandas.pydata.org/) - 数据分析库
- [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/) - HTML 解析库

## 📞 支持

如有问题或建议，请:
- 创建 [GitHub Issue](https://github.com/username/reddit-monitor/issues)
- 发送邮件至: [your-email@example.com]
- 查看 [Wiki 文档](https://github.com/username/reddit-monitor/wiki)

---

⭐ 如果这个项目对你有帮助，请给它一个星标！