import os
import time
from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                            QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
                            QGroupBox, QToolBar, QAction, QMenu, QAbstractItemView, QMessageBox, QDialog, QProgressBar)
from PyQt5.QtCore import Qt, pyqtSlot, QSize, QTimer, QDateTime, pyqtSignal
from PyQt5.QtGui import QIcon, QColor, QBrush, QFont, QPixmap
import random

class AlertPanel(QWidget):
    """告警面板组件，显示各类灾害告警信息"""
    
    # 添加信号用于通知统计面板
    alert_added = pyqtSignal(str, str)  # 参数: alert_type, region
    alert_processed = pyqtSignal(str, str)  # 参数: alert_type, region - 新增信号用于通知告警已处理
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.alerts = []  # 保存所有告警
        self.current_filter = "all"  # 当前过滤类型
        self.current_severity = "all"  # 当前严重程度过滤
        
        # 从配置文件获取随机告警设置
        self.random_alert_config = config.get('random_alert', {
            'enabled': False,
            'interval': 5,
            'probability': 0.3,
            'types': ['fire', 'animal', 'landslide', 'forest_degradation', 'pest'],
            'locations': ['北部山区', '南部林区', '东部山脊', '西部谷地', '中央林场']
        })
        
        self.init_ui()
        
        # 设置自动更新定时器
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_alerts)
        self.update_timer.start(self.random_alert_config['interval'] * 1000)  # 转换为毫秒
        
    def init_ui(self):
        """初始化UI"""
        # 创建主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建工具栏
        toolbar = QHBoxLayout()
        
        # 添加标题
        title_label = QLabel("告警信息")
        title_label.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        title_label.setStyleSheet("color: #00e6e6; margin: 5px;")
        toolbar.addWidget(title_label)
        
        # 添加分隔符
        toolbar.addStretch(1)
        
        # 添加随机告警开关
        self.random_alert_btn = QPushButton(f"随机告警: {'开' if self.random_alert_config['enabled'] else '关'}")
        self.random_alert_btn.setCheckable(True)  # 使按钮可切换
        self.random_alert_btn.setChecked(self.random_alert_config['enabled'])  # 设置初始状态
        self.random_alert_btn.setFixedWidth(100)
        self.random_alert_btn.clicked.connect(self.toggle_random_alerts)
        self.random_alert_btn.setStyleSheet("""
            QPushButton {
                background-color: #666666;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton:checked {
                background-color: #4CAF50;
            }
        """)
        toolbar.addWidget(self.random_alert_btn)
        
        # 添加过滤下拉框
        self.filter_combo = QComboBox()
        self.filter_combo.addItem("全部告警", "all")
        self.filter_combo.addItem("火灾告警", "fire")
        self.filter_combo.addItem("动物告警", "animal")
        self.filter_combo.addItem("滑坡告警", "landslide")
        self.filter_combo.addItem("森林退化告警", "forest")
        self.filter_combo.addItem("病虫害告警", "pest")
        self.filter_combo.currentIndexChanged.connect(self.filter_alerts)
        toolbar.addWidget(QLabel("过滤: "))
        toolbar.addWidget(self.filter_combo)
        
        # 添加严重程度过滤下拉框
        self.severity_combo = QComboBox()
        self.severity_combo.addItem("所有等级", "all")
        self.severity_combo.addItem("高", "high")
        self.severity_combo.addItem("中", "medium")
        self.severity_combo.addItem("低", "low")
        self.severity_combo.currentIndexChanged.connect(self.filter_alerts)
        toolbar.addWidget(QLabel("严重程度: "))
        toolbar.addWidget(self.severity_combo)
        
        # 添加按钮
        self.clear_btn = QPushButton("清空")
        self.clear_btn.setIcon(QIcon(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'clear.png')))
        self.clear_btn.clicked.connect(self.clear_alerts)
        toolbar.addWidget(self.clear_btn)
        
        # 添加工具栏到布局
        layout.addLayout(toolbar)
        
        # 创建表格
        self.alert_table = QTableWidget()
        self.alert_table.setColumnCount(6)
        self.alert_table.setHorizontalHeaderLabels(["时间", "类型", "位置", "详情", "等级", "操作"])
        self.alert_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.alert_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.alert_table.setAlternatingRowColors(True)
        self.alert_table.setStyleSheet("alternate-background-color: #0c1e32; background-color: #081a2e; color: white; "
                                      "QHeaderView::section { background-color: #15253a; color: white; padding: 4px; "
                                      "border: 1px solid #1e3a5a; font-weight: bold; }"
                                      "QTableView { gridline-color: #1e3a5a; border: 1px solid #1e3a5a; }"
                                      "QTableView::item:selected { background-color: #2a4a6a; }")
        
        # 设置列宽
        self.alert_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.alert_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.alert_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.alert_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.alert_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.alert_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        
        # 双击行处理
        self.alert_table.cellDoubleClicked.connect(self.show_alert_detail)
        
        # 添加表格到布局
        layout.addWidget(self.alert_table)
        
        # 设置最小高度
        self.setMinimumHeight(150)
        
    def add_alert(self, alert):
        """添加告警到列表和表格"""
        # 添加到告警列表
        self.alerts.append(alert)
        
        # 发出信号通知统计面板
        print(f"发送告警信号: 类型={alert['type']}, 区域={alert['location']}")
        self.alert_added.emit(alert['type'], alert['location'])
        
        # 检查是否符合当前过滤条件
        type_match = self.current_filter == "all" or alert['type'] == self.current_filter
        severity_match = self.current_severity == "all" or alert['level'] == self.current_severity
        
        if type_match and severity_match:
            self.add_filtered_alert(alert)
        
    def get_alert_type_name(self, alert_type):
        """获取告警类型的中文名称
        
        Args:
            alert_type (str): 告警类型
            
        Returns:
            str: 告警类型的中文名称
        """
        type_names = {
            "fire": "森林火灾",
            "animal": "野生动物异常",
            "landslide": "山体滑坡",
            "forest_degradation": "森林退化",
            "pest": "病虫害"
        }
        return type_names.get(alert_type, "未知类型")
        
    def get_alert_type_color(self, alert_type):
        """获取告警类型显示颜色"""
        type_colors = {
            'fire': QColor(255, 200, 200),  # 红色
            'animal': QColor(200, 255, 200),  # 绿色
            'landslide': QColor(200, 200, 255),  # 蓝色
            'pest': QColor(230, 190, 255)  # 紫色
        }
        return type_colors.get(alert_type, QColor(240, 240, 240))
        
    def get_alert_level_name(self, level):
        """获取告警等级的中文名称
        
        Args:
            level (int): 告警等级
            
        Returns:
            str: 告警等级的中文名称
        """
        level_names = {
            1: "一级 (紧急)",
            2: "二级 (高危)",
            3: "三级 (中危)",
            4: "四级 (低危)",
            5: "五级 (提示)"
        }
        return level_names.get(level, "未知等级")
        
    def get_alert_level_color(self, level):
        """获取告警等级显示颜色"""
        level_colors = {
            'high': QColor(255, 100, 100),  # 红色
            'medium': QColor(255, 200, 100),  # 橙色
            'low': QColor(200, 200, 200),  # 灰色
            'processed': QColor(100, 220, 100)  # 绿色，表示已处理
        }
        return level_colors.get(level, QColor(240, 240, 240))
        
    @pyqtSlot(int)
    def filter_alerts(self, index):
        """过滤告警"""
        # 获取当前过滤类型
        self.current_filter = self.filter_combo.currentData()
        self.current_severity = self.severity_combo.currentData()
        
        # 清空表格
        self.alert_table.setRowCount(0)
        
        # 重新添加符合条件的告警
        for alert in self.alerts:
            type_match = self.current_filter == "all" or alert['type'] == self.current_filter
            severity_match = self.current_severity == "all" or alert['level'] == self.current_severity
            
            if type_match and severity_match:
                self.add_filtered_alert(alert)
                
    def add_filtered_alert(self, alert):
        """添加过滤后的告警到表格（不添加到告警列表）"""
        row = self.alert_table.rowCount()
        self.alert_table.insertRow(row)
        
        # 设置单元格内容
        self.alert_table.setItem(row, 0, QTableWidgetItem(alert['time']))
        
        # 根据类型设置显示名称和颜色
        type_item = QTableWidgetItem(self.get_alert_type_name(alert['type']))
        type_item.setData(Qt.UserRole, alert['type'])
        type_item.setBackground(self.get_alert_type_color(alert['type']))
        self.alert_table.setItem(row, 1, type_item)
        
        self.alert_table.setItem(row, 2, QTableWidgetItem(alert['location']))
        self.alert_table.setItem(row, 3, QTableWidgetItem(alert['detail']))
        
        # 根据等级设置显示名称和颜色
        level_item = QTableWidgetItem(self.get_alert_level_name(alert['level']))
        level_item.setBackground(self.get_alert_level_color(alert['level']))
        self.alert_table.setItem(row, 4, level_item)
        
        # 操作按钮
        btn_cell = QWidget()
        btn_layout = QHBoxLayout(btn_cell)
        btn_layout.setContentsMargins(2, 2, 2, 2)
        
        details_btn = QPushButton("详情")
        details_btn.setFixedWidth(60)
        details_btn.clicked.connect(lambda _, a=alert: self.show_alert_details(a))
        
        handle_btn = QPushButton("处理")
        handle_btn.setFixedWidth(60)
        if alert['level'] == 'high':
            handle_btn.setEnabled(False)
        handle_btn.clicked.connect(lambda _, r=row: self.handle_alert(r))
        
        btn_layout.addWidget(details_btn)
        btn_layout.addWidget(handle_btn)
        btn_cell.setLayout(btn_layout)
        
        self.alert_table.setCellWidget(row, 5, btn_cell)
        
        # 自动滚动到最新行
        self.alert_table.scrollToItem(self.alert_table.item(row, 0))
        
    @pyqtSlot()
    def clear_alerts(self):
        """清空告警"""
        self.alerts = []
        self.alert_table.setRowCount(0)
        
    @pyqtSlot(int, int)
    def show_alert_detail(self, row, column):
        """显示告警详情（双击行时触发）"""
        # 实际项目中可以打开告警详情对话框
        print(f"显示第 {row} 行告警详情")
        
    def show_alert_details(self, alert):
        """显示告警详情"""
        # 防止重复触发
        current_time = datetime.now()
        if hasattr(self, 'last_detail_time'):
            if (current_time - self.last_detail_time).total_seconds() < 1:
                return
        self.last_detail_time = current_time
        
        msg = QMessageBox()
        msg.setWindowTitle("预警详情")
        
        details = f"""
        时间：{alert['time']}
        类型：{self.get_alert_type_name(alert['type'])}
        位置：{alert['location']}
        严重程度：{alert['level']}
        详细信息：{alert['detail']}
        """
        
        msg.setText(details)
        msg.setIcon(QMessageBox.Information)
        msg.exec_()
        
    def handle_alert(self, row):
        """处理告警"""
        # 防止重复处理
        current_time = datetime.now()
        if hasattr(self, 'last_handle_time'):
            if (current_time - self.last_handle_time).total_seconds() < 1:
                return
        self.last_handle_time = current_time
        
        # 获取告警数据
        alert = self.alerts[row]
        
        # 向护林员发送通知
        self.send_notification_to_ranger(alert)
        
        # 降低告警等级 
        original_level = alert['level']
        if alert['level'] == 'high':
            alert['level'] = 'medium'
        elif alert['level'] == 'medium':
            alert['level'] = 'low'
        elif alert['level'] == 'low':
            alert['level'] = 'processed'  # 添加'processed'状态表示已完全处理
        
        # 更新UI显示
        level_name = self.get_alert_level_name(alert['level'])
        level_color = self.get_alert_level_color(alert['level'])
        
        level_item = QTableWidgetItem(level_name)
        level_item.setBackground(level_color)
        self.alert_table.setItem(row, 4, level_item)
        
        # 如果已完全处理，禁用处理按钮
        if alert['level'] == 'processed':
            cell_widget = self.alert_table.cellWidget(row, 5)
            if cell_widget:
                for child in cell_widget.children():
                    if isinstance(child, QPushButton) and child.text() == "处理":
                        child.setEnabled(False)
                        child.setText("已处理")
                        break
        
        # 发送告警已处理信号
        print(f"发送告警处理信号: 类型={alert['type']}, 区域={alert['location']}")
        self.alert_processed.emit(alert['type'], alert['location'])
        
        # 滚动到当前行
        self.alert_table.scrollToItem(self.alert_table.item(row, 0))
        
    def send_notification_to_ranger(self, alert):
        """向护林员发送通知
        
        Args:
            alert (dict): 告警信息
        """
        from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                                   QFrame, QSpacerItem, QSizePolicy, QProgressBar)
        from PyQt5.QtGui import QFont, QPixmap, QIcon
        from PyQt5.QtCore import Qt, QTimer
        import os
        
        # 根据告警类型确定应联系的组织
        alert_type = alert['type']
        organization = self.get_responsible_organization(alert_type)
        
        # 创建自定义对话框
        dialog = QDialog(self)
        dialog.setWindowTitle(f"通知{organization}")
        dialog.setMinimumWidth(500)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
            }
            QLabel {
                color: #333333;
            }
            QPushButton {
                background-color: #2196f3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #0d8bf2;
            }
            QPushButton:pressed {
                background-color: #0a75cf;
            }
            QFrame {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                background-color: white;
            }
            QProgressBar {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                background-color: #f0f0f0;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4caf50;
                border-radius: 3px;
            }
        """)
        
        # 创建布局
        layout = QVBoxLayout(dialog)
        
        # 标题区域
        title_layout = QHBoxLayout()
        
        # 尝试根据告警类型添加图标
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', f"{alert_type}.png")
        icon_label = QLabel()
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path).scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(pixmap)
        else:
            # 使用默认警告图标
            icon_label.setText("⚠️")
            icon_label.setFont(QFont("Arial", 24))
        
        icon_label.setFixedSize(60, 60)
        icon_label.setAlignment(Qt.AlignCenter)
        title_layout.addWidget(icon_label)
        
        # 标题文本
        title_text = QLabel("正在发送告警通知...")
        title_text.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        title_layout.addWidget(title_text, 1)
        
        layout.addLayout(title_layout)
        
        # 进度条
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 100)
        progress_bar.setValue(0)
        progress_bar.setFixedHeight(20)
        layout.addWidget(progress_bar)
        
        # 状态标签
        status_label = QLabel("正在连接通信系统...")
        status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(status_label)
        
        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)
        
        # 信息面板
        info_frame = QFrame()
        info_layout = QVBoxLayout(info_frame)
        
        # 添加告警信息
        info_layout.addWidget(self.create_info_row("告警类型", self.get_alert_type_name(alert_type)))
        info_layout.addWidget(self.create_info_row("告警区域", alert['location']))
        info_layout.addWidget(self.create_info_row("告警等级", self.get_alert_level_name(alert['level'])))
        info_layout.addWidget(self.create_info_row("详细信息", alert['detail']))
        info_layout.addWidget(self.create_info_row("时间", alert['time']))
        info_layout.addWidget(self.create_info_row("接收组织", organization))
        
        layout.addWidget(info_frame)
        
        # 添加消息
        message_label = QLabel("")
        message_label.setWordWrap(True)
        message_label.setAlignment(Qt.AlignCenter)
        message_label.setFont(QFont("Microsoft YaHei", 10))
        message_label.setStyleSheet("color: #666666; margin: 10px;")
        layout.addWidget(message_label)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # 禁用关闭按钮，等待通知发送完成
        close_button = QPushButton("关闭")
        close_button.setFixedWidth(120)
        close_button.setEnabled(False)  # 先禁用按钮
        close_button.clicked.connect(dialog.accept)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        
        # 设置进度条更新的定时器
        progress = 0
        timer = QTimer(dialog)
        
        # 进度模拟阶段
        stages = [
            (10, "正在连接通信系统..."),
            (30, f"正在向{organization}发送告警信息..."),
            (60, f"等待{organization}确认接收..."),
            (90, f"{organization}已确认接收告警信息"),
            (100, f"通知流程完成，{organization}将立即处理")
        ]
        current_stage = 0
        
        def update_progress():
            nonlocal progress, current_stage
            
            # 更新进度条
            progress += 5
            if progress > 100:
                progress = 100
                
            progress_bar.setValue(progress)
            
            # 检查是否需要更新阶段
            if current_stage < len(stages) and progress >= stages[current_stage][0]:
                status_label.setText(stages[current_stage][1])
                current_stage += 1
                
            # 通知完成时
            if progress >= 100:
                timer.stop()
                title_text.setText(f"已向{organization}发送告警通知")
                message_label.setText(f"相关{organization}已接收通知，并将前往现场处理。\n系统会持续跟踪处理进度，直至告警解除。")
                close_button.setEnabled(True)  # 启用关闭按钮
                
                # 在控制台打印日志
                print(f"已向{organization}发送告警通知: {alert_type} - {alert['location']}")
                
        # 启动定时器
        timer.timeout.connect(update_progress)
        timer.start(150)  # 每150毫秒更新一次
        
        # 显示对话框
        dialog.exec_()
        
    def create_info_row(self, label_text, value_text):
        """创建信息行
        
        Args:
            label_text (str): 标签文本
            value_text (str): 值文本
            
        Returns:
            QWidget: 包含标签和值的行
        """
        from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel
        from PyQt5.QtGui import QFont
        from PyQt5.QtCore import Qt
        
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 5, 0, 5)
        
        label = QLabel(label_text + ":")
        label.setFixedWidth(80)
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        label.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        
        value = QLabel(value_text)
        value.setWordWrap(True)
        value.setFont(QFont("Microsoft YaHei", 10))
        value.setStyleSheet("color: #333333;")
        
        layout.addWidget(label)
        layout.addWidget(value, 1)
        
        return row
        
    def get_responsible_organization(self, alert_type):
        """根据告警类型获取负责组织
        
        Args:
            alert_type (str): 告警类型
            
        Returns:
            str: 负责组织名称
        """
        organizations = {
            "fire": "森林消防队",
            "animal": "野生动物保护中心",
            "landslide": "地质灾害应急中心",
            "forest_degradation": "森林修复小组",
            "pest": "病虫害防治站"
        }
        return organizations.get(alert_type, "森林管理部门")
        
    def toggle_random_alerts(self):
        """切换随机告警功能"""
        self.random_alert_config['enabled'] = not self.random_alert_config['enabled']
        self.random_alert_btn.setText(f"随机告警: {'开' if self.random_alert_config['enabled'] else '关'}")
        
        # 立即生成一个告警作为反馈
        if self.random_alert_config['enabled']:
            self.generate_random_alert()
            
    def generate_random_alert(self):
        """生成一个随机告警"""
        # 根据当前过滤类型选择告警类型
        if self.current_filter != "all":
            alert_type = self.current_filter
        else:
            alert_type = random.choice(self.random_alert_config['types'])
            
        # 根据当前严重程度过滤选择告警等级
        if self.current_severity != "all":
            alert_level = self.current_severity
        else:
            alert_level = random.choice(['high', 'medium', 'low'])
            
        alert_location = random.choice(self.random_alert_config['locations'])
        
        print(f"告警面板生成新告警: 类型={alert_type}, 区域={alert_location}")
        
        # 为病虫害生成特殊的详情
        if alert_type == 'pest':
            pest_types = ['松毛虫', '美国白蛾', '落叶松毛虫', '杨树食叶害虫', '松材线虫病']
            pest_type = random.choice(pest_types)
            area = random.randint(10, 200)
            detail = f'检测到{pest_type}病虫害，受灾面积约{area}平方米'
        else:
            detail = f'新检测到的告警 #{len(self.alerts) + 1}'
        
        alert = {
            'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'type': alert_type,
            'location': alert_location,
            'detail': detail,
            'level': alert_level
        }
        
        self.add_alert(alert)
        
    def update_alerts(self):
        """更新告警（由定时器调用）"""
        # 如果启用了随机告警，则有机会生成新告警
        if self.random_alert_config['enabled'] and random.random() < self.random_alert_config['probability']:
            self.generate_random_alert()
        
        # 更新UI显示
        self.alert_table.viewport().update() 