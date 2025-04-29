from PyQt5.QtWidgets import (QWidget, QGridLayout, QLabel, QPushButton, 
                            QVBoxLayout, QHBoxLayout, QComboBox, QMenu)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QSize
from PyQt5.QtGui import QImage, QPixmap, QIcon
import cv2
import numpy as np
import base64
from ..assets.icons import GRID_ICON, SINGLE_ICON, REFRESH_ICON

def create_icon_from_base64(base64_str):
    """从Base64字符串创建图标"""
    pixmap = QPixmap()
    pixmap.loadFromData(base64.b64decode(base64_str))
    return QIcon(pixmap)

class CameraGridCell(QLabel):
    """单个摄像头格子组件"""
    clicked = pyqtSignal(int)  # 点击信号，传递格子索引
    fire_detected = pyqtSignal(str)  # 火灾检测信号
    animal_detected = pyqtSignal(object, str, float)  # 动物检测信号
    
    def __init__(self, index, parent=None):
        super().__init__(parent)
        self.index = index
        self.active = False
        self.last_fire_check = 0  # 上次火情检查时间
        self.fire_check_interval = 1.0  # 火情检查间隔（秒）
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(320, 240)
        self.setStyleSheet("""
            QLabel {
                border: 2px solid #1e3a5a;
                background-color: #0a1a2a;
                color: white;
            }
            QLabel:hover {
                border: 2px solid #3a6a9a;
            }
        """)
        self.setText("摄像头未连接")
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.index)
        super().mousePressEvent(event)
        
    def setImage(self, image, camera_info=None):
        """设置图像并进行灾害检测"""
        if isinstance(image, np.ndarray):
            # 保存原始图像用于显示
            display_image = image.copy()
            
            # 进行火灾检测
            current_time = cv2.getTickCount() / cv2.getTickFrequency()
            if current_time - self.last_fire_check >= self.fire_check_interval:
                self.last_fire_check = current_time
                
                # 火灾检测
                if self.detect_fire(image):
                    region = camera_info['name'] if camera_info else f"摄像头 {self.index + 1}"
                    self.fire_detected.emit(region)
                    # 在图像上标注火灾警告
                    cv2.putText(display_image, "火灾警告!", (10, 30),
                              cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                
                # 动物检测
                animal_result = self.detect_animal(image)
                if animal_result:
                    species, confidence = animal_result
                    self.animal_detected.emit(image, species, confidence)
                    # 在图像上标注动物信息
                    cv2.putText(display_image, f"{species} ({confidence:.2f}%)", (10, 60),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # 转换BGR到RGB并显示
            display_image = cv2.cvtColor(display_image, cv2.COLOR_BGR2RGB)
            height, width, channel = display_image.shape
            bytesPerLine = 3 * width
            qImg = QImage(display_image.data, width, height, bytesPerLine, QImage.Format_RGB888)
            self.setPixmap(QPixmap.fromImage(qImg).scaled(
                self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.active = True
        else:
            self.setText("摄像头未连接")
            self.active = False
            
    def detect_fire(self, image):
        """检测火灾
        使用简单的颜色阈值方法检测火焰
        """
        try:
            # 转换到HSV颜色空间
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # 定义火焰的颜色范围（红色和橙色）
            lower_red1 = np.array([0, 120, 70])
            upper_red1 = np.array([10, 255, 255])
            lower_red2 = np.array([170, 120, 70])
            upper_red2 = np.array([180, 255, 255])
            
            # 创建掩码
            mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
            mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
            mask = cv2.bitwise_or(mask1, mask2)
            
            # 计算火焰像素占比
            fire_ratio = np.sum(mask > 0) / (mask.shape[0] * mask.shape[1])
            
            # 如果火焰像素占比超过阈值，认为检测到火灾
            return fire_ratio > 0.01
            
        except Exception as e:
            print(f"火灾检测出错: {e}")
            return False
            
    def detect_animal(self, image):
        """检测动物
        这里使用简单的运动检测作为示例
        实际项目中应该使用更复杂的目标检测模型
        """
        try:
            # 在实际项目中，这里应该使用预训练的目标检测模型
            # 例如 YOLO 或 SSD
            # 这里仅作为示例返回模拟结果
            return None
            
        except Exception as e:
            print(f"动物检测出错: {e}")
            return None

class GridCameraView(QWidget):
    """九宫格摄像头视图"""
    
    # 添加灾害检测信号
    fire_detected = pyqtSignal(str)  # 火灾检测信号
    animal_detected = pyqtSignal(object, str, float)  # 动物检测信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cameras = {}  # 存储摄像头对象
        self.current_layout = "grid"  # grid或single
        self.active_cell = None
        
        # 创建图标
        self.grid_icon = create_icon_from_base64(GRID_ICON)
        self.single_icon = create_icon_from_base64(SINGLE_ICON)
        self.refresh_icon = create_icon_from_base64(REFRESH_ICON)
        
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        # 创建主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        self.main_layout.setSpacing(5)
        
        # 创建工具栏
        toolbar = QHBoxLayout()
        
        # 添加布局切换按钮
        self.layout_btn = QPushButton("切换视图")
        self.layout_btn.setIcon(self.grid_icon)
        self.layout_btn.clicked.connect(self.toggle_layout)
        toolbar.addWidget(self.layout_btn)
        
        # 添加摄像头选择下拉框
        self.camera_combo = QComboBox()
        self.camera_combo.addItem("所有摄像头")
        self.camera_combo.addItem("地面摄像头")
        self.camera_combo.addItem("无人机摄像头")
        self.camera_combo.currentIndexChanged.connect(self.on_camera_type_changed)
        toolbar.addWidget(QLabel("摄像头类型:"))
        toolbar.addWidget(self.camera_combo)
        
        toolbar.addStretch()
        
        # 添加刷新按钮
        refresh_btn = QPushButton("刷新")
        refresh_btn.setIcon(self.refresh_icon)
        refresh_btn.clicked.connect(self.refresh_cameras)
        toolbar.addWidget(refresh_btn)
        
        self.main_layout.addLayout(toolbar)
        
        # 创建九宫格容器
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(5)
        
        # 创建9个摄像头格子
        self.cells = []
        for i in range(9):
            cell = CameraGridCell(i)
            cell.clicked.connect(self.on_cell_clicked)
            # 连接灾害检测信号
            cell.fire_detected.connect(self.fire_detected)
            cell.animal_detected.connect(self.animal_detected)
            self.cells.append(cell)
            self.grid_layout.addWidget(cell, i // 3, i % 3)
            
        self.main_layout.addWidget(self.grid_container)
        
        # 创建定时器用于更新画面
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_frames)
        self.update_timer.start(33)  # 约30fps
        
        # 初始化摄像头
        self.refresh_cameras()
        
    def toggle_layout(self):
        """切换布局模式"""
        if self.current_layout == "grid":
            self.current_layout = "single"
            self.layout_btn.setIcon(self.single_icon)
            # 隐藏除了活动格子之外的所有格子
            for i, cell in enumerate(self.cells):
                cell.setVisible(i == self.active_cell if self.active_cell is not None else i == 0)
        else:
            self.current_layout = "grid"
            self.layout_btn.setIcon(self.grid_icon)
            # 显示所有格子
            for cell in self.cells:
                cell.setVisible(True)
                
    def on_cell_clicked(self, index):
        """处理格子点击事件"""
        self.active_cell = index
        if self.current_layout == "grid":
            self.toggle_layout()  # 切换到单视图模式
            
    def on_camera_type_changed(self, index):
        """处理摄像头类型切换"""
        self.refresh_cameras()
        
    def refresh_cameras(self):
        """刷新摄像头列表"""
        # 这里应该实现摄像头检测和连接逻辑
        # 示例：模拟9个摄像头
        self.cameras.clear()
        camera_type = self.camera_combo.currentText()
        
        if camera_type in ["所有摄像头", "地面摄像头"]:
            # 添加4个地面摄像头
            for i in range(4):
                try:
                    cap = cv2.VideoCapture(i)
                    if cap.isOpened():
                        self.cameras[i] = {
                            'capture': cap,
                            'type': 'ground',
                            'name': f'地面摄像头 {i+1}'
                        }
                except Exception as e:
                    print(f"连接摄像头 {i} 失败: {e}")
                    
        if camera_type in ["所有摄像头", "无人机摄像头"]:
            # 模拟5个无人机摄像头
            for i in range(5):
                self.cameras[i+4] = {
                    'capture': None,  # 实际项目中应该连接到无人机视频流
                    'type': 'drone',
                    'name': f'无人机 {i+1}'
                }
                
    def update_frames(self):
        """更新所有摄像头画面"""
        if self.current_layout == "single" and self.active_cell is not None:
            # 单视图模式只更新活动格子
            self.update_cell(self.active_cell)
        else:
            # 网格模式更新所有格子
            for i in range(9):
                self.update_cell(i)
                
    def update_cell(self, index):
        """更新单个格子的画面"""
        if index in self.cameras:
            camera = self.cameras[index]
            if camera['type'] == 'ground' and camera['capture'] is not None:
                ret, frame = camera['capture'].read()
                if ret:
                    self.cells[index].setImage(frame, camera)
                    return
            elif camera['type'] == 'drone':
                # 模拟无人机画面
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(frame, f"无人机 {index-3} 画面", (50, 240),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                self.cells[index].setImage(frame, camera)
                return
                
        # 如果没有摄像头或获取画面失败
        self.cells[index].setImage(None)
        
    def closeEvent(self, event):
        """关闭时释放摄像头资源"""
        self.update_timer.stop()
        for camera in self.cameras.values():
            if camera['type'] == 'ground' and camera['capture'] is not None:
                camera['capture'].release()
        super().closeEvent(event) 