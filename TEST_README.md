# Reddit监控系统测试指南

这个文档介绍如何运行和使用Reddit监控系统的测试套件。

## 测试结构

```
tests/
├── __init__.py                 # 测试包初始化
├── test_config_manager.py      # 配置管理器单元测试
├── test_reddit_monitor.py      # Reddit监控器单元测试
├── test_data_analyzer.py       # 数据分析器单元测试
├── test_web_interface.py       # Web界面集成测试
└── test_performance.py         # 性能和压力测试
```

## 安装测试依赖

```bash
# 安装所有依赖
pip install -r requirements.txt

# 或者单独安装测试依赖
pip install pytest pytest-mock pytest-cov psutil
```

## 运行测试

### 1. 快速测试（推荐开发时使用）

```bash
python test_quick.py
```

快速验证所有核心功能是否正常工作，耗时约几秒钟。

### 2. 完整测试套件

```bash
# 运行所有测试
python run_tests.py

# 或使用参数运行特定类型的测试
python run_tests.py --type unit          # 仅单元测试
python run_tests.py --type integration   # 仅集成测试  
python run_tests.py --type performance   # 仅性能测试
python run_tests.py --type stress        # 仅压力测试
python run_tests.py --type lint          # 仅代码检查

# 详细输出
python run_tests.py --verbose

# 生成覆盖率报告
python run_tests.py --coverage

# 跳过压力测试（节省时间）
python run_tests.py --skip-stress
```

### 3. 直接使用pytest

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_config_manager.py

# 详细输出
pytest -v

# 生成覆盖率报告
pytest --cov=. --cov-report=html

# 运行性能测试（不包括慢速测试）
pytest tests/test_performance.py -m "not slow"

# 运行压力测试
pytest tests/test_performance.py -m "slow"
```

## 测试类型说明

### 单元测试
- **test_config_manager.py**: 测试配置文件的加载、保存、验证等功能
- **test_reddit_monitor.py**: 测试网站监控、数据获取、变化检测等核心功能
- **test_data_analyzer.py**: 测试数据文件分析、变化统计等功能
- **test_web_interface.py**: 测试Web API端点和界面功能

### 集成测试
- 测试各模块之间的协作
- 测试完整的工作流程
- 验证配置变更对系统的影响

### 性能测试
- 测试大量数据文件的处理性能
- 测试配置加载/保存性能
- 测试并发访问性能
- 内存使用情况测试

### 压力测试
- 长时间运行测试
- 大量数据处理测试
- 极限情况处理测试

## 测试报告

运行测试后会生成以下报告：

1. **控制台输出**: 实时显示测试结果
2. **test_report.html**: 详细的HTML测试报告
3. **htmlcov/**: 覆盖率报告（使用--coverage参数时）

## 常见测试场景

### 开发时快速验证
```bash
python test_quick.py
```

### 提交前完整测试
```bash
python run_tests.py --skip-stress
```

### 性能基准测试
```bash
python run_tests.py --type performance --verbose
```

### 发布前完整验证
```bash
python run_tests.py --verbose --coverage
```

## Mock和模拟

测试中使用了以下模拟技术：

- **网络请求模拟**: 使用`unittest.mock.patch`模拟requests.get
- **文件系统模拟**: 使用临时目录和文件
- **时间模拟**: 使用固定的时间戳进行测试
- **错误模拟**: 模拟各种异常情况

## 测试数据

测试使用临时数据，不会影响实际的监控数据：

- 临时配置文件
- 临时数据目录  
- 模拟的网络响应
- 测试专用的URL和内容

## 故障排除

### 常见问题

1. **导入错误**: 确保在项目根目录运行测试
2. **权限错误**: 确保有临时目录的读写权限
3. **网络错误**: 性能测试可能需要网络访问
4. **编码错误**: Windows环境下可能遇到Unicode问题

### 调试技巧

```bash
# 显示详细错误信息
pytest -v -s

# 在第一个失败时停止
pytest -x

# 运行特定测试
pytest tests/test_config_manager.py::TestConfigManager::test_init_with_default_config

# 显示最慢的10个测试
pytest --durations=10
```

## 持续集成

测试脚本设计用于CI/CD环境：

- 返回适当的退出码
- 生成机器可读的测试报告
- 支持并行测试执行
- 自动处理依赖安装

## 贡献测试

添加新测试时请遵循以下原则：

1. 使用描述性的测试名称
2. 每个测试只验证一个功能
3. 使用适当的断言
4. 清理测试数据
5. 添加适当的文档字符串

示例：
```python
def test_config_validation_with_invalid_url(self):
    """测试配置验证功能对无效URL的处理"""
    config_manager = ConfigManager(self.config_file)
    config_manager.update_monitor_config(url="invalid-url")
    
    errors = config_manager.validate_config()
    assert len(errors) > 0
    assert any("URL" in error for error in errors)
```