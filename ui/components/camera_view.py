import os
import cv2
import numpy as np
from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QComboBox, QToolBar, QAction, 
                            QGridLayout, QFrame, QSplitter, QFileDialog,
                            QMessageBox)
from PyQt5.QtCore import Qt, QTimer, pyqtSlot, pyqtSignal, QSize, QRect, QThread
from PyQt5.QtGui import QImage, QPixmap, QIcon, QPainter, QPen, QColor, QFont
import random
import time
import torch
import torch.backends.cudnn as cudnn
from pathlib import Path
import sys

# 添加项目根目录到系统路径
FILE = Path(__file__).resolve()
ROOT = FILE.parents[2]  # YOLOv5 root directory
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from models.common import DetectMultiBackend
from models.yolo import Detect
from utils.datasets import IMG_FORMATS, VID_FORMATS, LoadImages, LoadStreams
from utils.general import (LOGGER, check_file, check_img_size, check_imshow, check_requirements, colorstr,
                         increment_path, non_max_suppression, print_args, scale_coords, strip_optimizer, xyxy2xywh)
from utils.plots import Annotator, colors, save_one_box
from utils.torch_utils import select_device, time_sync

class VideoThread(QThread):
    """视频处理线程，用于读取摄像头或视频文件"""
    update_frame = pyqtSignal(np.ndarray)
    update_detections = pyqtSignal(list)
    fire_detected = pyqtSignal(str)  # 修改为发送区域信息的信号
    error_signal = pyqtSignal(str)
    
    def __init__(self, source=0):
        super().__init__()
        self.source = source
        self.running = False
        self.model = None
        self.device = select_device('0' if torch.cuda.is_available() else 'cpu')
        self.half = False
        self.stride = 32
        self.imgsz = [640, 640]
        self.current_region = "中央林场"  # 添加默认区域
        self.init_model()
        
    def init_model(self):
        """初始化YOLOv5火焰检测模型"""
        try:
            # 获取项目根目录路径
            weights = str(ROOT / 'weights/best.pt')
            
            if not os.path.exists(weights):
                print(f"错误：模型文件 {weights} 不存在")
                self.model = None
                return
                
            # 加载模型
            self.model = DetectMultiBackend(weights, device=self.device)
            self.stride = self.model.stride
            self.imgsz = check_img_size(self.imgsz, s=self.stride)  # 检查图片尺寸
            
            # 打印模型支持的类别
            print("模型支持的类别：", self.model.names)
            
            # 设置半精度
            self.half = self.device.type != 'cpu'  # 仅在GPU上使用半精度
            if self.half:
                self.model.half()  # 转换模型为半精度
            else:
                self.model.float()  # 使用单精度

            # 确保Detect层有inplace属性
            for m in self.model.model.modules():
                if isinstance(m, Detect):
                    if not hasattr(m, 'inplace'):
                        m.inplace = True
            
            # 预热模型
            if self.device.type != 'cpu':
                dummy = torch.zeros(1, 3, *self.imgsz).to(self.device)
                dummy = dummy.half() if self.half else dummy.float()
                for _ in range(3):  # 预热3次
                    with torch.no_grad():
                        self.model(dummy)  # 预热推理
                torch.cuda.empty_cache()  # 清理显存
                
            print(f"火焰检测模型加载成功：{weights}")
            
            # 设置CUDA性能优化
            if self.device.type != 'cpu':
                cudnn.benchmark = True  # 加速固定大小图像的推理
                cudnn.deterministic = False  # 提高速度
                
        except Exception as e:
            print(f"火焰检测模型加载失败: {str(e)}")
            import traceback
            traceback.print_exc()
            self.model = None
            self.error_signal.emit(f"模型加载失败: {str(e)}")
        
    def set_source(self, source):
        """设置视频源"""
        self.source = source
        
    def run(self):
        """运行线程，读取视频并进行检测"""
        if self.model is None:
            self.error_signal.emit("错误：模型未加载")
            return
            
        try:
            self.running = True
            
            # 初始化参数
            conf_thres = 0.25  # 置信度阈值
            iou_thres = 0.45  # NMS IOU阈值
            max_det = 1000  # 每张图片最大检测数量
            line_thickness = 2  # 减小边框线条粗细以提高性能
            hide_labels = False  # 是否隐藏标签
            hide_conf = False  # 是否隐藏置信度
            
            # 设置数据源
            source = str(self.source)
            webcam = source.isnumeric()
            
            # 检查视频源
            if webcam:
                try:
                    source = int(source)
                    cap = cv2.VideoCapture(source)
                    if not cap.isOpened():
                        self.error_signal.emit(f"无法打开摄像头 {source}")
                        return
                    cap.release()
                except Exception as e:
                    self.error_signal.emit(f"摄像头初始化失败: {str(e)}")
                    return
            else:
                if not os.path.exists(source):
                    self.error_signal.emit(f"视频文件不存在: {source}")
                    return
                try:
                    cap = cv2.VideoCapture(source)
                    if not cap.isOpened():
                        self.error_signal.emit(f"无法打开视频文件: {source}")
                        return
                    # 检查视频是否可读
                    ret, frame = cap.read()
                    if not ret:
                        self.error_signal.emit(f"无法读取视频帧: {source}")
                        return
                    cap.release()
                except Exception as e:
                    self.error_signal.emit(f"视频文件打开失败: {str(e)}")
                    return
            
            # 获取模型信息
            stride = self.model.stride
            names = self.model.names
            pt = getattr(self.model, 'pt', True)
            
            # 检查图像尺寸
            self.imgsz = check_img_size(self.imgsz, s=stride)
            
            try:
                # 设置数据加载器
                if webcam:
                    cudnn.benchmark = True
                    dataset = LoadStreams(str(source), img_size=self.imgsz[0], stride=stride, auto=pt)
                else:
                    dataset = LoadImages(source, img_size=self.imgsz[0], stride=stride, auto=pt)
            except Exception as e:
                self.error_signal.emit(f"数据加载失败: {str(e)}")
                return
                
            # 处理每一帧
            for path, im, im0s, vid_cap, s in dataset:
                if not self.running:
                    break
                    
                try:
                    # 预处理图像
                    im = torch.from_numpy(im).to(self.device)
                    im = im.half() if self.half else im.float()
                    im /= 255
                    if len(im.shape) == 3:
                        im = im[None]
                        
                    # 推理
                    with torch.no_grad():
                        pred = self.model(im, augment=False)  # 禁用数据增强以提高速度
                        if isinstance(pred, (list, tuple)):
                            pred = pred[0]
                    
                    # NMS
                    pred = non_max_suppression(pred, conf_thres, iou_thres, None, False, max_det=max_det)
                    
                    # 处理检测结果
                    for i, det in enumerate(pred):
                        if webcam:
                            im0 = im0s[i].copy()
                        else:
                            im0 = im0s.copy()
                            
                        s += '%gx%g ' % im.shape[2:]
                        annotator = Annotator(im0, line_width=line_thickness, example=str(names))
                        
                        if len(det):
                            # 将边界框从img_size缩放到im0大小
                            det[:, :4] = scale_coords(im.shape[2:], det[:, :4], im0.shape).round()
                            
                            detections = []
                            fire_detected = False
                            
                            for c in det[:, -1].unique():
                                n = (det[:, -1] == c).sum()
                                s += f"{n} {names[int(c)]}{'s' * (n > 1)}, "
                            
                            for *xyxy, conf, cls in reversed(det):
                                c = int(cls)
                                if conf > conf_thres:  # 如果置信度大于阈值
                                    label = None if hide_labels else (
                                        names[c] if hide_conf else f'{names[c]} {conf:.2f}'
                                    )
                                    annotator.box_label(xyxy, label, color=colors(c, True))
                                    
                                    # 如果检测到火焰，发送信号
                                    if names[c].lower() == 'fire' and conf > 0.5:  # 提高火焰检测的置信度阈值
                                        print(f"检测到火焰！类别：{names[c]}，置信度：{conf:.2f}")  # 添加调试输出
                                        self.fire_detected.emit(self.current_region)  # 发送当前区域信息
                            
                            self.update_detections.emit(detections)
                        
                        im0 = annotator.result()
                        self.update_frame.emit(im0)
                        
                except Exception as e:
                    print(f"处理帧时出错: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    continue
                
                self.msleep(10)  # 减小延迟时间，提高帧率
                
        except Exception as e:
            print(f"视频处理线程出错: {str(e)}")
            import traceback
            traceback.print_exc()
            self.error_signal.emit(f"视频处理出错: {str(e)}")
            
        finally:
            self.running = False
        
    def draw_box(self, img, xyxy, label):
        """在图像上绘制边界框和标签"""
        x1, y1, x2, y2 = [int(x) for x in xyxy]
        color = (0, 0, 255)  # 红色
        
        # 绘制边界框
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
        
        # 绘制标签背景
        text_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
        cv2.rectangle(img, (x1, y1 - text_size[1] - 5), (x1 + text_size[0], y1), color, -1)
        
        # 绘制标签
        cv2.putText(img, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        return img
        
    def stop(self):
        """停止线程"""
        self.running = False
        self.wait()
        
    def preprocess_frame(self, frame):
        """预处理帧，用于模型输入"""
        # 缩放到模型所需尺寸
        resized = cv2.resize(frame, (640, 640))
        # 转换为RGB
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        # 归一化
        normalized = rgb / 255.0
        # 转换为tensor
        img = torch.from_numpy(normalized).float()
        # 调整维度顺序 (H, W, C) -> (C, H, W)
        img = img.permute(2, 0, 1)
        # 添加批次维度
        img = img.unsqueeze(0)
        return img
        
    def mock_detections(self, frame):
        """模拟检测结果，用于开发阶段"""
        height, width = frame.shape[:2]
        
        # 模拟一些检测结果
        detections = [
            {
                'task': 'fire',
                'class': 0,  # 火焰
                'label': '火灾',
                'confidence': 0.85,
                'bbox': [width * 0.1, height * 0.2, width * 0.2, height * 0.3]  # [x1, y1, x2, y2]
            },
            {
                'task': 'animal',
                'class': 2,  # 某种动物
                'label': '野生动物',
                'confidence': 0.76,
                'bbox': [width * 0.6, height * 0.5, width * 0.8, height * 0.7]
            },
            {
                'task': 'pest',
                'class': 3,  # 病虫害
                'label': '病虫害-松毛虫',
                'confidence': 0.82,
                'bbox': [width * 0.3, height * 0.4, width * 0.5, height * 0.6],
                'subtype': '松毛虫',
                'severity': '中度'
            }
        ]
        
        # 每秒随机变化一下位置，模拟运动
        random.seed(int(time.time()))
        
        for det in detections:
            # 随机移动边界框
            x1, y1, x2, y2 = det['bbox']
            dx = random.uniform(-10, 10)
            dy = random.uniform(-10, 10)
            
            # 确保边界框在图像内
            x1 = max(0, min(width - 10, x1 + dx))
            y1 = max(0, min(height - 10, y1 + dy))
            x2 = max(x1 + 10, min(width, x2 + dx))
            y2 = max(y1 + 10, min(height, y2 + dy))
            
            det['bbox'] = [x1, y1, x2, y2]
        
        return detections
        
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
            
            # 如果是病虫害，添加额外信息
            if det['task'] == 'pest' and 'subtype' in det:
                severity_text = f"类型: {det['subtype']}"
                if 'severity' in det:
                    severity_text += f" | 严重程度: {det['severity']}"
                cv2.putText(frame, severity_text, (x1, y1 - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return frame

class CameraView(QWidget):
    """摄像头视图组件，用于显示实时视频流和检测结果"""
    
    fire_detected = pyqtSignal(str)  # 修改为发送区域信息的信号
    
    def __init__(self, config=None):
        super().__init__()
        self.config = config
        self.detection_results = []
        self.current_source = '0'  # 默认使用摄像头
        self.output_size = 400
        self.current_region = "中央林场"  # 默认区域
        
        # 修改设备选择逻辑
        try:
            if torch.cuda.is_available():
                self.device = select_device('0')
            else:
                self.device = select_device('cpu')
        except Exception as e:
            print(f"GPU初始化失败，使用CPU: {str(e)}")
            self.device = select_device('cpu')
        
        # 创建视频处理线程
        self.video_thread = VideoThread(self.current_source)
        self.video_thread.update_frame.connect(self.update_frame)
        self.video_thread.update_detections.connect(self.update_detections)
        self.video_thread.fire_detected.connect(self.on_fire_detected)
        self.video_thread.error_signal.connect(self.on_error)
        
        # 创建结果保存目录
        self.results_dir = str(ROOT / 'results')
        os.makedirs(self.results_dir, exist_ok=True)
        
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        # 创建主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建顶部工具栏布局
        toolbar_layout = QHBoxLayout()
        
        # 添加摄像头选择下拉框
        self.camera_combo = QComboBox()
        self.camera_combo.addItem("摄像头0", '0')
        self.camera_combo.addItem("摄像头1", '1')
        self.camera_combo.addItem("视频文件", '-1')
        self.camera_combo.currentIndexChanged.connect(self.change_camera)
        toolbar_layout.addWidget(QLabel("视频源:"))
        toolbar_layout.addWidget(self.camera_combo)
        
        # 添加空白占位
        toolbar_layout.addStretch(1)
        
        # 添加截图按钮
        self.snapshot_btn = QPushButton("截图")
        self.snapshot_btn.setIcon(QIcon(str(ROOT / 'ui/assets/snapshot.png')))
        self.snapshot_btn.clicked.connect(self.take_snapshot)
        toolbar_layout.addWidget(self.snapshot_btn)
        
        # 添加工具栏到布局
        layout.addLayout(toolbar_layout)
        
        # 创建视频显示区域
        self.video_frame = QLabel()
        self.video_frame.setAlignment(Qt.AlignCenter)
        self.video_frame.setMinimumSize(640, 480)
        self.video_frame.setStyleSheet("background-color: black;")
        
        # 添加视频帧到布局
        layout.addWidget(self.video_frame, 1)
        
        # 创建状态栏
        status_bar = QHBoxLayout()
        
        # 添加状态信息
        self.status_label = QLabel("状态: 未启动")
        status_bar.addWidget(self.status_label)
        
        # 添加FPS信息
        self.fps_label = QLabel("FPS: 0")
        status_bar.addWidget(self.fps_label)
        
        # 添加检测结果信息
        self.detection_label = QLabel("检测结果: 0")
        status_bar.addWidget(self.detection_label)
        
        # 添加时间戳
        self.timestamp_label = QLabel(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        status_bar.addWidget(self.timestamp_label, 1, Qt.AlignRight)
        
        # 添加状态栏到布局
        layout.addLayout(status_bar)
        
        # 创建定时器更新时间戳
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timestamp)
        self.timer.start(1000)  # 每秒更新一次
        
        # 计算FPS的变量
        self.frame_count = 0
        self.fps = 0
        self.fps_timer = QTimer(self)
        self.fps_timer.timeout.connect(self.calculate_fps)
        self.fps_timer.start(1000)  # 每秒计算一次FPS
        
    def update_frame(self, frame):
        """更新视频帧"""
        # 计算帧数
        self.frame_count += 1
        
        # 转换OpenCV的BGR格式为RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # 转换为QImage
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        
        # 缩放到显示区域大小
        pixmap = QPixmap.fromImage(qt_image)
        pixmap = pixmap.scaled(self.video_frame.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        # 设置图像
        self.video_frame.setPixmap(pixmap)
        
    def update_detections(self, detections):
        """更新检测结果"""
        self.detection_results = detections
        self.detection_label.setText(f"检测结果: {len(detections)}")
        
    def update_timestamp(self):
        """更新时间戳"""
        self.timestamp_label.setText(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
    def calculate_fps(self):
        """计算FPS"""
        self.fps = self.frame_count
        self.fps_label.setText(f"FPS: {self.fps}")
        self.frame_count = 0
        
    def update_view(self):
        """更新视图（由外部定时器调用）"""
        # 由于视频帧由线程自动更新，这里主要更新其他UI元素
        if self.video_thread.isRunning():
            self.status_label.setText("状态: 监控中")
        else:
            self.status_label.setText("状态: 已停止")
            
    def start_monitoring(self):
        """开始监控"""
        if not self.video_thread.isRunning():
            self.video_thread.start()
            self.status_label.setText("状态: 监控中")
            
    def stop_monitoring(self):
        """停止监控"""
        if self.video_thread.isRunning():
            self.video_thread.stop()
            self.status_label.setText("状态: 已停止")
            
    @pyqtSlot(int)
    def change_camera(self, index):
        """改变摄像头"""
        # 获取选择的摄像头
        source = self.camera_combo.currentData()
        
        # 如果选择了视频文件
        if source == '-1':
            fileName, _ = QFileDialog.getOpenFileName(
                self,
                "选择视频文件",
                "",
                "视频文件 (*.mp4 *.avi *.mkv *.mov);;所有文件 (*.*)"
            )
            if not fileName:
                # 如果用户取消选择，恢复到之前的选项
                self.camera_combo.setCurrentIndex(0)
                return
            source = fileName
        
        # 停止当前视频
        self.stop_monitoring()
        
        # 设置新的视频源
        self.current_source = source
        self.video_thread.set_source(source)
        
        # 重新开始监控
        self.start_monitoring()
        
    @pyqtSlot()
    def take_snapshot(self):
        """截取当前帧"""
        # 获取当前显示的图像
        pixmap = self.video_frame.pixmap()
        
        if pixmap and not pixmap.isNull():
            # 创建保存目录
            snapshots_dir = os.path.join(self.results_dir, 'snapshots')
            os.makedirs(snapshots_dir, exist_ok=True)
            
            # 保存图像
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = os.path.join(snapshots_dir, f"snapshot_{timestamp}.jpg")
            
            if pixmap.save(file_path, "JPG"):
                self.status_label.setText(f"状态: 已保存截图 {file_path}")
            else:
                self.status_label.setText("状态: 截图保存失败")
                
    def resizeEvent(self, event):
        """窗口大小改变事件"""
        # 如果有图像，重新缩放
        if self.video_frame.pixmap() and not self.video_frame.pixmap().isNull():
            pixmap = self.video_frame.pixmap().scaled(
                self.video_frame.size(), 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            self.video_frame.setPixmap(pixmap)
            
    def on_fire_detected(self, region):
        """处理火焰检测信号"""
        # 转发信号到主窗口，包含区域信息
        self.fire_detected.emit(region)

    def on_error(self, error_msg):
        """处理错误信息"""
        self.status_label.setText(f"状态: {error_msg}")
        QMessageBox.warning(self, "错误", error_msg)
        self.reset_camera()
        
    def reset_camera(self):
        """重置摄像头状态"""
        self.stop_monitoring()
        self.camera_combo.setCurrentIndex(0)  # 切换回默认摄像头
        self.video_frame.clear()  # 清空视频显示
        self.video_frame.setStyleSheet("background-color: black;")

    def detect_vid(self):
        """视频检测函数"""
        try:
            # 初始化模型参数
            model = self.model
            output_size = self.output_size
            imgsz = [640, 640]  # 推理时的输入图像尺寸（像素）
            conf_thres = 0.25  # 置信度阈值
            iou_thres = 0.45  # NMS（非极大值抑制）IOU阈值
            max_det = 1000  # 每张图片最大检测数
            
            # 设备选择逻辑
            try:
                if torch.cuda.is_available():
                    device = select_device('0')
                    half = True  # 在GPU上使用半精度
                else:
                    device = select_device('cpu')
                    half = False  # CPU不使用半精度
            except Exception as e:
                print(f"GPU初始化失败，使用CPU: {str(e)}")
                device = select_device('cpu')
                half = False
            
            view_img = False  # 是否显示检测结果
            save_txt = False  # 是否保存结果到*.txt文件
            save_conf = False  # 是否保存置信度到标签文件
            save_crop = False  # 是否保存裁剪后的预测框图像
            nosave = False  # 是否禁用保存图像/视频
            classes = None  # 按类别过滤：--class 0，或者--class 0 2 3
            agnostic_nms = False  # 是否使用类别无关的NMS
            augment = False  # 是否进行增强推理
            visualize = False  # 是否可视化特征
            line_thickness = 3  # 边框的厚度（像素）
            hide_labels = False  # 是否隐藏标签
            hide_conf = False  # 是否隐藏置信度
            dnn = False  # 是否使用OpenCV DNN进行ONNX推理

            source = str(self.vid_source)  # 设置视频源（文件/目录）
            webcam = self.webcam  # 是否使用摄像头
            device = select_device(self.device)  # 选择推理设备
            
            # 获取模型信息
            stride = model.stride
            names = model.names
            pt = getattr(model, 'pt', True)
            
            # 检查图像尺寸
            imgsz = check_img_size(imgsz, s=stride)  # 检查图像尺寸是否合适
            
            # 检查视频源
            if webcam:
                try:
                    source = int(source)
                    cap = cv2.VideoCapture(source)
                    if not cap.isOpened():
                        self.error_signal.emit(f"无法打开摄像头 {source}")
                        return
                    cap.release()
                except Exception as e:
                    self.error_signal.emit(f"摄像头初始化失败: {str(e)}")
                    return
            else:
                if not os.path.exists(source):
                    self.error_signal.emit(f"视频文件不存在: {source}")
                    return
                try:
                    cap = cv2.VideoCapture(source)
                    if not cap.isOpened():
                        self.error_signal.emit(f"无法打开视频文件: {source}")
                        return
                    ret, frame = cap.read()
                    if not ret:
                        self.error_signal.emit(f"无法读取视频帧: {source}")
                        return
                    cap.release()
                except Exception as e:
                    self.error_signal.emit(f"视频文件打开失败: {str(e)}")
                    return

            try:
                # 设置数据加载器
                if webcam:
                    cudnn.benchmark = True  # 设置为True以加速恒定图像大小的推理
                    dataset = LoadStreams(str(source), img_size=imgsz[0], stride=stride, auto=pt)
                else:
                    dataset = LoadImages(source, img_size=imgsz[0], stride=stride, auto=pt)
            except Exception as e:
                self.error_signal.emit(f"数据加载失败: {str(e)}")
                return

            # 预热模型
            if pt and device.type != 'cpu':
                model(torch.zeros(1, 3, *imgsz).to(device).type_as(next(model.parameters())))

            # 处理每一帧
            for path, im, im0s, vid_cap, s in dataset:
                try:
                    # 预处理
                    im = torch.from_numpy(im).to(device)
                    im = im.half() if half else im.float()  # uint8 转为 fp16/32
                    im /= 255  # 将像素值从0-255归一化到0.0-1.0
                    if len(im.shape) == 3:
                        im = im[None]  # 扩展维度以符合batch size要求

                    # 推理过程
                    with torch.no_grad():
                        pred = model(im, augment=augment, visualize=visualize)
                        if isinstance(pred, (list, tuple)):
                            pred = pred[0]

                    # NMS非极大值抑制
                    pred = non_max_suppression(pred, conf_thres, iou_thres, classes, agnostic_nms, max_det=max_det)

                    # 处理检测结果
                    for i, det in enumerate(pred):
                        if webcam:  # 如果是摄像头流
                            im0 = im0s[i].copy()
                        else:
                            im0 = im0s.copy()

                        # 初始化标注器
                        annotator = Annotator(im0, line_width=line_thickness, example=str(names))

                        if len(det):
                            # 将边框坐标从img_size映射到原始图像尺寸
                            det[:, :4] = scale_coords(im.shape[2:], det[:, :4], im0.shape).round()

                            # 处理每个检测结果
                            for *xyxy, conf, cls in reversed(det):
                                c = int(cls)
                                if conf > conf_thres:  # 如果置信度大于阈值
                                    label = None if hide_labels else (
                                        names[c] if hide_conf else f'{names[c]} {conf:.2f}'
                                    )
                                    annotator.box_label(xyxy, label, color=colors(c, True))
                                    
                                    # 如果检测到火焰，发送信号
                                    if names[c].lower() == 'fire' and conf > 0.5:  # 提高火焰检测的置信度阈值
                                        print(f"检测到火焰！类别：{names[c]}，置信度：{conf:.2f}")  # 添加调试输出
                                        self.fire_detected.emit(self.current_region)  # 发送当前区域信息

                        # 获取标注后的图像
                        im0 = annotator.result()
                        
                        # 调整图像大小并显示
                        resize_scale = output_size / im0.shape[0]
                        im0 = cv2.resize(im0, (0, 0), fx=resize_scale, fy=resize_scale)
                        
                        # 转换为Qt图像并显示
                        rgb_image = cv2.cvtColor(im0, cv2.COLOR_BGR2RGB)
                        h, w, ch = rgb_image.shape
                        qt_image = QImage(rgb_image.data, w, h, w * ch, QImage.Format_RGB888)
                        self.vid_img.setPixmap(QPixmap.fromImage(qt_image))

                except Exception as e:
                    print(f"处理帧时出错: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    continue

                # 检查是否需要停止
                if self.stopEvent.is_set():
                    break

                self.msleep(10)  # 控制帧率

        except Exception as e:
            print(f"视频处理出错: {str(e)}")
            import traceback
            traceback.print_exc()
            self.error_signal.emit(f"视频处理出错: {str(e)}")
        finally:
            self.reset_vid()

class MockDetector:
    """模拟检测器类，用于生成模拟检测结果"""
    
    def __init__(self):
        """初始化检测器"""
        self.detection_mode = "all"  # 默认检测所有类型
        
    def set_mode(self, mode):
        """设置检测模式"""
        self.detection_mode = mode
        
    def detect(self, frame):
        """在图像上执行检测"""
        # 实际项目中，这里应该调用真实的检测模型
        # 这里仅做模拟，随机生成检测结果
        
        height, width = frame.shape[:2]
        detections = []
        
        # 随机决定是否生成检测结果
        if random.random() < 0.2:  # 20%概率生成检测
            # 可检测的类型
            types = {
                'all': ['fire', 'animal', 'landslide', 'forest', 'pest'],
                'fire': ['fire'],
                'animal': ['animal'],
                'landslide': ['landslide'],
                'forest': ['forest'],
                'pest': ['pest']
            }
            
            # 根据检测模式选择可能的检测类型
            possible_types = types.get(self.detection_mode, ['fire'])
            
            # 随机选择一种类型
            detection_type = random.choice(possible_types)
            
            # 类型对应的标签和颜色
            labels = {
                'fire': '火灾',
                'animal': '野生动物',
                'landslide': '滑坡',
                'forest': '森林退化',
                'pest': '病虫害'
            }
            
            colors = {
                'fire': (0, 0, 255),      # 红色
                'animal': (0, 255, 0),    # 绿色
                'landslide': (255, 0, 0), # 蓝色
                'forest': (255, 255, 0),  # 青色
                'pest': (128, 0, 128)     # 紫色
            }
            
            # 对于病虫害类型，生成更详细的标签
            if detection_type == 'pest':
                pest_types = ['松毛虫', '美国白蛾', '落叶松毛虫', '杨树食叶害虫', '松材线虫病']
                pest_subtype = random.choice(pest_types)
                label = f"{labels[detection_type]}-{pest_subtype}"
            else:
                label = labels[detection_type]
            
            # 随机生成边界框
            x = random.randint(10, width - 100)
            y = random.randint(10, height - 100)
            w = random.randint(50, 150)
            h = random.randint(50, 150)
            
            # 随机生成置信度
            confidence = random.uniform(0.65, 0.95)
            
            # 创建检测结果
            detection = {
                'type': detection_type,
                'bbox': [x, y, x+w, y+h],
                'confidence': confidence,
                'label': label,
                'color': colors[detection_type]
            }
            
            detections.append(detection)
            
        return detections 