import cv2
import torch
import numpy as np
from models.yolo import YOLOv5

class CameraDetector:
    def __init__(self, config):
        """初始化摄像头检测器"""
        self.config = config
        self.device = torch.device(config['device'])
        
        # 初始化YOLOv5模型
        weights_path = f"{config['weights_path']}/yolov5{config['model_size']}.pt"
        self.model = YOLOv5(weights_path, self.device)
        self.model.conf = config['conf_threshold']
        self.model.iou = config['iou_threshold']
        
        # 初始化摄像头
        self.cap = None
        self.is_running = False
        
    def start_camera(self, camera_id=0):
        """启动摄像头"""
        try:
            self.cap = cv2.VideoCapture(camera_id)
            if not self.cap.isOpened():
                raise Exception("无法打开摄像头")
            self.is_running = True
            return True
        except Exception as e:
            print(f"摄像头启动失败: {e}")
            return False
            
    def stop_camera(self):
        """停止摄像头"""
        self.is_running = False
        if self.cap:
            self.cap.release()
            
    def detect_frame(self, frame):
        """对单帧图像进行检测"""
        if frame is None:
            return None, []
            
        # 调整图像大小
        img = cv2.resize(frame, (self.config['image_size'], self.config['image_size']))
        
        # 执行检测
        results = self.model(img)
        
        # 处理检测结果
        detections = []
        for *xyxy, conf, cls in results.xyxy[0]:
            x1, y1, x2, y2 = map(int, xyxy)
            label = self.model.names[int(cls)]
            confidence = float(conf)
            
            # 在图像上绘制边界框
            color = (0, 0, 255) if label == 'fire' else (0, 255, 0)  # 火焰用红色，烟雾用绿色
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, f'{label} {confidence:.2f}',
                       (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX,
                       0.5, color, 2)
                       
            detections.append({
                'label': label,
                'confidence': confidence,
                'bbox': (x1, y1, x2, y2)
            })
            
        return frame, detections
        
    def get_frame(self):
        """获取一帧并进行检测"""
        if not self.is_running or not self.cap:
            return None, []
            
        ret, frame = self.cap.read()
        if not ret:
            return None, []
            
        return self.detect_frame(frame)
        
    def __del__(self):
        """析构函数，确保释放摄像头资源"""
        self.stop_camera() 