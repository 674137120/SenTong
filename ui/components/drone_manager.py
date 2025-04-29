import os
import cv2
import numpy as np
import random
from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QComboBox, QToolBar, QAction, 
                            QGridLayout, QFrame, QSplitter, QFileDialog,
                            QTableWidget, QTableWidgetItem, QHeaderView,
                            QAbstractItemView, QGroupBox, QTabWidget)
from PyQt5.QtCore import Qt, QTimer, pyqtSlot, pyqtSignal, QSize, QRect, QThread
from PyQt5.QtGui import QImage, QPixmap, QIcon, QPainter, QPen, QColor, QFont, QBrush

class DroneSimulator(QThread):
    """无人机模拟器，用于模拟无人机状态和视频流"""
    update_frame = pyqtSignal(int, np.ndarray)  # 发送无人机ID和视频帧
    update_status = pyqtSignal(int, dict)  # 发送无人机ID和状态信息
    update_detection = pyqtSignal(int, list)  # 发送无人机ID和检测结果
    
    def __init__(self, drone_id, drone_type="DJI Mavic Air 2"):
        super().__init__()
        self.drone_id = drone_id
        self.drone_type = drone_type
        self.running = False
        self.battery = 100
        self.altitude = 120  # 初始高度，米
        self.speed = 0
        self.gps = {"lat": 39.916527 + random.uniform(-0.01, 0.01), 
                    "lng": 116.397128 + random.uniform(-0.01, 0.01)}
        self.signal = 95
        self.status = "待命"
        
        # 选择一个示例视频作为无人机视频源
        self.video_files = [
            "resources/videos/drone_forest_1.mp4",
            "resources/videos/drone_forest_2.mp4",
            "resources/videos/drone_forest_3.mp4"
        ]
        # 使用无人机ID作为随机种子选择视频源，确保每个无人机有不同的视频
        random.seed(drone_id)
        self.video_source = "resources/videos/forest_fire.mp4"  # 默认使用一个通用视频
        
        # 初始化帧计数
        self.frame_count = 0
        
    def run(self):
        """运行无人机模拟器"""
        self.running = True
        cap = cv2.VideoCapture(self.video_source)
        
        if not cap.isOpened():
            # 无法打开视频，使用生成的图像
            print(f"无法打开视频源，使用生成图像: {self.video_source}")
            while self.running:
                # 生成模拟画面
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
                # 添加一些背景
                frame[:] = (30, 50, 30)  # 深绿色背景
                # 添加一些文字
                text = f"无人机 #{self.drone_id} - 信号丢失"
                cv2.putText(frame, text, (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                
                # 添加当前状态信息
                info_text = f"电池: {self.battery}% | 高度: {self.altitude}m | 信号: {self.signal}%"
                cv2.putText(frame, info_text, (50, 280), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 1)
                
                # 更新无人机状态
                self.update_drone_status()
                
                # 发送帧和状态
                self.update_frame.emit(self.drone_id, frame)
                self.update_status.emit(self.drone_id, self.get_status())
                
                # 控制帧率
                self.msleep(100)
        else:
            while self.running:
                ret, frame = cap.read()
                if not ret:
                    # 视频结束，从头开始
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                
                # 添加无人机信息叠加层
                frame = self.add_drone_info(frame)
                
                # 每隔一段时间生成模拟检测结果
                self.frame_count += 1
                if self.frame_count % 30 == 0:  # 每30帧生成一次检测结果
                    detections = self.generate_mock_detection(frame)
                    self.update_detection.emit(self.drone_id, detections)
                    # 将检测结果绘制在画面上
                    frame = self.draw_detections(frame, detections)
                
                # 更新无人机状态
                self.update_drone_status()
                
                # 发送帧和状态
                self.update_frame.emit(self.drone_id, frame)
                self.update_status.emit(self.drone_id, self.get_status())
                
                # 控制帧率
                self.msleep(50)
            
            cap.release()
    
    def stop(self):
        """停止无人机模拟器"""
        self.running = False
        self.wait()
    
    def update_drone_status(self):
        """更新无人机状态"""
        # 模拟电池消耗
        self.battery = max(0, self.battery - random.uniform(0.01, 0.05))
        
        # 模拟高度变化
        if random.random() < 0.3:
            self.altitude += random.uniform(-1, 1)
            self.altitude = max(30, min(200, self.altitude))
        
        # 模拟速度变化
        self.speed = random.uniform(0, 8)
        
        # 模拟GPS位置变化
        self.gps["lat"] += random.uniform(-0.0001, 0.0001)
        self.gps["lng"] += random.uniform(-0.0001, 0.0001)
        
        # 模拟信号强度变化
        if random.random() < 0.2:
            self.signal += random.uniform(-2, 1)
            self.signal = max(60, min(100, self.signal))
    
    def get_status(self):
        """获取无人机状态信息"""
        return {
            "id": self.drone_id,
            "type": self.drone_type,
            "battery": self.battery,
            "altitude": self.altitude,
            "speed": self.speed,
            "gps": self.gps,
            "signal": self.signal,
            "status": self.status,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def add_drone_info(self, frame):
        """在视频帧上添加无人机信息"""
        height, width = frame.shape[:2]
        
        # 添加半透明的顶部信息栏
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (width, 40), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame, 0)
        
        # 添加无人机ID和类型
        cv2.putText(frame, f"无人机 #{self.drone_id} | {self.drone_type}", 
                   (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        # 添加电池和GPS信息
        battery_text = f"电池: {int(self.battery)}%"
        battery_color = (0, 255, 0) if self.battery > 30 else (0, 165, 255) if self.battery > 15 else (0, 0, 255)
        cv2.putText(frame, battery_text, (width - 300, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, battery_color, 1)
        
        gps_text = f"GPS: {self.gps['lat']:.4f}, {self.gps['lng']:.4f}"
        cv2.putText(frame, gps_text, (width - 180, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        # 添加时间戳
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, timestamp, (width - 180, height - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # 添加高度和速度信息
        altitude_text = f"高度: {int(self.altitude)}m"
        cv2.putText(frame, altitude_text, (10, height - 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        speed_text = f"速度: {self.speed:.1f}m/s"
        cv2.putText(frame, speed_text, (10, height - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return frame
    
    def generate_mock_detection(self, frame):
        """生成模拟检测结果"""
        height, width = frame.shape[:2]
        
        # 随机决定是否生成检测结果
        if random.random() < 0.3:  # 30%的概率生成检测
            detection_type = random.choice(['fire', 'animal', 'landslide', 'pest'])
            
            # 根据检测类型设置标签
            label_map = {
                'fire': '火灾',
                'animal': '野生动物',
                'landslide': '滑坡',
                'pest': '病虫害'
            }
            
            # 对于病虫害类型，随机选择具体的病虫害种类
            pest_types = ['松毛虫', '美国白蛾', '落叶松毛虫', '杨树食叶害虫', '松材线虫病']
            pest_subtypes = ['轻度', '中度', '重度']
            
            # 随机位置
            x1 = random.randint(50, width - 150)
            y1 = random.randint(50, height - 150)
            w = random.randint(50, 150)
            h = random.randint(50, 150)
            x2 = x1 + w
            y2 = y1 + h
            
            # 随机置信度
            confidence = random.uniform(0.65, 0.95)
            
            # 如果是病虫害类型，创建更详细的标签
            if detection_type == 'pest':
                pest_type = random.choice(pest_types)
                pest_subtype = random.choice(pest_subtypes)
                return [{
                    'task': detection_type,
                    'class': 0,
                    'label': f"{label_map[detection_type]}-{pest_type}({pest_subtype})",
                    'confidence': confidence,
                    'bbox': [x1, y1, x2, y2],
                    'subtype': pest_type,
                    'severity': pest_subtype
                }]
            else:
                return [{
                    'task': detection_type,
                    'class': 0,
                    'label': label_map[detection_type],
                    'confidence': confidence,
                    'bbox': [x1, y1, x2, y2]
                }]
        else:
            return []  # 没有检测结果
    
    def draw_detections(self, frame, detections):
        """在帧上绘制检测结果"""
        for det in detections:
            # 获取边界框和标签
            x1, y1, x2, y2 = [int(c) for c in det['bbox']]
            label = f"{det['label']} {det['confidence']:.2f}"
            
            # 根据任务选择颜色
            if det['task'] == 'fire':
                color = (0, 0, 255)  # 红色
            elif det['task'] == 'animal':
                color = (0, 255, 0)  # 绿色
            elif det['task'] == 'landslide':
                color = (255, 0, 0)  # 蓝色
            elif det['task'] == 'pest':
                color = (128, 0, 128)  # 紫色
            else:
                color = (255, 255, 0)  # 青色
                
            # 绘制边界框
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            # 绘制标签背景
            text_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
            cv2.rectangle(frame, (x1, y1 - text_size[1] - 5), (x1 + text_size[0], y1), color, -1)
            
            # 绘制标签
            cv2.putText(frame, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            
            # 如果是病虫害，绘制额外信息
            if det['task'] == 'pest' and 'severity' in det:
                # 在框的上方显示严重程度
                severity_text = f"严重程度: {det['severity']}"
                cv2.putText(frame, severity_text, (x1, y1 - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return frame

class DroneManager(QWidget):
    """无人机管理组件，用于管理多个无人机，显示视频流和状态"""
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.drones = {}  # 存储无人机模拟器，key为无人机ID
        self.drone_frames = {}  # 存储无人机视频帧
        self.drone_status = {}  # 存储无人机状态
        self.drone_detections = {}  # 存储无人机检测结果
        
        self.init_ui()
        
        # 创建自动更新定时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_drone_display)
        self.timer.start(200)  # 每200毫秒更新一次显示
        
    def init_ui(self):
        """初始化UI"""
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建工具栏
        toolbar_layout = QHBoxLayout()
        
        # 添加标题
        title_label = QLabel("无人机管理")
        title_label.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        title_label.setStyleSheet("color: white; margin: 5px;")
        toolbar_layout.addWidget(title_label)
        
        # 添加空白占位
        toolbar_layout.addStretch(1)
        
        # 添加无人机类型选择
        self.drone_type_combo = QComboBox()
        self.drone_type_combo.addItem("DJI Mavic Air 2")
        self.drone_type_combo.addItem("DJI Phantom 4")
        self.drone_type_combo.addItem("DJI Inspire 2")
        self.drone_type_combo.addItem("Autel EVO II")
        toolbar_layout.addWidget(QLabel("无人机类型:"))
        toolbar_layout.addWidget(self.drone_type_combo)
        
        # 添加添加无人机按钮
        self.add_drone_btn = QPushButton("添加无人机")
        self.add_drone_btn.setIcon(QIcon(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'add.png')))
        self.add_drone_btn.clicked.connect(self.add_drone)
        toolbar_layout.addWidget(self.add_drone_btn)
        
        # 添加删除无人机按钮
        self.remove_drone_btn = QPushButton("删除无人机")
        self.remove_drone_btn.setIcon(QIcon(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'remove.png')))
        self.remove_drone_btn.clicked.connect(self.remove_drone)
        toolbar_layout.addWidget(self.remove_drone_btn)
        
        main_layout.addLayout(toolbar_layout)
        
        # 创建分割器
        splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(splitter, 1)
        
        # 创建无人机视图区域 - 使用标签页
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab_widget.setStyleSheet("QTabWidget::pane { border: 0; } QTabBar::tab { background-color: #102040; color: white; padding: 6px 12px; margin-right: 2px; } QTabBar::tab:selected { background-color: #1a3a5a; }")
        splitter.addWidget(self.tab_widget)
        
        # 创建无人机控制面板
        control_panel = QWidget()
        control_layout = QVBoxLayout(control_panel)
        
        # 添加无人机状态表格
        self.status_table = QTableWidget()
        self.status_table.setColumnCount(9)
        self.status_table.setHorizontalHeaderLabels(["ID", "类型", "电池", "高度", "速度", "经度", "纬度", "信号", "状态"])
        self.status_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.status_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.status_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.status_table.setAlternatingRowColors(True)
        self.status_table.setStyleSheet("alternate-background-color: #0c1e32; background-color: #081a2e; color: white; "
                                      "QHeaderView::section { background-color: #15253a; color: white; padding: 4px; "
                                      "border: 1px solid #1e3a5a; font-weight: bold; }")
        control_layout.addWidget(self.status_table)
        
        # 添加按钮栏
        btn_layout = QHBoxLayout()
        
        # 起飞按钮
        self.takeoff_btn = QPushButton("起飞")
        self.takeoff_btn.clicked.connect(self.takeoff_drone)
        btn_layout.addWidget(self.takeoff_btn)
        
        # 降落按钮
        self.land_btn = QPushButton("降落")
        self.land_btn.clicked.connect(self.land_drone)
        btn_layout.addWidget(self.land_btn)
        
        # 返航按钮
        self.return_btn = QPushButton("返航")
        self.return_btn.clicked.connect(self.return_drone)
        btn_layout.addWidget(self.return_btn)
        
        # 停止按钮
        self.stop_btn = QPushButton("紧急停止")
        self.stop_btn.setStyleSheet("background-color: #8b0000; color: white;")
        self.stop_btn.clicked.connect(self.emergency_stop_drone)
        btn_layout.addWidget(self.stop_btn)
        
        control_layout.addLayout(btn_layout)
        
        splitter.addWidget(control_panel)
        
        # 设置分割器比例
        splitter.setSizes([int(self.height() * 0.7), int(self.height() * 0.3)])
        
        # 添加一些初始无人机
        QTimer.singleShot(500, self.add_initial_drones)
    
    def add_initial_drones(self):
        """添加初始无人机"""
        for i in range(3):  # 添加3个初始无人机
            self.add_drone()
    
    def add_drone(self):
        """添加一个无人机"""
        # 生成新的无人机ID
        drone_id = len(self.drones) + 1
        drone_type = self.drone_type_combo.currentText()
        
        # 创建无人机模拟器
        drone = DroneSimulator(drone_id, drone_type)
        drone.update_frame.connect(self.update_drone_frame)
        drone.update_status.connect(self.update_drone_status)
        drone.update_detection.connect(self.update_drone_detection)
        drone.start()
        
        # 存储无人机
        self.drones[drone_id] = drone
        
        # 创建视频显示标签页
        drone_tab = QWidget()
        tab_layout = QVBoxLayout(drone_tab)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建视频帧标签
        frame_label = QLabel()
        frame_label.setAlignment(Qt.AlignCenter)
        frame_label.setMinimumSize(640, 480)
        frame_label.setStyleSheet("background-color: black;")
        tab_layout.addWidget(frame_label)
        
        # 添加标签页
        self.tab_widget.addTab(drone_tab, f"无人机 #{drone_id}")
        
        # 切换到新标签页
        self.tab_widget.setCurrentIndex(self.tab_widget.count() - 1)
        
        # 初始化视频帧
        self.drone_frames[drone_id] = frame_label
        
        # 更新状态表格
        self.update_status_table()
    
    def remove_drone(self):
        """移除选中的无人机"""
        # 获取当前选中的标签页
        current_index = self.tab_widget.currentIndex()
        if current_index >= 0:
            # 获取无人机ID
            drone_id = int(self.tab_widget.tabText(current_index).split("#")[1])
            
            # 停止无人机模拟器
            if drone_id in self.drones:
                self.drones[drone_id].stop()
                del self.drones[drone_id]
            
            # 移除视频帧
            if drone_id in self.drone_frames:
                del self.drone_frames[drone_id]
            
            # 移除状态
            if drone_id in self.drone_status:
                del self.drone_status[drone_id]
            
            # 移除检测结果
            if drone_id in self.drone_detections:
                del self.drone_detections[drone_id]
            
            # 移除标签页
            self.tab_widget.removeTab(current_index)
            
            # 更新状态表格
            self.update_status_table()
    
    def update_drone_frame(self, drone_id, frame):
        """更新无人机视频帧"""
        if drone_id in self.drone_frames:
            # 转换为QImage并显示
            height, width, channels = frame.shape
            bytes_per_line = channels * width
            q_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
            self.drone_frames[drone_id].setPixmap(QPixmap.fromImage(q_image).scaled(
                self.drone_frames[drone_id].width(), 
                self.drone_frames[drone_id].height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            ))
    
    def update_drone_status(self, drone_id, status):
        """更新无人机状态"""
        self.drone_status[drone_id] = status
    
    def update_drone_detection(self, drone_id, detections):
        """更新无人机检测结果"""
        self.drone_detections[drone_id] = detections
        
        # 如果有检测结果，可以向主窗口发送告警
        if detections and hasattr(self.parent(), 'alert_panel'):
            for det in detections:
                # 构造告警信息
                alert = {
                    'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'type': det['task'],
                    'location': f"无人机 #{drone_id} 位置",
                    'detail': f"检测到{det['label']}，置信度: {det['confidence']:.2f}",
                    'level': 'high' if det['confidence'] > 0.85 else 'medium'
                }
                # 向告警面板添加告警
                self.parent().alert_panel.add_alert(alert)
    
    def update_drone_display(self):
        """更新无人机显示和状态表格"""
        self.update_status_table()
    
    def update_status_table(self):
        """更新状态表格"""
        self.status_table.setRowCount(0)
        
        for drone_id, status in self.drone_status.items():
            row = self.status_table.rowCount()
            self.status_table.insertRow(row)
            
            # 设置ID
            self.status_table.setItem(row, 0, QTableWidgetItem(str(drone_id)))
            
            # 设置类型
            self.status_table.setItem(row, 1, QTableWidgetItem(status['type']))
            
            # 设置电池
            battery_item = QTableWidgetItem(f"{int(status['battery'])}%")
            if status['battery'] > 30:
                battery_item.setForeground(QBrush(QColor(0, 255, 0)))
            elif status['battery'] > 15:
                battery_item.setForeground(QBrush(QColor(255, 165, 0)))
            else:
                battery_item.setForeground(QBrush(QColor(255, 0, 0)))
            self.status_table.setItem(row, 2, battery_item)
            
            # 设置高度
            self.status_table.setItem(row, 3, QTableWidgetItem(f"{int(status['altitude'])}m"))
            
            # 设置速度
            self.status_table.setItem(row, 4, QTableWidgetItem(f"{status['speed']:.1f}m/s"))
            
            # 设置经度
            self.status_table.setItem(row, 5, QTableWidgetItem(f"{status['gps']['lng']:.6f}"))
            
            # 设置纬度
            self.status_table.setItem(row, 6, QTableWidgetItem(f"{status['gps']['lat']:.6f}"))
            
            # 设置信号
            signal_item = QTableWidgetItem(f"{int(status['signal'])}%")
            if status['signal'] > 80:
                signal_item.setForeground(QBrush(QColor(0, 255, 0)))
            elif status['signal'] > 60:
                signal_item.setForeground(QBrush(QColor(255, 165, 0)))
            else:
                signal_item.setForeground(QBrush(QColor(255, 0, 0)))
            self.status_table.setItem(row, 7, signal_item)
            
            # 设置状态
            self.status_table.setItem(row, 8, QTableWidgetItem(status['status']))
    
    def takeoff_drone(self):
        """起飞选中的无人机"""
        selected_rows = self.status_table.selectionModel().selectedRows()
        for index in selected_rows:
            drone_id = int(self.status_table.item(index.row(), 0).text())
            if drone_id in self.drones:
                self.drones[drone_id].status = "已起飞"
    
    def land_drone(self):
        """降落选中的无人机"""
        selected_rows = self.status_table.selectionModel().selectedRows()
        for index in selected_rows:
            drone_id = int(self.status_table.item(index.row(), 0).text())
            if drone_id in self.drones:
                self.drones[drone_id].status = "正在降落"
    
    def return_drone(self):
        """返航选中的无人机"""
        selected_rows = self.status_table.selectionModel().selectedRows()
        for index in selected_rows:
            drone_id = int(self.status_table.item(index.row(), 0).text())
            if drone_id in self.drones:
                self.drones[drone_id].status = "返航中"
    
    def emergency_stop_drone(self):
        """紧急停止选中的无人机"""
        selected_rows = self.status_table.selectionModel().selectedRows()
        for index in selected_rows:
            drone_id = int(self.status_table.item(index.row(), 0).text())
            if drone_id in self.drones:
                self.drones[drone_id].status = "紧急停止"
    
    def closeEvent(self, event):
        """窗口关闭时停止所有无人机"""
        for drone in self.drones.values():
            drone.stop()
        event.accept() 