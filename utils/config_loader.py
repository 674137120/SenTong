import os
import yaml
import json

def load_config(config_path=None):
    """
    加载系统配置
    
    参数:
        config_path (str, optional): 配置文件路径，默认为None，使用默认配置文件
        
    返回:
        dict: 配置字典
    """
    # 如果未指定配置文件，使用默认配置文件
    if config_path is None:
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'configs', 'config.yaml')
    
    # 检查文件是否存在
    if not os.path.exists(config_path):
        print(f"警告：配置文件 {config_path} 不存在，使用默认配置")
        return get_default_config()
    
    # 根据文件扩展名选择加载方式
    _, ext = os.path.splitext(config_path)
    try:
        if ext.lower() in ['.yaml', '.yml']:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
        elif ext.lower() == '.json':
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        else:
            print(f"不支持的配置文件格式：{ext}，使用默认配置")
            return get_default_config()
    except Exception as e:
        print(f"加载配置文件失败：{e}，使用默认配置")
        return get_default_config()
    
    # 合并默认配置和加载的配置
    default_config = get_default_config()
    merged_config = {**default_config, **config}
    
    return merged_config

def get_default_config():
    """
    获取默认配置
    
    返回:
        dict: 默认配置字典
    """
    return {
        # 模型配置
        'model_size': 's',                  # YOLOv5模型大小：n, s, m, l, x
        'num_classes_fire': 2,              # 火灾类别数（火焰、烟雾）
        'num_classes_animal': 5,            # 动物类别数（可根据保护区内具体动物调整）
        'num_classes_landslide': 3,         # 地质灾害类别数（滑坡、泥石流、山体崩塌）
        'conf_threshold': 0.25,             # 检测置信度阈值
        'iou_threshold': 0.45,              # NMS IOU阈值
        
        # 数据配置
        'image_size': 640,                  # 输入图像大小
        'batch_size': 16,                   # 批次大小
        'data_augmentation': True,          # 是否使用数据增强
        
        # 训练配置
        'learning_rate': 0.01,              # 学习率
        'weight_decay': 0.0005,             # 权重衰减
        'epochs': 100,                      # 训练轮数
        'save_interval': 10,                # 模型保存间隔
        
        # 系统配置
        'device': 'cuda:0',                 # 设备，cuda:0或cpu
        'num_workers': 4,                   # 数据加载线程数
        'weights_path': 'weights',          # 权重保存路径
        'logs_path': 'logs',                # 日志保存路径
        
        # 监测区域配置
        'monitor_regions': [
            {
                'name': '北部山区',
                'latitude': 40.123,
                'longitude': 116.456,
                'radius': 50,               # 监测半径（公里）
                'priority': 'high'
            },
            {
                'name': '南部林区',
                'latitude': 39.876,
                'longitude': 115.789,
                'radius': 40,
                'priority': 'medium'
            }
        ],
        
        # GIS集成配置
        'gis_api_key': '',                  # GIS API密钥
        'map_center': [39.9, 116.3],        # 地图中心点
        'map_zoom': 8,                      # 地图缩放级别
        
        # UI配置
        'dark_mode': True,                  # 是否使用暗色模式
        'language': 'zh_CN',                # 语言设置
        'auto_refresh': 60,                 # 自动刷新间隔（秒）
        
        # 告警配置
        'alert_threshold': 0.75,            # 告警阈值
        'alert_methods': ['ui', 'sound'],   # 告警方式：ui界面、声音
        'alert_interval': 30                # 告警间隔（秒）
    } 