import os
import sys
from datetime import datetime
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QTabWidget, QLabel, QPushButton, QComboBox, 
                            QStatusBar, QSplitter, QProgressBar, QAction, 
                            QFileDialog, QMessageBox, QMenu, QGroupBox)
from PyQt5.QtCore import Qt, QTimer, pyqtSlot, QUrl, QSize
from PyQt5.QtGui import QIcon, QPixmap, QFont, QColor, QPainter
from PyQt5.QtWebEngineWidgets import QWebEngineView
import psutil
from PyQt5.QtWidgets import QApplication
import time

from ui.components.map_view import MapView
from ui.components.camera_view import CameraView
from ui.components.alert_panel import AlertPanel
from ui.components.control_panel import ControlPanel
from ui.components.statistics_panel import StatisticsPanel
from ui.components.drone_manager import DroneManager
from ui.components.grid_camera_view import GridCameraView
from PyQt5.QtChart import QChartView, QChart, QPieSeries

class MainWindow(QMainWindow):
    """
    森林多模态灾害监测系统主窗口
    """
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.last_fire_update_time = 0  # 添加上次火灾更新时间记录
        self.fire_update_interval = 5  # 设置最小更新间隔为5秒
        self.last_animal_update = 0  # 添加动物检测更新时间记录
        self.min_update_interval = 5  # 设置最小更新间隔为5秒
        self.init_ui()
        
        # 连接摄像头视图的火灾检测信号
        self.camera_view.fire_detected.connect(self.on_fire_detected)
        
    def init_ui(self):
        """初始化UI界面"""
        # 设置窗口属性
        self.setWindowTitle("森林多模态灾害监测系统")
        self.setGeometry(100, 100, 1280, 800)
        
        # 设置图标
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'icon.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # 创建主布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # 创建顶部工具栏
        self.create_toolbar()
        
        # 创建三栏主分割器
        main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(main_splitter)
        
        # === 左侧栏：控制面板和地图 ===
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # 控制面板
        self.control_panel = ControlPanel(self.config)
        left_layout.addWidget(self.control_panel)
        
        # 地图视图
        self.map_view = MapView(self.config)
        left_layout.addWidget(self.map_view)
        
        # === 中间栏：摄像头视图和告警面板 ===
        middle_panel = QWidget()
        middle_layout = QVBoxLayout(middle_panel)
        middle_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建标签页容器
        camera_tabs = QTabWidget()
        camera_tabs.setTabPosition(QTabWidget.South)
        camera_tabs.setStyleSheet("QTabBar::tab { background-color: #102040; color: white; padding: 6px 12px; margin-right: 2px; border-top-left-radius: 4px; border-top-right-radius: 4px; } QTabBar::tab:selected { background-color: #1a3a5a; }")
        
        # 添加九宫格视图标签页
        self.grid_camera_view = GridCameraView()
        camera_tabs.addTab(self.grid_camera_view, "多路监控")
        
        # 连接九宫格视图的灾害检测信号
        self.grid_camera_view.fire_detected.connect(self.on_fire_detected)
        self.grid_camera_view.animal_detected.connect(self.on_animal_detected)
        
        # 添加单路摄像头视图标签页
        self.camera_view = CameraView(self.config)
        camera_tabs.addTab(self.camera_view, "单路监控")
        
        # 添加无人机管理标签页
        self.drone_manager = DroneManager(self.config)
        camera_tabs.addTab(self.drone_manager, "无人机集群")
        
        # 将标签页容器添加到中间布局
        middle_layout.addWidget(camera_tabs, 7)  # 占70%高度
        
        # 告警面板
        self.alert_panel = AlertPanel(self.config)
        middle_layout.addWidget(self.alert_panel, 3)  # 占30%高度
        
        # 连接告警面板的信号
        self.alert_panel.alert_added.connect(self.on_alert_added)
        # 连接告警处理信号
        self.alert_panel.alert_processed.connect(self.on_alert_processed)
        
        # === 右侧栏：统计信息面板 ===
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(5)
        right_panel.setStyleSheet("background-color: #0a1a2a; "
                               "QGroupBox { background-color: #102040; border: 1px solid #1e3a5a; border-radius: 5px; margin-top: 8px; } "
                               "QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px; color: white; font-weight: bold; }"
                               "QLabel { color: white; }"
                               "QComboBox { color: white; background-color: #1a3a5a; border: 1px solid #2a4a6a; }"
                               "QPushButton { color: white; background-color: #1a3a5a; border: 1px solid #2a4a6a; }")
        
        # 标题标签
        stats_title = QLabel("统计信息")
        stats_title.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        stats_title.setStyleSheet("color: white; margin: 5px;")
        stats_title.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(stats_title)
        
        # 创建统计面板
        self.statistics_panel = StatisticsPanel(self.config)
        
        # ==== 概览部分 ====
        overview_group = QGroupBox("告警概览")
        overview_group.setObjectName("overview_group")
        overview_layout = QVBoxLayout(overview_group)
        overview_layout.setContentsMargins(5, 10, 5, 10)  # 设置合适的边距
        
        # 告警统计数字
        stats_layout = QHBoxLayout()
        fire_label = QLabel(f"火灾告警: {self.statistics_panel.alert_stats['fire']}")
        fire_label.setObjectName("fire_overview")
        fire_label.setStyleSheet("color: #ff6666; font-weight: bold;")
        
        animal_label = QLabel(f"动物告警: {self.statistics_panel.alert_stats['animal']}")
        animal_label.setObjectName("animal_overview")
        animal_label.setStyleSheet("color: #66ff66; font-weight: bold;")
        
        landslide_label = QLabel(f"滑坡告警: {self.statistics_panel.alert_stats['landslide']}")
        landslide_label.setObjectName("landslide_overview")
        landslide_label.setStyleSheet("color: #6666ff; font-weight: bold;")
        
        pest_label = QLabel(f"病虫害: {self.statistics_panel.alert_stats['pest']}")
        pest_label.setObjectName("pest_overview")
        pest_label.setStyleSheet("color: #cc99ff; font-weight: bold;")
        
        stats_layout.addWidget(fire_label)
        stats_layout.addWidget(animal_label)
        stats_layout.addWidget(landslide_label)
        stats_layout.addWidget(pest_label)
        overview_layout.addLayout(stats_layout)
        
        # 饼图视图
        pie_chart = self.statistics_panel.create_pie_chart()
        pie_chart.setObjectName("overview_pie_chart")
        pie_chart.setMinimumHeight(250)  # 设置最小高度
        pie_chart.setFixedHeight(250)    # 设置固定高度，防止尺寸变化
        overview_layout.addWidget(pie_chart)
        
        right_layout.addWidget(overview_group)
        
        # ==== 趋势图部分 ====
        trend_group = QGroupBox("告警趋势")
        trend_group.setObjectName("trend_group")
        trend_layout = QVBoxLayout(trend_group)
        trend_layout.setContentsMargins(5, 10, 5, 10)  # 设置合适的边距
        
        # 时间范围选择器
        time_range_layout = QHBoxLayout()
        time_range_layout.addWidget(QLabel("时间范围:"))
        time_range_combo = QComboBox()
        time_range_combo.setObjectName("time_range_combo")
        time_range_combo.addItems(["最近24小时", "最近7天", "最近30天", "本月", "本年"])
        time_range_combo.currentIndexChanged.connect(self.statistics_panel.change_time_range)
        time_range_layout.addWidget(time_range_combo)
        time_range_layout.addStretch(1)
        trend_layout.addLayout(time_range_layout)
        
        # 趋势图视图
        trend_chart = self.statistics_panel.create_trend_chart_view()
        trend_chart.setObjectName("trend_chart_view")
        trend_chart.setMinimumHeight(280)  # 设置最小高度
        trend_chart.setFixedHeight(280)    # 设置固定高度，防止尺寸变化
        trend_layout.addWidget(trend_chart)
        
        right_layout.addWidget(trend_group)
        
        # ==== 区域统计部分 ====
        region_group = QGroupBox("区域统计")
        region_group.setObjectName("region_group")
        region_layout = QVBoxLayout(region_group)
        region_layout.setContentsMargins(5, 10, 5, 10)  # 设置合适的边距
        
        # 区域统计图表
        region_chart = self.statistics_panel.create_region_chart_view()
        region_chart.setObjectName("region_chart_view")
        region_chart.setMinimumHeight(280)  # 设置最小高度
        region_chart.setFixedHeight(280)    # 设置固定高度，防止尺寸变化
        region_layout.addWidget(region_chart)
        
        right_layout.addWidget(region_group)
        
        # 刷新按钮
        refresh_btn = QPushButton("刷新统计信息")
        refresh_btn.clicked.connect(self.statistics_panel.refresh_statistics)
        right_layout.addWidget(refresh_btn)
        
        # 将三个面板添加到主分割器
        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(middle_panel)
        main_splitter.addWidget(right_panel)
        
        # 设置三栏分割比例
        main_splitter.setSizes([int(self.width() * 0.2), int(self.width() * 0.55), int(self.width() * 0.25)])
        
        # 创建状态栏
        self.create_statusbar()
        
        # 创建定时器，定期更新UI
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_ui)
        self.update_timer.start(5000)  # 每5秒更新一次
        
        # 应用暗色/亮色主题
        self.apply_theme()
        
    def create_toolbar(self):
        """创建工具栏"""
        self.toolbar = self.addToolBar("主工具栏")
        self.toolbar.setMovable(False)
        
        # 添加启动监控按钮
        start_action = QAction(QIcon(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'start.png')), "启动监控", self)
        start_action.triggered.connect(self.start_monitoring)
        self.toolbar.addAction(start_action)
        
        # 添加停止监控按钮
        stop_action = QAction(QIcon(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'stop.png')), "停止监控", self)
        stop_action.triggered.connect(self.stop_monitoring)
        self.toolbar.addAction(stop_action)
        
        self.toolbar.addSeparator()
        
        # 添加无人机控制菜单
        drone_menu = QMenu("无人机", self)
        
        # 添加起飞所有无人机动作
        takeoff_all_action = QAction(QIcon(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'takeoff.png')), "起飞所有无人机", self)
        takeoff_all_action.triggered.connect(self.takeoff_all_drones)
        drone_menu.addAction(takeoff_all_action)
        
        # 添加返航所有无人机动作
        return_all_action = QAction(QIcon(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'return.png')), "返航所有无人机", self)
        return_all_action.triggered.connect(self.return_all_drones)
        drone_menu.addAction(return_all_action)
        
        # 添加紧急停止所有无人机动作
        emergency_action = QAction(QIcon(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'emergency.png')), "紧急停止所有无人机", self)
        emergency_action.triggered.connect(self.emergency_stop_all_drones)
        drone_menu.addAction(emergency_action)
        
        # 添加无人机菜单按钮
        drone_action = QAction(QIcon(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'drone.png')), "无人机控制", self)
        drone_action.setMenu(drone_menu)
        self.toolbar.addAction(drone_action)
        
        self.toolbar.addSeparator()
        
        # 添加导入数据按钮
        import_action = QAction(QIcon(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'import.png')), "导入数据", self)
        import_action.triggered.connect(self.import_data)
        self.toolbar.addAction(import_action)
        
        # 添加导出报告按钮
        export_action = QAction(QIcon(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'export.png')), "导出报告", self)
        export_action.triggered.connect(self.export_report)
        self.toolbar.addAction(export_action)
        
        self.toolbar.addSeparator()
        
        # 添加设置按钮
        settings_action = QAction(QIcon(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'settings.png')), "设置", self)
        settings_action.triggered.connect(self.show_settings)
        self.toolbar.addAction(settings_action)
        
        # 添加帮助按钮
        help_action = QAction(QIcon(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'help.png')), "帮助", self)
        help_action.triggered.connect(self.show_help)
        self.toolbar.addAction(help_action)
        
    def create_statusbar(self):
        """创建状态栏"""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        
        # 添加系统状态标签
        self.status_label = QLabel("系统状态: 待机")
        self.statusbar.addWidget(self.status_label)
        
        # 添加CPU使用率进度条
        self.cpu_label = QLabel("CPU: ")
        self.statusbar.addPermanentWidget(self.cpu_label)
        
        self.cpu_progress = QProgressBar()
        self.cpu_progress.setMaximumWidth(100)
        self.cpu_progress.setMaximumHeight(16)
        self.cpu_progress.setRange(0, 100)
        self.cpu_progress.setValue(0)
        self.statusbar.addPermanentWidget(self.cpu_progress)
        
        # 添加内存使用率进度条
        self.memory_label = QLabel("内存: ")
        self.statusbar.addPermanentWidget(self.memory_label)
        
        self.memory_progress = QProgressBar()
        self.memory_progress.setMaximumWidth(100)
        self.memory_progress.setMaximumHeight(16)
        self.memory_progress.setRange(0, 100)
        self.memory_progress.setValue(0)
        self.statusbar.addPermanentWidget(self.memory_progress)
        
        # 添加时间标签
        self.time_label = QLabel()
        self.update_time()  # 初始化时间
        self.statusbar.addPermanentWidget(self.time_label)
        
        # 创建时间更新定时器
        self.time_timer = QTimer(self)
        self.time_timer.timeout.connect(self.update_time)
        self.time_timer.start(1000)  # 每秒更新一次
        
    def update_time(self):
        """更新状态栏时间"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.setText(current_time)
        
    def apply_theme(self):
        """应用主题"""
        if self.config.get('dark_mode', True):
            # 应用暗色主题
            self.setStyleSheet("""
                QMainWindow, QWidget {
                    background-color: #2D2D30;
                    color: #FFFFFF;
                }
                QTabWidget::pane {
                    border: 1px solid #3F3F46;
                    background-color: #252526;
                }
                QTabBar::tab {
                    background-color: #2D2D30;
                    color: #FFFFFF;
                    padding: 5px 15px;
                    border: 1px solid #3F3F46;
                }
                QTabBar::tab:selected {
                    background-color: #007ACC;
                }
                QPushButton {
                    background-color: #0E639C;
                    color: white;
                    border: none;
                    padding: 5px 15px;
                    border-radius: 2px;
                }
                QPushButton:hover {
                    background-color: #1177BB;
                }
                QPushButton:pressed {
                    background-color: #13669C;
                }
            """)
        else:
            # 应用亮色主题
            self.setStyleSheet("")
        
    def update_ui(self):
        """定期更新UI界面"""
        # 更新系统状态
        self.status_label.setText("系统状态: 正常运行中")
        
        # 获取真实CPU和内存使用率
        cpu_usage = psutil.cpu_percent()
        memory_usage = psutil.virtual_memory().percent
        
        self.cpu_progress.setValue(cpu_usage)
        self.memory_progress.setValue(memory_usage)
        
        # 更新子组件
        self.camera_view.update_view()
        self.map_view.update_view()
        self.alert_panel.update_alerts()
        self.statistics_panel.update_statistics()
        
        # 添加无人机组件更新
        if hasattr(self, 'drone_manager'):
            self.drone_manager.update_drone_display()
        
        # 更新右侧概览面板的统计数据
        self.update_overview_stats()
        
    @pyqtSlot()
    def start_monitoring(self):
        """启动监控"""
        self.status_label.setText("系统状态: 监控中")
        self.camera_view.start_monitoring()
        # 更新其他组件状态
        
    @pyqtSlot()
    def stop_monitoring(self):
        """停止监控"""
        self.status_label.setText("系统状态: 已停止")
        self.camera_view.stop_monitoring()
        # 更新其他组件状态
        
    @pyqtSlot()
    def import_data(self):
        """导入数据"""
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter("数据文件 (*.csv *.json *.zip)")
        
        if file_dialog.exec_():
            file_paths = file_dialog.selectedFiles()
            if file_paths:
                # 处理导入文件
                QMessageBox.information(self, "导入数据", f"已选择导入文件: {file_paths[0]}")
                
    @pyqtSlot()
    def export_report(self):
        """导出报告"""
        file_dialog = QFileDialog()
        file_dialog.setAcceptMode(QFileDialog.AcceptSave)
        file_dialog.setNameFilter("报告文件 (*.pdf *.docx *.html)")
        
        if file_dialog.exec_():
            file_paths = file_dialog.selectedFiles()
            if file_paths:
                # 处理导出报告
                QMessageBox.information(self, "导出报告", f"报告将保存到: {file_paths[0]}")
                
    @pyqtSlot()
    def show_settings(self):
        """显示设置对话框"""
        self.tab_widget.setCurrentIndex(3)  # 切换到设置页面
        
    @pyqtSlot()
    def show_help(self):
        """显示帮助信息"""
        QMessageBox.information(self, "帮助", "森林多模态灾害监测系统\n版本: 1.0.0\n\n基于YOLOv5的智能监测系统，用于森林火灾、滑坡、动物盗猎等多灾害监测。")
        
    @pyqtSlot()
    def takeoff_all_drones(self):
        """起飞所有无人机"""
        if hasattr(self, 'drone_manager'):
            # 切换到无人机管理标签页
            for i in range(4):  # 假设标签页在索引1-3
                if "无人机" in self.findChildren(QTabWidget)[i].tabText(1):
                    self.findChildren(QTabWidget)[i].setCurrentIndex(1)
                    break
            
            # 修改所有无人机状态为已起飞
            for drone_id, drone in self.drone_manager.drones.items():
                drone.status = "已起飞"
            
            # 更新状态表格
            self.drone_manager.update_status_table()
            
            QMessageBox.information(self, "无人机控制", "已发送起飞命令至所有无人机")
    
    @pyqtSlot()
    def return_all_drones(self):
        """返航所有无人机"""
        if hasattr(self, 'drone_manager'):
            # 切换到无人机管理标签页
            for i in range(4):  # 假设标签页在索引1-3
                if "无人机" in self.findChildren(QTabWidget)[i].tabText(1):
                    self.findChildren(QTabWidget)[i].setCurrentIndex(1)
                    break
            
            # 修改所有无人机状态为返航中
            for drone_id, drone in self.drone_manager.drones.items():
                drone.status = "返航中"
            
            # 更新状态表格
            self.drone_manager.update_status_table()
            
            QMessageBox.information(self, "无人机控制", "已发送返航命令至所有无人机")
    
    @pyqtSlot()
    def emergency_stop_all_drones(self):
        """紧急停止所有无人机"""
        if hasattr(self, 'drone_manager'):
            reply = QMessageBox.warning(self, "紧急停止确认", 
                                       "确定要紧急停止所有无人机吗？这可能导致无人机坠落！", 
                                       QMessageBox.Yes | QMessageBox.No,
                                       QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                # 切换到无人机管理标签页
                for i in range(4):  # 假设标签页在索引1-3
                    if "无人机" in self.findChildren(QTabWidget)[i].tabText(1):
                        self.findChildren(QTabWidget)[i].setCurrentIndex(1)
                        break
                
                # 修改所有无人机状态为紧急停止
                for drone_id, drone in self.drone_manager.drones.items():
                    drone.status = "紧急停止"
                
                # 更新状态表格
                self.drone_manager.update_status_table()
                
                QMessageBox.critical(self, "无人机控制", "已发送紧急停止命令至所有无人机")
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        reply = QMessageBox.question(self, '退出确认', 
                                    "确定要退出系统吗？", 
                                    QMessageBox.Yes | QMessageBox.No,
                                    QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            # 停止所有正在运行的线程和定时器
            self.update_timer.stop()
            self.time_timer.stop()
            self.camera_view.stop_monitoring()
            
            # 停止所有无人机
            if hasattr(self, 'drone_manager'):
                for drone in self.drone_manager.drones.values():
                    drone.stop()
            
            event.accept()
        else:
            event.ignore()

    def update_overview_stats(self):
        """更新右侧统计面板中的数据显示"""
        # 更新告警概览组的统计数字
        fire_label = self.findChild(QLabel, "fire_overview")
        if fire_label:
            fire_label.setText(f"火灾告警: {self.statistics_panel.alert_stats['fire']}")
            
        animal_label = self.findChild(QLabel, "animal_overview")
        if animal_label:
            animal_label.setText(f"动物告警: {self.statistics_panel.alert_stats['animal']}")
            
        landslide_label = self.findChild(QLabel, "landslide_overview")
        if landslide_label:
            landslide_label.setText(f"滑坡告警: {self.statistics_panel.alert_stats['landslide']}")
            
        pest_label = self.findChild(QLabel, "pest_overview")
        if pest_label:
            pest_label.setText(f"病虫害: {self.statistics_panel.alert_stats['pest']}")
            
        # 更新各个图表
        self.update_overview_chart()
        self.update_trend_chart()
        self.update_region_chart()

    def update_overview_chart(self):
        """更新右侧统计面板中的饼图"""
        # 获取当前概览组中的饼图
        overview_group = self.findChild(QGroupBox, "overview_group")
        if overview_group:
            # 获取旧的饼图视图
            old_chart_view = None
            for i in range(overview_group.layout().count()):
                item = overview_group.layout().itemAt(i)
                if item and item.widget() and isinstance(item.widget(), QChartView):
                    old_chart_view = item.widget()
                    break
            
            if old_chart_view:
                # 创建新的饼图
                new_chart_view = self.statistics_panel.create_pie_chart()
                new_chart_view.setObjectName("overview_pie_chart")
                new_chart_view.setMinimumHeight(250)  # 设置最小高度
                new_chart_view.setFixedHeight(250)    # 设置固定高度，防止尺寸变化
                
                # 替换旧的饼图
                layout = overview_group.layout()
                layout.replaceWidget(old_chart_view, new_chart_view)
                old_chart_view.deleteLater() 

    def update_trend_chart(self):
        """更新趋势图"""
        trend_group = self.findChild(QGroupBox, "trend_group")
        if trend_group:
            # 获取旧的趋势图
            old_chart_view = trend_group.findChild(QChartView, "trend_chart_view")
            if old_chart_view:
                # 创建新的趋势图
                new_chart_view = self.statistics_panel.create_trend_chart_view()
                new_chart_view.setObjectName("trend_chart_view")
                
                # 保持尺寸一致
                new_chart_view.setMinimumHeight(280)
                new_chart_view.setFixedHeight(280)
                
                # 替换旧的趋势图
                layout = trend_group.layout()
                for i in range(layout.count()):
                    item = layout.itemAt(i)
                    if item.widget() == old_chart_view:
                        layout.replaceWidget(old_chart_view, new_chart_view)
                        old_chart_view.deleteLater()
                        break
    
    def update_region_chart(self):
        """更新区域统计图"""
        region_group = self.findChild(QGroupBox, "region_group")
        if region_group:
            # 获取旧的区域图
            old_chart_view = region_group.findChild(QChartView, "region_chart_view")
            if old_chart_view:
                # 创建新的区域图
                new_chart_view = self.statistics_panel.create_region_chart_view()
                new_chart_view.setObjectName("region_chart_view")
                
                # 保持尺寸一致
                new_chart_view.setMinimumHeight(280)
                new_chart_view.setFixedHeight(280)
                
                # 替换旧的区域图
                layout = region_group.layout()
                for i in range(layout.count()):
                    item = layout.itemAt(i)
                    if item.widget() == old_chart_view:
                        layout.replaceWidget(old_chart_view, new_chart_view)
                        old_chart_view.deleteLater()
                        print("已更新区域统计图")
                        break
            else:
                print("警告: 未找到区域图表视图")
        else:
            print("警告: 未找到区域统计组")

    def on_alert_added(self, alert_type, region):
        """处理新告警信号，更新统计面板"""
        print(f"主窗口收到新告警: 类型={alert_type}, 区域={region}")
        
        # 调用统计面板的方法处理新告警
        self.statistics_panel.handle_new_alert(alert_type, region)
        
        # 立即更新右侧统计信息显示
        self.update_overview_stats()
        
        # 强制更新区域图表
        self.update_region_chart()
        
        # 重置随机更新定时器，避免冲突
        self.statistics_panel.update_timer.stop()
        self.statistics_panel.update_timer.start(10000)  # 增加到10秒，减少干扰
        
        # 强制立即刷新所有图表
        QApplication.processEvents()  # 确保UI更新立即可见 

    def on_alert_processed(self, alert_type, region):
        """处理告警处理信号，更新统计面板"""
        print(f"主窗口收到告警处理: 类型={alert_type}, 区域={region}")
        
        # 调用统计面板的方法处理告警处理
        self.statistics_panel.handle_alert_processed(alert_type, region)
        
        # 立即更新右侧统计信息显示
        self.update_overview_stats()
        
        # 强制更新区域图表
        self.update_region_chart()
        
        # 重置随机更新定时器，避免冲突
        self.statistics_panel.update_timer.stop()
        self.statistics_panel.update_timer.start(10000)  # 增加到10秒，减少干扰
        
        # 强制立即刷新所有图表
        QApplication.processEvents()  # 确保UI更新立即可见 

    def on_fire_detected(self, region):
        """处理火灾检测信号"""
        current_time = datetime.now().timestamp()
        # 检查是否达到最小更新间隔
        if current_time - self.last_fire_update_time < self.fire_update_interval:
            return  # 如果间隔太短，直接返回不处理
            
        print(f"收到火灾检测信号，区域：{region}")
        # 更新上次处理时间
        self.last_fire_update_time = current_time
        
        # 创建并添加告警
        alert = {
            'type': 'fire',
            'location': region,
            'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'detail': '检测到火灾隐患',
            'level': 'high',
            'status': '未处理'
        }
        self.alert_panel.add_alert(alert)  # 这会触发alert_added信号，统计更新将在on_alert_added中处理 

    def on_animal_detected(self, image, species, confidence):
        """处理动物检测信号"""
        current_time = time.time()
        if current_time - self.last_animal_update < self.min_update_interval:
            return
            
        self.last_animal_update = current_time
        
        # 创建动物检测告警
        alert = {
            'type': 'animal',
            'location': '未知位置',  # 可以根据摄像头位置更新
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'unprocessed',
            'details': f'检测到{species}，置信度: {confidence:.1f}%',
            'image': image  # 保存检测到动物的图像
        }
        
        # 添加到告警面板
        self.alert_panel.add_alert(alert)
        
        # 调用统计面板的方法处理新告警
        self.statistics_panel.handle_new_alert('animal', '未知位置')
        
        # 立即更新右侧统计信息显示
        self.update_overview_stats()
        
        # 强制更新区域图表
        self.update_region_chart()
        
        # 重置随机更新定时器，避免冲突
        self.statistics_panel.update_timer.stop()
        self.statistics_panel.update_timer.start(10000)  # 增加到10秒，减少干扰
        
        # 强制立即刷新所有图表
        QApplication.processEvents()  # 确保UI更新立即可见 