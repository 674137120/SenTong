import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QComboBox, QGroupBox, QSlider, QCheckBox,
                            QSpinBox, QDoubleSpinBox, QFormLayout, QTabWidget)
from PyQt5.QtCore import Qt, pyqtSlot, QSize, QSettings
from PyQt5.QtGui import QIcon, QFont

class ControlPanel(QWidget):
    """控制面板组件，用于系统参数调整和控制"""
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        # 创建主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 创建标签页
        tab_widget = QTabWidget()
        
        # 添加检测控制页
        detection_tab = self.create_detection_tab()
        tab_widget.addTab(detection_tab, "检测控制")
        
        # 添加摄像头控制页
        camera_tab = self.create_camera_tab()
        tab_widget.addTab(camera_tab, "摄像头控制")
        
        # 添加告警控制页
        alert_tab = self.create_alert_tab()
        tab_widget.addTab(alert_tab, "告警控制")
        
        # 添加标签页到布局
        layout.addWidget(tab_widget)
        
        # 底部按钮区域
        button_layout = QHBoxLayout()
        
        # 启动按钮
        self.start_btn = QPushButton("启动监测")
        self.start_btn.setIcon(QIcon(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'start.png')))
        self.start_btn.clicked.connect(self.start_monitoring)
        button_layout.addWidget(self.start_btn)
        
        # 停止按钮
        self.stop_btn = QPushButton("停止监测")
        self.stop_btn.setIcon(QIcon(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'stop.png')))
        self.stop_btn.clicked.connect(self.stop_monitoring)
        self.stop_btn.setEnabled(False)
        button_layout.addWidget(self.stop_btn)
        
        # 添加按钮区域到布局
        layout.addLayout(button_layout)
        
    def create_detection_tab(self):
        """创建检测控制标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 检测任务分组
        task_group = QGroupBox("检测任务")
        task_layout = QVBoxLayout(task_group)
        
        # 添加复选框
        self.fire_check = QCheckBox("火灾检测")
        self.fire_check.setChecked(True)
        task_layout.addWidget(self.fire_check)
        
        self.animal_check = QCheckBox("动物检测")
        self.animal_check.setChecked(True)
        task_layout.addWidget(self.animal_check)
        
        self.landslide_check = QCheckBox("滑坡检测")
        self.landslide_check.setChecked(True)
        task_layout.addWidget(self.landslide_check)
        
        self.pest_check = QCheckBox("病虫害检测")
        self.pest_check.setChecked(True)
        task_layout.addWidget(self.pest_check)
        
        layout.addWidget(task_group)
        
        # 检测参数分组
        param_group = QGroupBox("检测参数")
        param_layout = QFormLayout(param_group)
        
        # 置信度阈值
        self.conf_slider = QSlider(Qt.Horizontal)
        self.conf_slider.setRange(1, 100)
        self.conf_slider.setValue(int(self.config.get('conf_threshold', 0.25) * 100))
        self.conf_slider.setTickPosition(QSlider.TicksBelow)
        self.conf_slider.setTickInterval(10)
        self.conf_slider.valueChanged.connect(self.update_conf_threshold)
        
        self.conf_label = QLabel(f"{self.conf_slider.value() / 100:.2f}")
        conf_layout = QHBoxLayout()
        conf_layout.addWidget(self.conf_slider)
        conf_layout.addWidget(self.conf_label)
        
        param_layout.addRow("置信度阈值:", conf_layout)
        
        # IOU阈值
        self.iou_slider = QSlider(Qt.Horizontal)
        self.iou_slider.setRange(1, 100)
        self.iou_slider.setValue(int(self.config.get('iou_threshold', 0.45) * 100))
        self.iou_slider.setTickPosition(QSlider.TicksBelow)
        self.iou_slider.setTickInterval(10)
        self.iou_slider.valueChanged.connect(self.update_iou_threshold)
        
        self.iou_label = QLabel(f"{self.iou_slider.value() / 100:.2f}")
        iou_layout = QHBoxLayout()
        iou_layout.addWidget(self.iou_slider)
        iou_layout.addWidget(self.iou_label)
        
        param_layout.addRow("IOU阈值:", iou_layout)
        
        # 输入尺寸
        self.size_combo = QComboBox()
        self.size_combo.addItem("320x320", 320)
        self.size_combo.addItem("416x416", 416)
        self.size_combo.addItem("512x512", 512)
        self.size_combo.addItem("640x640", 640)
        self.size_combo.addItem("1280x1280", 1280)
        
        # 设置默认值
        default_size = self.config.get('image_size', 640)
        index = self.size_combo.findData(default_size)
        if index >= 0:
            self.size_combo.setCurrentIndex(index)
            
        param_layout.addRow("输入尺寸:", self.size_combo)
        
        # 批处理大小
        self.batch_spin = QSpinBox()
        self.batch_spin.setRange(1, 64)
        self.batch_spin.setValue(self.config.get('batch_size', 16))
        param_layout.addRow("批处理大小:", self.batch_spin)
        
        layout.addWidget(param_group)
        
        # 添加保存按钮
        self.save_params_btn = QPushButton("保存参数")
        self.save_params_btn.clicked.connect(self.save_detection_params)
        layout.addWidget(self.save_params_btn)
        
        return widget
        
    def create_camera_tab(self):
        """创建摄像头控制标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 摄像头选择分组
        camera_group = QGroupBox("摄像头选择")
        camera_layout = QFormLayout(camera_group)
        
        # 摄像头列表
        self.camera_combo = QComboBox()
        self.camera_combo.addItem("默认摄像头", 0)
        self.camera_combo.addItem("USB摄像头1", 1)
        self.camera_combo.addItem("网络摄像头", "rtsp://admin:admin@192.168.1.100:554/stream")
        camera_layout.addRow("摄像头:", self.camera_combo)
        
        # 分辨率选择
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItem("320x240", (320, 240))
        self.resolution_combo.addItem("640x480", (640, 480))
        self.resolution_combo.addItem("1280x720", (1280, 720))
        self.resolution_combo.addItem("1920x1080", (1920, 1080))
        camera_layout.addRow("分辨率:", self.resolution_combo)
        
        # 帧率选择
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(1, 60)
        self.fps_spin.setValue(30)
        camera_layout.addRow("帧率:", self.fps_spin)
        
        layout.addWidget(camera_group)
        
        # 图像调整分组
        adjust_group = QGroupBox("图像调整")
        adjust_layout = QFormLayout(adjust_group)
        
        # 亮度调整
        self.brightness_slider = QSlider(Qt.Horizontal)
        self.brightness_slider.setRange(0, 100)
        self.brightness_slider.setValue(50)
        adjust_layout.addRow("亮度:", self.brightness_slider)
        
        # 对比度调整
        self.contrast_slider = QSlider(Qt.Horizontal)
        self.contrast_slider.setRange(0, 100)
        self.contrast_slider.setValue(50)
        adjust_layout.addRow("对比度:", self.contrast_slider)
        
        # 饱和度调整
        self.saturation_slider = QSlider(Qt.Horizontal)
        self.saturation_slider.setRange(0, 100)
        self.saturation_slider.setValue(50)
        adjust_layout.addRow("饱和度:", self.saturation_slider)
        
        layout.addWidget(adjust_group)
        
        # 添加应用按钮
        self.apply_camera_btn = QPushButton("应用设置")
        self.apply_camera_btn.clicked.connect(self.apply_camera_settings)
        layout.addWidget(self.apply_camera_btn)
        
        return widget
        
    def create_alert_tab(self):
        """创建告警控制标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 告警阈值分组
        threshold_group = QGroupBox("告警阈值设置")
        threshold_layout = QFormLayout(threshold_group)
        
        # 火灾告警阈值
        self.fire_threshold = QSlider(Qt.Horizontal)
        self.fire_threshold.setRange(50, 95)
        self.fire_threshold.setValue(75)
        self.fire_threshold.setTracking(True)
        self.fire_threshold.setTickPosition(QSlider.TicksBelow)
        threshold_layout.addRow("火灾告警阈值:", self.fire_threshold)
        
        # 动物告警阈值
        self.animal_threshold = QSlider(Qt.Horizontal)
        self.animal_threshold.setRange(50, 95)
        self.animal_threshold.setValue(70)
        self.animal_threshold.setTracking(True)
        self.animal_threshold.setTickPosition(QSlider.TicksBelow)
        threshold_layout.addRow("动物告警阈值:", self.animal_threshold)
        
        # 滑坡告警阈值
        self.landslide_threshold = QSlider(Qt.Horizontal)
        self.landslide_threshold.setRange(50, 95)
        self.landslide_threshold.setValue(80)
        self.landslide_threshold.setTracking(True)
        self.landslide_threshold.setTickPosition(QSlider.TicksBelow)
        threshold_layout.addRow("滑坡告警阈值:", self.landslide_threshold)
        
        # 病虫害告警阈值
        self.pest_threshold = QSlider(Qt.Horizontal)
        self.pest_threshold.setRange(50, 95)
        self.pest_threshold.setValue(70)
        self.pest_threshold.setTracking(True)
        self.pest_threshold.setTickPosition(QSlider.TicksBelow)
        threshold_layout.addRow("病虫害告警阈值:", self.pest_threshold)
        
        layout.addWidget(threshold_group)
        
        # 告警方式分组
        method_group = QGroupBox("告警方式")
        method_layout = QVBoxLayout(method_group)
        
        # 添加复选框
        self.ui_alert_check = QCheckBox("界面告警")
        self.ui_alert_check.setChecked(True)
        method_layout.addWidget(self.ui_alert_check)
        
        self.sound_alert_check = QCheckBox("声音告警")
        self.sound_alert_check.setChecked(True)
        method_layout.addWidget(self.sound_alert_check)
        
        self.sms_alert_check = QCheckBox("短信告警")
        self.sms_alert_check.setChecked(False)
        method_layout.addWidget(self.sms_alert_check)
        
        self.email_alert_check = QCheckBox("邮件告警")
        self.email_alert_check.setChecked(False)
        method_layout.addWidget(self.email_alert_check)
        
        layout.addWidget(method_group)
        
        # 添加应用按钮
        self.apply_alert_btn = QPushButton("应用设置")
        self.apply_alert_btn.clicked.connect(self.apply_alert_settings)
        layout.addWidget(self.apply_alert_btn)
        
        return widget
        
    @pyqtSlot(int)
    def update_conf_threshold(self, value):
        """更新置信度阈值显示"""
        self.conf_label.setText(f"{value / 100:.2f}")
        
    @pyqtSlot(int)
    def update_iou_threshold(self, value):
        """更新IOU阈值显示"""
        self.iou_label.setText(f"{value / 100:.2f}")
        
    @pyqtSlot()
    def save_detection_params(self):
        """保存检测参数"""
        # 获取参数
        conf_threshold = self.conf_slider.value() / 100
        iou_threshold = self.iou_slider.value() / 100
        image_size = self.size_combo.currentData()
        batch_size = self.batch_spin.value()
        
        # 更新配置
        self.config['conf_threshold'] = conf_threshold
        self.config['iou_threshold'] = iou_threshold
        self.config['image_size'] = image_size
        self.config['batch_size'] = batch_size
        
        # 保存检测任务
        self.config['enable_fire_detection'] = self.fire_check.isChecked()
        self.config['enable_animal_detection'] = self.animal_check.isChecked()
        self.config['enable_landslide_detection'] = self.landslide_check.isChecked()
        self.config['enable_pest_detection'] = self.pest_check.isChecked()
        
        # 保存到设置文件（实际项目中实现）
        print("检测参数已保存")
        
    @pyqtSlot()
    def apply_camera_settings(self):
        """应用摄像头设置"""
        # 获取参数
        camera_source = self.camera_combo.currentData()
        resolution = self.resolution_combo.currentData()
        fps = self.fps_spin.value()
        brightness = self.brightness_slider.value()
        contrast = self.contrast_slider.value()
        saturation = self.saturation_slider.value()
        
        # 更新配置
        self.config['camera_source'] = camera_source
        self.config['camera_resolution'] = resolution
        self.config['camera_fps'] = fps
        self.config['camera_brightness'] = brightness
        self.config['camera_contrast'] = contrast
        self.config['camera_saturation'] = saturation
        
        # 应用设置（实际项目中实现）
        print("摄像头设置已应用")
        
    @pyqtSlot()
    def apply_alert_settings(self):
        """应用告警设置"""
        # 获取参数
        fire_threshold = self.fire_threshold.value()
        animal_threshold = self.animal_threshold.value()
        landslide_threshold = self.landslide_threshold.value()
        pest_threshold = self.pest_threshold.value()
        
        # 获取告警方式
        alert_methods = []
        if self.ui_alert_check.isChecked():
            alert_methods.append('ui')
        if self.sound_alert_check.isChecked():
            alert_methods.append('sound')
        if self.sms_alert_check.isChecked():
            alert_methods.append('sms')
        if self.email_alert_check.isChecked():
            alert_methods.append('email')
            
        # 更新配置
        self.config['fire_alert_threshold'] = fire_threshold
        self.config['animal_alert_threshold'] = animal_threshold
        self.config['landslide_alert_threshold'] = landslide_threshold
        self.config['pest_alert_threshold'] = pest_threshold
        self.config['alert_methods'] = alert_methods
        
        # 应用设置（实际项目中实现）
        print("告警设置已应用")
        
    @pyqtSlot()
    def start_monitoring(self):
        """启动监测"""
        # 切换按钮状态
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        
        # 通知主窗口启动监测
        parent = self.parent()
        while parent:
            if hasattr(parent, 'start_monitoring'):
                parent.start_monitoring()
                break
            parent = parent.parent()
        
    @pyqtSlot()
    def stop_monitoring(self):
        """停止监测"""
        # 切换按钮状态
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
        # 通知主窗口停止监测
        parent = self.parent()
        while parent:
            if hasattr(parent, 'stop_monitoring'):
                parent.stop_monitoring()
                break
            parent = parent.parent() 