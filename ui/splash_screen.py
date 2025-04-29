import sys
import os
from PyQt5.QtWidgets import (QApplication, QSplashScreen, QProgressBar, 
                             QLabel, QVBoxLayout, QWidget, QFrame, QDesktopWidget)
from PyQt5.QtCore import Qt, QTimer, QSize, QPropertyAnimation, QEasingCurve, QPoint
from PyQt5.QtGui import QPixmap, QFont, QColor, QPainter, QBrush, QPen, QRadialGradient, QLinearGradient, QMovie
import math  # 添加数学库

class ParticleEffect(QWidget):
    """粒子效果动画组件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.particles = []
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_particles)
        self.timer.start(50)  # 每50毫秒更新一次
        
        # 初始化粒子
        for _ in range(100):  # 增加粒子数量
            self.particles.append({
                'x': self.width() * 0.5,
                'y': self.height() * 0.5,
                'vx': (0.5 - float(os.urandom(1)[0]) / 255.0) * 8,  # 增加速度范围
                'vy': (0.5 - float(os.urandom(1)[0]) / 255.0) * 8,
                'size': 1 + float(os.urandom(1)[0]) / 32.0,  # 增加粒子大小
                'alpha': 0.5 + float(os.urandom(1)[0]) / 255.0,
                'color': QColor(100 + int(os.urandom(1)[0]) % 155, 
                                200 + int(os.urandom(1)[0]) % 55, 
                                220 + int(os.urandom(1)[0]) % 35,  # 更亮的蓝色调
                                200)
            })
    
    def update_particles(self):
        width = self.width() or 1920  # 防止宽度为0
        height = self.height() or 1080
        
        for p in self.particles:
            # 更新位置
            p['x'] += p['vx']
            p['y'] += p['vy']
            
            # 如果超出边界，重新生成粒子
            if (p['x'] < 0 or p['x'] > width or 
                p['y'] < 0 or p['y'] > height):
                p['x'] = width * 0.5 + (width * 0.3 * (float(os.urandom(1)[0]) / 255.0 - 0.5))  # 随机中心位置
                p['y'] = height * 0.5 + (height * 0.3 * (float(os.urandom(1)[0]) / 255.0 - 0.5))
                p['vx'] = (0.5 - float(os.urandom(1)[0]) / 255.0) * 8
                p['vy'] = (0.5 - float(os.urandom(1)[0]) / 255.0) * 8
        
        self.update()  # 触发重绘
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        for p in self.particles:
            painter.setPen(Qt.NoPen)
            painter.setBrush(p['color'])
            size = p['size']
            painter.drawEllipse(p['x'] - size/2, p['y'] - size/2, size, size)
            
            # 为部分粒子添加轻微的发光效果
            if size > 2:
                glow = QColor(p['color'])
                glow.setAlpha(50)
                painter.setBrush(glow)
                painter.drawEllipse(p['x'] - size, p['y'] - size, size * 2, size * 2)
        
class HexEffect(QWidget):
    """六边形网格效果"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.hexagons = []
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_hexagons)
        self.timer.start(100)  # 每100毫秒更新一次
        self.alpha_direction = 1  # 透明度变化方向
        self.current_alpha = 40  # 初始透明度
        
    def update_hexagons(self):
        # 更新六边形透明度
        self.current_alpha += self.alpha_direction
        if self.current_alpha >= 60:  # 最大透明度
            self.alpha_direction = -1
        elif self.current_alpha <= 20:  # 最小透明度
            self.alpha_direction = 1
            
        self.update()  # 触发重绘
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        hex_size = 60  # 六边形大小
        width = self.width()
        height = self.height()
        
        # 计算六边形网格
        horizontal_spacing = hex_size * 1.5
        vertical_spacing = hex_size * 0.866 * 2  # sqrt(3)/2 * 2 * hex_size
        
        rows = int(height / vertical_spacing) + 2
        cols = int(width / horizontal_spacing) + 2
        
        color = QColor(0, 180, 220, self.current_alpha)
        painter.setPen(QPen(QColor(0, 220, 255, 80), 1))
        
        for row in range(rows):
            for col in range(cols):
                x = col * horizontal_spacing
                y = row * vertical_spacing
                
                # 偶数行需要偏移
                if row % 2 == 1:
                    x += hex_size * 0.75
                
                # 绘制六边形
                painter.setBrush(QBrush(color))
                self.draw_hexagon(painter, x, y, hex_size)
                
    def draw_hexagon(self, painter, x, y, size):
        """绘制六边形"""
        points = []
        for i in range(6):
            angle_deg = 60 * i - 30
            angle_rad = 3.14159 * angle_deg / 180
            point_x = x + size * 0.5 * math.cos(angle_rad)
            point_y = y + size * 0.5 * math.sin(angle_rad)
            points.append(QPoint(point_x, point_y))
            
        painter.drawPolygon(points)

class CircuitEffect(QWidget):
    """电路板效果"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.circuit_points = []
        self.circuit_lines = []
        self.pulse_positions = {}  # 线路上的脉冲位置
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_pulses)
        self.timer.start(50)  # 每50毫秒更新一次
        
    def generate_circuits(self, width, height):
        """生成电路图案"""
        self.circuit_points = []
        self.circuit_lines = []
        self.pulse_positions = {}
        
        # 网格大小
        cell_size = 100
        cols = width // cell_size + 1
        rows = height // cell_size + 1
        
        # 生成网格点
        for row in range(rows):
            for col in range(cols):
                # 添加一些随机性
                jitter_x = (float(os.urandom(1)[0]) / 255.0 - 0.5) * cell_size * 0.5
                jitter_y = (float(os.urandom(1)[0]) / 255.0 - 0.5) * cell_size * 0.5
                
                x = col * cell_size + jitter_x
                y = row * cell_size + jitter_y
                
                self.circuit_points.append((x, y))
        
        # 生成线条连接
        for i, point1 in enumerate(self.circuit_points):
            # 找到最近的几个点
            distances = []
            for j, point2 in enumerate(self.circuit_points):
                if i != j:
                    dx = point1[0] - point2[0]
                    dy = point1[1] - point2[1]
                    distance = (dx * dx + dy * dy) ** 0.5
                    if distance < cell_size * 1.8:  # 只连接较近的点
                        distances.append((distance, j))
            
            # 最多连接3条线
            distances.sort()
            for k in range(min(3, len(distances))):
                j = distances[k][1]
                if i < j:  # 避免重复添加
                    self.circuit_lines.append((i, j))
                    # 初始化脉冲位置，20%的线有脉冲
                    if float(os.urandom(1)[0]) / 255.0 < 0.2:
                        self.pulse_positions[(i, j)] = 0.0
    
    def update_pulses(self):
        """更新脉冲位置"""
        # 更新现有脉冲
        keys_to_remove = []
        for line, pos in self.pulse_positions.items():
            self.pulse_positions[line] = pos + 0.02  # 脉冲前进速度
            if self.pulse_positions[line] > 1.0:
                keys_to_remove.append(line)
        
        # 移除完成的脉冲
        for key in keys_to_remove:
            del self.pulse_positions[key]
        
        # 随机添加新脉冲
        if len(self.circuit_lines) > 0 and len(self.pulse_positions) < len(self.circuit_lines) * 0.2:
            if float(os.urandom(1)[0]) / 255.0 < 0.1:  # 10%几率添加新脉冲
                line_idx = int(float(os.urandom(1)[0]) / 255.0 * len(self.circuit_lines))
                # 确保索引不超出范围
                line_idx = min(line_idx, len(self.circuit_lines) - 1)
                line = self.circuit_lines[line_idx]
                if line not in self.pulse_positions:
                    self.pulse_positions[line] = 0.0
        
        self.update()  # 触发重绘
        
    def paintEvent(self, event):
        # 如果还没有生成电路，则生成
        if not self.circuit_points:
            self.generate_circuits(self.width(), self.height())
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制线条
        painter.setPen(QPen(QColor(0, 180, 220, 40), 1))
        for i, j in self.circuit_lines:
            p1 = self.circuit_points[i]
            p2 = self.circuit_points[j]
            painter.drawLine(p1[0], p1[1], p2[0], p2[1])
        
        # 绘制脉冲
        for line, pos in self.pulse_positions.items():
            i, j = line
            p1 = self.circuit_points[i]
            p2 = self.circuit_points[j]
            
            # 计算脉冲位置
            pulse_x = p1[0] + (p2[0] - p1[0]) * pos
            pulse_y = p1[1] + (p2[1] - p1[1]) * pos
            
            # 绘制脉冲（亮点）
            gradient = QRadialGradient(pulse_x, pulse_y, 10)
            gradient.setColorAt(0, QColor(0, 230, 255, 200))
            gradient.setColorAt(1, QColor(0, 230, 255, 0))
            
            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(pulse_x - 10, pulse_y - 10, 20, 20)
            
        # 绘制交叉点
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(0, 200, 220, 100)))
        for point in self.circuit_points:
            painter.drawEllipse(point[0] - 3, point[1] - 3, 6, 6)
        
class CustomSplashScreen(QSplashScreen):
    """自定义启动屏幕"""
    def __init__(self):
        super().__init__()
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        
        # 获取屏幕尺寸并全屏显示
        desktop = QDesktopWidget().availableGeometry()
        self.screen_width = desktop.width()
        self.screen_height = desktop.height()
        self.setGeometry(0, 0, self.screen_width, self.screen_height)
        
        # 创建基础窗口
        self.setStyleSheet("""
            QSplashScreen {
                background-color: #0a1a2a;
                border: 0px;
            }
        """)
        
        # 创建中央组件来布局内容
        self.central_widget = QWidget(self)
        self.central_widget.setGeometry(0, 0, self.screen_width, self.screen_height)
        
        # 主布局
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(15)
        
        # 添加空白占位
        self.layout.addStretch(1)
        
        # 添加标题
        self.title_label = QLabel("森林多模态灾害监测系统", self)
        self.title_label.setAlignment(Qt.AlignCenter)
        font = QFont("Microsoft YaHei", 42, QFont.Bold)
        self.title_label.setFont(font)
        self.title_label.setStyleSheet("color: #00e6e6; margin-top: 20px;")
        self.layout.addWidget(self.title_label)
        
        # 添加英文副标题
        self.subtitle_label = QLabel("Forest Multi-modal Disaster Monitoring System", self)
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_font = QFont("Arial", 20)
        subtitle_font.setItalic(True)
        self.subtitle_label.setFont(subtitle_font)
        self.subtitle_label.setStyleSheet("color: #99f2ff; margin-bottom: 20px;")
        self.layout.addWidget(self.subtitle_label)
        
        # 添加分隔线
        self.separator = QFrame(self)
        self.separator.setFrameShape(QFrame.HLine)
        self.separator.setStyleSheet("background-color: #00a0c0; margin: 20px 200px;")
        self.separator.setFixedHeight(3)
        self.layout.addWidget(self.separator)
        
        # 添加加载动画
        self.animation_label = QLabel(self)
        self.animation_label.setAlignment(Qt.AlignCenter)
        # 检查GIF文件是否存在，否则使用替代动画
        animation_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ui', 'assets', 'loading.gif')
        if os.path.exists(animation_path):
            try:
                self.animation = QMovie(animation_path)
                self.animation.setScaledSize(QSize(200, 200))
                self.animation_label.setMovie(self.animation)
                self.animation.start()
            except Exception as e:
                print(f"加载动画文件失败: {e}")
                self.animation_label.setText("系统初始化中...")
                self.animation_label.setStyleSheet("color: #99f2ff; font-size: 24px;")
        else:
            # 使用文本代替动画
            self.animation_label.setText("系统初始化中...")
            self.animation_label.setStyleSheet("color: #99f2ff; font-size: 24px;")
            print(f"动画文件不存在: {animation_path}")
        
        self.layout.addWidget(self.animation_label)
        
        # 添加状态标签
        self.status_label = QLabel("正在加载组件...", self)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #99f2ff; font-size: 20px; margin-top: 20px;")
        self.layout.addWidget(self.status_label)
        
        # 添加进度条
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(10)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #001824;
                border: 1px solid #004080;
                border-radius: 5px;
                margin: 10px 100px;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0.5, x2:1, y2:0.5, stop:0 #00ccff, stop:1 #00ffcc);
                border-radius: 5px;
            }
        """)
        self.layout.addWidget(self.progress_bar)
        
        # 添加空白占位
        self.layout.addStretch(2)
        
        # 添加版本信息
        self.version_label = QLabel("版本 1.0.0  |  © 2025 火眼金睛灾害监测技术实验室", self)
        self.version_label.setAlignment(Qt.AlignCenter)
        self.version_label.setStyleSheet("color: #4db8ff; font-size: 14px; margin-bottom: 20px;")
        self.layout.addWidget(self.version_label)
        
        # 添加底部说明
        self.bottom_label = QLabel("正在启动...", self)
        self.bottom_label.setAlignment(Qt.AlignCenter)
        self.bottom_label.setStyleSheet("color: #6698ff; font-size: 12px; margin-bottom: 10px;")
        self.layout.addWidget(self.bottom_label)
        
        # 添加背景效果
        self.circuit_effect = CircuitEffect(self)
        self.circuit_effect.setGeometry(0, 0, self.screen_width, self.screen_height)
        
        # 添加粒子效果
        self.particle_effect = ParticleEffect(self)
        self.particle_effect.setGeometry(0, 0, self.screen_width, self.screen_height)
        
        # 初始化进度计时器
        self.progress_timer = QTimer(self)
        self.progress_timer.timeout.connect(self.update_progress)
        self.current_progress = 0
        
        # 状态消息列表
        self.status_messages = [
            "加载核心模块...",
            "初始化灾害检测模型...",
            "配置多模态数据源...",
            "加载地理信息系统...",
            "初始化摄像头监控模块...",
            "配置告警系统...",
            "连接云端数据中心...",
            "准备AI分析引擎...",
            "系统启动完成，正在进入主界面..."
        ]
        self.current_message_index = 0
        
        # 效果定时器
        self.effect_timer = QTimer(self)
        self.effect_timer.timeout.connect(self.update_effects)
        self.effect_timer.start(100)
        
        # 效果变量
        self.title_phase = 0
        self.glow_value = 0
        self.glow_direction = 1
        
    def update_effects(self):
        """更新视觉效果"""
        # 标题发光效果
        self.glow_value += self.glow_direction * 2
        if self.glow_value > 100:
            self.glow_value = 100
            self.glow_direction = -1
        elif self.glow_value < 0:
            self.glow_value = 0
            self.glow_direction = 1
            
        glow_color = f"rgba(0, {180 + self.glow_value//2}, {220 + self.glow_value//3}, 0.8)"
        self.title_label.setStyleSheet(f"color: #00e6e6; margin-top: 20px; text-shadow: 0 0 15px {glow_color};")
        
        # 底部提示变化
        self.title_phase += 1
        if self.title_phase % 50 == 0:
            dots = "." * ((self.title_phase // 10) % 4)
            self.bottom_label.setText(f"正在启动{dots}")
        
    def start_loading(self, duration=5000):
        """开始加载动画，持续duration毫秒"""
        self.progress_timer.start(duration / 100)  # 将持续时间分成100步
        
    def update_progress(self):
        """更新进度和消息"""
        self.current_progress += 1
        self.progress_bar.setValue(self.current_progress)
        
        # 更新状态消息
        if self.current_progress % (100 // len(self.status_messages)) == 0:
            if self.current_message_index < len(self.status_messages):
                self.status_label.setText(self.status_messages[self.current_message_index])
                self.current_message_index += 1
        
        # 完成加载
        if self.current_progress >= 100:
            self.progress_timer.stop()
            QTimer.singleShot(500, self.finish_loading)  # 延迟半秒后完成
    
    def finish_loading(self):
        """完成加载后的处理"""
        # 在实际应用中，这里可以发出加载完成的信号
        pass
            
    def paintEvent(self, event):
        """自定义绘制事件"""
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制背景渐变
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(10, 30, 60))
        gradient.setColorAt(0.5, QColor(5, 20, 40))
        gradient.setColorAt(1, QColor(10, 30, 60))
        painter.fillRect(0, 0, self.width(), self.height(), gradient)
        
        # 绘制边框
        margin = 10
        pen = QPen(QColor(0, 180, 230, 100), 3)
        painter.setPen(pen)
        painter.drawRect(margin, margin, self.width()-margin*2, self.height()-margin*2)
        
        # 绘制顶部和底部装饰线
        painter.setPen(QPen(QColor(0, 180, 230, 150), 2))
        
        # 顶部装饰
        top_margin = 30
        line_width = self.width() * 0.4
        painter.drawLine(self.width()/2 - line_width/2, top_margin, 
                         self.width()/2 + line_width/2, top_margin)
        
        # 左上角装饰
        painter.drawLine(margin*2, top_margin*2, margin*6, top_margin*2)
        painter.drawLine(margin*2, top_margin*2, margin*2, top_margin*5)
        
        # 右上角装饰
        painter.drawLine(self.width()-margin*6, top_margin*2, self.width()-margin*2, top_margin*2)
        painter.drawLine(self.width()-margin*2, top_margin*2, self.width()-margin*2, top_margin*5)
        
        # 底部装饰
        bottom_margin = 30
        painter.drawLine(self.width()/2 - line_width/2, self.height()-bottom_margin, 
                         self.width()/2 + line_width/2, self.height()-bottom_margin)
        
        # 左下角装饰
        painter.drawLine(margin*2, self.height()-top_margin*2, margin*6, self.height()-top_margin*2)
        painter.drawLine(margin*2, self.height()-top_margin*2, margin*2, self.height()-top_margin*5)
        
        # 右下角装饰
        painter.drawLine(self.width()-margin*6, self.height()-top_margin*2, self.width()-margin*2, self.height()-top_margin*2)
        painter.drawLine(self.width()-margin*2, self.height()-top_margin*2, self.width()-margin*2, self.height()-top_margin*5)

def show_splash_screen(app, main_window, duration=5000):
    """显示启动屏幕
    
    Args:
        app: QApplication实例
        main_window: 主窗口实例
        duration: 显示启动屏幕的时间（毫秒）
    """
    splash = CustomSplashScreen()
    splash.show()
    
    # 开始加载动画
    splash.start_loading(duration)
    
    # 设置计时器，在指定时间后隐藏启动屏幕并显示主窗口
    QTimer.singleShot(duration, lambda: finish_splash(splash, main_window))
    
    # 处理事件，确保启动屏幕显示
    app.processEvents()
    
def finish_splash(splash, main_window):
    """完成启动屏幕并显示主窗口"""
    # 淡出效果
    fade_out = QPropertyAnimation(splash, b"windowOpacity")
    fade_out.setDuration(1000)  # 延长淡出时间
    fade_out.setStartValue(1.0)
    fade_out.setEndValue(0.0)
    fade_out.setEasingCurve(QEasingCurve.OutQuad)
    fade_out.finished.connect(splash.close)
    fade_out.start()
    
    # 显示主窗口
    main_window.show()

# 测试代码
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 创建一个简单的主窗口用于测试
    main = QWidget()
    main.setWindowTitle("测试主窗口")
    main.resize(800, 600)
    
    # 显示启动屏幕
    show_splash_screen(app, main, 5000)
    
    sys.exit(app.exec_()) 