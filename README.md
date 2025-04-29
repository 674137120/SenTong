# 森瞳森林多模态灾害监测系统
![Uploading image.png…]()

## 项目概述

森瞳森林多模态灾害监测系统是一个基于深度学习的智能森林监控平台，采用YOLOv5作为核心检测框架，结合多任务学习方法，实现对森林火灾、野生动物活动、地质灾害等多种灾害类型的实时监测和预警。系统集成了多路摄像头实时监控、无人机集群管理、GIS地理信息系统等功能，为森林安全管理提供全方位的技术支持。

## 核心技术特点

### 1. 多任务深度学习框架

- **检测网络**: 基于YOLOv5的多任务检测网络
- **模型优化**:
  - 任务特定的检测头设计
  - 多尺度特征融合
  - 注意力机制增强
- **训练策略**:
  - 多任务联合训练
  - 渐进式学习
  - 数据增强技术

### 2. 特征增强模块

- **SPD-Conv空间金字塔扩张卷积**
  - 增强小目标检测能力
  - 多尺度特征提取
- **CBAM通道空间注意力机制**
  - 提升模糊目标识别效果
  - 自适应特征权重调整
- **高分辨率特征保留模块**
  - 保持细节信息
  - 提高检测精度

## 系统功能

### 1. 多路摄像头监控 🎥

- **视频源支持**:
  - IP摄像头 (RTSP/RTMP)
  - USB摄像头
  - 本地视频文件
- **显示模式**:
  - 9路同屏显示
  - 单路全屏
  - 自定义布局
- **视频处理**:
  - 实时编解码
  - 画面增强
  - 运动检测

### 2. 智能灾害检测 🔥

- **火灾检测**:
  - 烟雾识别
  - 火焰检测
  - 热成像分析
- **野生动物监测**:
  - 物种识别
  - 行为分析
  - 数量统计
- **地质灾害预警**:
  - 地表变形检测
  - 滑坡预警
  - 泥石流监测

### 3. 无人机集群管理 🚁

- **飞行控制**:
  - 一键起飞/降落
  - 自动返航
  - 紧急停止
- **任务规划**:
  - 航线规划
  - 区域覆盖
  - 目标跟踪
- **数据采集**:
  - 高清图像
  - 热成像
  - 多光谱数据

### 4. GIS地图集成 🗺️

- **地图功能**:
  - 多图层显示
  - 实时定位
  - 区域标记
- **数据可视化**:
  - 热力图
  - 轨迹回放
  - 统计图表

## 系统要求

### 硬件要求

- **处理器**: Intel Core i7-9700K或更高
- **内存**: 16GB RAM (推荐32GB)
- **显卡**: NVIDIA RTX 2060 6GB或更高
- **存储**: 500GB SSD (系统盘)
- **网络**: 千兆以太网

### 软件要求

- **操作系统**:
  - Windows 10/11 专业版
  - Ubuntu 20.04 LTS或更高
- **Python环境**:
  - Python 3.8+
  - CUDA 11.3+
  - cuDNN 8.2+
- **依赖库版本**:
  - PyTorch 1.10+
  - OpenCV 4.5+
  - PyQt5 5.15+

## 快速开始

### 1. 环境配置

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 安装CUDA工具包（如果需要GPU加速）
# 请访问NVIDIA官网下载对应版本的CUDA和cuDNN
```

### 2. 配置文件说明

在 `configs/config.yaml` 中配置系统参数：

```yaml
# 基础配置
app_name: "森瞳森林多模态灾害监测系统"
theme: "dark"  # dark/light
language: "zh_CN"
debug_mode: false

# 更新配置
update_interval: 60  # 秒
auto_save: true
save_interval: 300  # 秒

# 地图配置
map_center: [39.916527, 116.397128]  # 北京市中心
map_zoom: 12
map_type: "satellite"  # satellite/terrain/roadmap

# 监测区域配置
monitor_regions:
  - name: "北京密云"
    latitude: 40.3764
    longitude: 116.8301
    radius: 5  # 公里
    camera_ids: ["CAM001", "CAM002"]
  
# 摄像头配置
cameras:
  - id: "CAM001"
    name: "密云水库东"
    type: "rtsp"
    url: "rtsp://admin:admin@192.168.1.100:554"
    enabled: true
  
# 检测模型配置
models:
  fire:
    weights: "weights/fire_detection.pt"
    conf_thres: 0.25
    iou_thres: 0.45
  animal:
    weights: "weights/animal_detection.pt"
    conf_thres: 0.3
    iou_thres: 0.5
```

### 3. 启动系统

```bash
# 启动主程序
python main.py

# 启动带调试信息的程序
python main.py --debug

# 指定配置文件启动
python main.py --config configs/custom_config.yaml
```

## 使用指南

### 1. 界面布局

系统界面分为四个主要区域：

- **顶部**: 主菜单栏和工具栏
- **左侧**: 控制面板和地图显示
- **中间**: 摄像头监控界面
- **右侧**: 统计信息和告警面板

### 2. 基本操作流程

#### 2.1 系统初始化

1. 启动系统后，检查所有摄像头连接状态
2. 确认无人机通信正常
3. 验证地图服务可用性

#### 2.2 监控操作

1. 选择监控区域
2. 配置检测参数
3. 启动视频流
4. 开启智能检测

#### 2.3 告警处理

1. 接收告警信息
2. 查看告警详情
3. 确认和处理告警
4. 生成告警报告

### 3. 快捷键

- **系统操作**:
  - `Ctrl+S`: 保存当前配置
  - `Ctrl+R`: 刷新监控画面
  - `Ctrl+Q`: 退出系统
  - `F11`: 全屏切换
- **视图操作**:
  - `1-9`: 切换摄像头视图
  - `Space`: 暂停/继续视频流
  - `Ctrl+C`: 截图
  - `Ctrl+V`: 粘贴图片
- **地图操作**:
  - `+/-`: 缩放地图
  - `方向键`: 平移地图
  - `Home`: 返回默认视图

## 开发指南

### 1. 项目结构

```
project_root/
├── main.py                    # 主程序入口
├── README.md                  # 项目说明文档
├── requirements.txt           # 项目依赖
├── map_temp.html             # 地图临时文件
│
├── ui/                       # 用户界面相关
│   ├── assets/              # 静态资源
│   ├── components/          # UI组件
│   │   ├── alert_panel.py      # 告警面板
│   │   ├── camera_view.py      # 摄像头视图
│   │   ├── control_panel.py    # 控制面板
│   │   ├── drone_manager.py    # 无人机管理
│   │   ├── grid_camera_view.py # 网格摄像头视图
│   │   ├── map_view.py         # 地图视图
│   │   └── statistics_panel.py # 统计面板
│   ├── pages/               # 页面
│   │   └── main_window.py   # 主窗口
│   └── splash_screen.py     # 启动画面
│
├── configs/                  # 配置文件
│   ├── config.yaml          # 主配置
│   └── yolov5s.yaml        # YOLOv5模型配置
│
├── utils/                   # 工具函数
│   ├── loggers/            # 日志工具
│   ├── aws/                # AWS相关工具
│   ├── config_loader.py    # 配置加载器
│   ├── camera_detector.py  # 摄像头检测器
│   ├── torch_utils.py      # PyTorch工具
│   ├── metrics.py          # 评估指标
│   ├── plots.py           # 绘图工具
│   ├── loss.py            # 损失函数
│   ├── general.py         # 通用工具
│   ├── datasets.py        # 数据集处理
│   └── ...                # 其他工具函数
│
├── models/                  # 模型相关
├── weights/                # 模型权重
├── results/                # 结果输出
├── scripts/                # 脚本文件
├── resources/              # 资源文件
└── data/                   # 数据文件
```

### 2. 开发规范

#### 2.1 代码风格

- 遵循PEP 8规范
- 使用类型注解
- 编写详细的文档字符串
- 保持代码模块化

#### 2.2 Git提交规范

```
feat: 新功能
fix: 修复bug
docs: 文档更新
style: 代码格式化
refactor: 代码重构
test: 测试相关
chore: 构建过程或辅助工具的变动
```

#### 2.3 测试规范

- 单元测试覆盖率 > 80%
- 集成测试覆盖主要功能
- 提交前本地测试通过
- 编写测试文档

## 常见问题

### 1. 系统启动问题

- **问题**: 系统无法启动
- **解决方案**:
  1. 检查Python版本
  2. 验证依赖完整性
  3. 查看日志文件
  4. 确认配置文件正确

### 2. 摄像头连接问题

- **问题**: 摄像头画面不显示
- **解决方案**:
  1. 检查网络连接
  2. 验证摄像头地址
  3. 确认权限设置
  4. 更新摄像头驱动

### 3. 性能优化

- **问题**: 系统运行缓慢
- **解决方案**:
  1. 降低分辨率
  2. 调整检测频率
  3. 优化GPU使用
  4. 清理缓存数据

## 技术支持

### 问题反馈

- Issues: [GitHub Issues](https://github.com/your-repo/issues)
- 邮箱: 674137120@qq.com
- QQ: 674137120

### 文档资源

- [在线文档](https://docs.example.com)
- [API参考](https://api.example.com)
- [开发Wiki](https://wiki.example.com)

## 贡献指南

欢迎提交 Pull Request 或 Issue。在贡献代码前，请：

1. Fork 本仓库
2. 创建新的分支
3. 提交变更
4. 创建 Pull Request

## 致谢

感谢以下开源项目的支持：

- YOLOv5
- PyQt5
- OpenCV
- PyTorch

---

© 2025 森瞳科技。保留所有权利。
