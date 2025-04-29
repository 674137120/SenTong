import os
import random
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider,
                              QTabWidget, QGroupBox, QComboBox, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import Qt, pyqtSlot, QTimer, QMargins
from PyQt5.QtGui import QFont, QPainter, QPen, QColor
from PyQt5.QtChart import QChart, QChartView, QLineSeries, QBarSet, QBarSeries, QPieSeries, QValueAxis, QDateTimeAxis, QBarCategoryAxis, QLegend

class StatisticsPanel(QWidget):
    """统计面板组件，显示各类灾害检测统计信息和趋势图表"""
    
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        
        # 初始化统计数据
        self.alert_stats = {
            'fire': 0,
            'animal': 0,
            'landslide': 0,
            'pest': 0
        }
        
        # 初始化区域统计数据为空字典
        self.region_stats = {}
        
        # 初始化区域名称映射字典
        self.region_mapping = {
            '北部山区': '东北区',  # 假设北部山区属于东北区
            '南部林区': '东南区',  # 假设南部林区属于东南区
            '东部山脊': '东北区',  # 假设东部山脊属于东北区
            '西部谷地': '西北区',  # 假设西部谷地属于西北区
            '西部林区': '西北区',  # 假设西部林区属于西北区
            '中央林场': '中部区'   # 假设中央林场属于中部区
        }
        
        # 模拟数据
        self.init_mock_data()
        
        # 初始化UI
        self.init_ui()
        
        # 创建并保存趋势图视图的引用
        self.trend_chart_view = self.create_trend_chart_view()
        
        # 设置自动更新定时器
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.auto_update_statistics)
        self.update_timer.start(5000)  # 每5秒更新一次统计数据
        
    def init_mock_data(self):
        """初始化模拟数据"""
        # 病虫害类型统计数据
        self.pest_type_stats = {
            '松材线虫': 0,
            '杨树食叶害虫': 0,
            '松毛虫': 0,
            '蚜虫': 0,
            '松墨天牛': 0,
            '落叶松针叶锈病': 0
        }
        
        # 初始化区域统计字典
        if not self.region_stats:
            self.region_stats = {
                '东北区': 0,
                '西北区': 0,
                '中部区': 0,
                '东南区': 0,
                '西南区': 0
            }
        
        # 模拟24小时数据
        self.hour_data = []
        now = datetime.now()
        for i in range(24):
            time_point = now - timedelta(hours=23-i)
            self.hour_data.append({
                'time': time_point,
                'fire': 0,
                'animal': 0,
                'landslide': 0,
                'forest_degradation': 0,
                'pest': 0
            })
        
        # 模拟7天数据
        self.day_data = []
        for i in range(7):
            time_point = now - timedelta(days=6-i)
            self.day_data.append({
                'time': time_point,
                'fire': 0,
                'animal': 0,
                'landslide': 0,
                'forest_degradation': 0,
                'pest': 0
            })
        
        # 模拟30天数据
        self.month_data = []
        for i in range(30):
            time_point = now - timedelta(days=29-i)
            self.month_data.append({
                'time': time_point,
                'fire': 0,
                'animal': 0,
                'landslide': 0,
                'forest_degradation': 0,
                'pest': 0
            })
        
    def init_ui(self):
        """初始化UI"""
        # 创建主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        
        # 概览标签页
        overview_tab = self.create_overview_tab()
        self.tab_widget.addTab(overview_tab, "概览")
        
        # 趋势图标签页
        trend_tab = self.create_trend_tab()
        self.tab_widget.addTab(trend_tab, "趋势图")
        
        # 区域统计标签页
        region_tab = self.create_region_tab()
        self.tab_widget.addTab(region_tab, "区域统计")
        
        # 添加标签页到布局
        layout.addWidget(self.tab_widget)
        
        # 底部工具栏
        toolbar = QHBoxLayout()
        
        # 时间范围下拉框
        self.time_range_combo = QComboBox()
        self.time_range_combo.addItems(["最近24小时", "最近7天", "最近30天", "本月", "本年"])
        self.time_range_combo.currentIndexChanged.connect(self.change_time_range)
        toolbar.addWidget(QLabel("时间范围:"))
        toolbar.addWidget(self.time_range_combo)
        
        # 添加刷新按钮
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.refresh_statistics)
        toolbar.addStretch(1)
        toolbar.addWidget(refresh_btn)
        
        # 添加工具栏到布局
        layout.addLayout(toolbar)
        
        # 设置最小高度
        self.setMinimumHeight(300)
        
    def create_overview_tab(self):
        """创建概览标签页"""
        tab = QWidget()
        tab.setObjectName("overview_tab")  # 添加对象名称
        layout = QVBoxLayout(tab)
        
        # 告警统计
        stats_group = QGroupBox("告警统计")
        stats_group.setObjectName("stats_group")  # 添加对象名称
        stats_layout = QHBoxLayout(stats_group)
        
        # 火灾告警
        fire_label = QLabel(f"火灾告警: {self.alert_stats['fire']}")
        fire_label.setObjectName("fire_label")  # 添加对象名称
        fire_label.setStyleSheet("color: red;")
        stats_layout.addWidget(fire_label)
        
        # 动物告警
        animal_label = QLabel(f"动物告警: {self.alert_stats['animal']}")
        animal_label.setObjectName("animal_label")  # 添加对象名称
        animal_label.setStyleSheet("color: green;")
        stats_layout.addWidget(animal_label)
        
        # 滑坡告警
        landslide_label = QLabel(f"滑坡告警: {self.alert_stats['landslide']}")
        landslide_label.setObjectName("landslide_label")  # 添加对象名称
        landslide_label.setStyleSheet("color: blue;")
        stats_layout.addWidget(landslide_label)
        
        # 病虫害告警
        pest_label = QLabel(f"病虫害: {self.alert_stats['pest']}")
        pest_label.setObjectName("pest_label")  # 添加对象名称
        pest_label.setStyleSheet("color: purple;")
        stats_layout.addWidget(pest_label)
        
        layout.addWidget(stats_group)
        
        # 饼图 - 使用create_pie_chart方法
        chart_view = self.create_pie_chart()
        chart_view.setObjectName("overview_pie_chart")  # 添加对象名称
        
        layout.addWidget(chart_view)
        
        return tab
        
    def create_trend_tab(self):
        """创建趋势图标签页"""
        tab = QWidget()
        tab.setObjectName("trend_tab")  # 添加对象名称
        layout = QVBoxLayout(tab)
        
        # 24小时趋势图
        trend_chart = QChart()
        trend_chart.setTitle("24小时告警趋势")
        trend_chart.setAnimationOptions(QChart.SeriesAnimations)
        trend_chart.setBackgroundBrush(QColor("#0a1a2a"))
        trend_chart.setTitleBrush(QColor("white"))
        trend_chart.setTitleFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        
        # 创建折线系列 - 火灾
        fire_series = QLineSeries()
        fire_series.setName("火灾告警")
        fire_series.setColor(QColor(255, 100, 100))
        
        # 创建折线系列 - 动物
        animal_series = QLineSeries()
        animal_series.setName("动物告警")
        animal_series.setColor(QColor(100, 255, 100))
        
        # 创建折线系列 - 滑坡
        landslide_series = QLineSeries()
        landslide_series.setName("滑坡告警")
        landslide_series.setColor(QColor(100, 100, 255))
        
        # 创建折线系列 - 病虫害
        pest_series = QLineSeries()
        pest_series.setName("病虫害告警")
        pest_series.setColor(QColor(180, 100, 200))
        
        # 添加数据点
        for i, data in enumerate(self.hour_data):
            timestamp = data['time'].timestamp() * 1000  # 转换为毫秒
            fire_series.append(timestamp, data['fire'])
            animal_series.append(timestamp, data['animal'])
            landslide_series.append(timestamp, data['landslide'])
            pest_series.append(timestamp, data['pest'])
        
        # 添加系列到图表
        trend_chart.addSeries(fire_series)
        trend_chart.addSeries(animal_series)
        trend_chart.addSeries(landslide_series)
        trend_chart.addSeries(pest_series)
        
        # 创建X轴(时间轴)
        axis_x = QDateTimeAxis()
        axis_x.setFormat("HH:mm")
        axis_x.setTitleText("时间")
        axis_x.setTickCount(8)  # 显示8个刻度
        axis_x.setRange(
            self.hour_data[0]['time'],
            self.hour_data[-1]['time']
        )
        axis_x.setTitleBrush(QColor("white"))
        axis_x.setLabelsColor(QColor("white"))
        
        # 创建Y轴
        axis_y = QValueAxis()
        axis_y.setLabelFormat("%d")
        axis_y.setTitleText("告警数量")
        axis_y.setRange(0, 15)  # 增大Y轴范围，避免文字被裁剪
        axis_y.setTickCount(6)  # 增加刻度数量以更好显示
        axis_y.setTitleBrush(QColor("white"))
        axis_y.setLabelsColor(QColor("white"))
        
        # 添加坐标轴到图表
        trend_chart.addAxis(axis_x, Qt.AlignBottom)
        trend_chart.addAxis(axis_y, Qt.AlignLeft)
        
        # 将所有系列依附到坐标轴
        fire_series.attachAxis(axis_x)
        fire_series.attachAxis(axis_y)
        animal_series.attachAxis(axis_x)
        animal_series.attachAxis(axis_y)
        landslide_series.attachAxis(axis_x)
        landslide_series.attachAxis(axis_y)
        pest_series.attachAxis(axis_x)
        pest_series.attachAxis(axis_y)
        
        # 设置图例位置和样式
        trend_chart.legend().setVisible(True)
        trend_chart.legend().setAlignment(Qt.AlignBottom)
        trend_chart.legend().setLabelColor(QColor("white"))
        trend_chart.legend().setMarkerShape(QLegend.MarkerShapeCircle)  
        
        # 创建图表视图
        chart_view = QChartView(trend_chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        chart_view.setMinimumHeight(250)  # 增加最小高度
        chart_view.setBackgroundBrush(QColor("#0a1a2a"))
        
        layout.addWidget(chart_view)
        
        return tab
        
    def create_region_tab(self):
        """创建区域统计标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 添加区域告警统计图表
        chart_view = self.create_region_chart_view()
        layout.addWidget(chart_view)
        
        # 添加病虫害类型统计表格
        pest_table = self.create_pest_table()
        layout.addWidget(pest_table)
        
        return tab
        
    def create_pest_table(self):
        """创建病虫害类型统计表格"""
        # 创建表格
        table = QTableWidget()
        table.setObjectName("pest_table")  # 添加对象名称便于检索
        table.setColumnCount(2)
        table.setRowCount(len(self.pest_type_stats))
        
        # 设置表头
        table.setHorizontalHeaderLabels(["病虫害类型", "检测数量"])
        
        # 添加数据
        row = 0
        for pest_type, count in self.pest_type_stats.items():
            # 添加病虫害类型
            type_item = QTableWidgetItem(pest_type)
            type_item.setTextAlignment(Qt.AlignCenter)
            table.setItem(row, 0, type_item)
            
            # 添加数量
            count_item = QTableWidgetItem(str(count))
            count_item.setTextAlignment(Qt.AlignCenter)
            table.setItem(row, 1, count_item)
            
            row += 1
        
        # 设置表格样式
        table.setStyleSheet("""
            QTableWidget {
                background-color: rgba(0, 20, 40, 0.8);
                color: white;
                gridline-color: rgba(80, 160, 220, 0.5);
                border: 1px solid rgba(80, 160, 220, 0.5);
                border-radius: 4px;
            }
            QHeaderView::section {
                background-color: rgba(0, 60, 120, 0.9);
                color: white;
                padding: 4px;
                border: 1px solid rgba(80, 160, 220, 0.5);
            }
            QTableWidget::item {
                border-bottom: 1px solid rgba(80, 160, 220, 0.3);
            }
        """)
        
        # 调整表格大小
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)
        table.setFixedHeight(200)
        
        # 打印当前病虫害统计数据用于调试
        print("病虫害统计数据:")
        for pest_type, count in self.pest_type_stats.items():
            print(f"  {pest_type}: {count}")
        
        return table
        
    @pyqtSlot(int)
    def change_time_range(self, index):
        """切换时间范围"""
        # 获取当前选择的时间范围
        time_range = self.time_range_combo.currentText()
        
        # 更新趋势图
        if time_range == "最近24小时":
            self.update_trend_chart(self.hour_data, "HH:mm", 8)
        elif time_range == "最近7天":
            self.update_trend_chart(self.day_data[:7], "MM-dd", 7)
        elif time_range == "最近30天":
            self.update_trend_chart(self.day_data, "MM-dd", 10)
        elif time_range == "本月":
            # 筛选本月数据
            now = datetime.now()
            month_data = [d for d in self.day_data if d['time'].month == now.month]
            self.update_trend_chart(month_data, "MM-dd", 10)
        elif time_range == "本年":
            # 筛选本年数据 (这里使用全部数据模拟)
            self.update_trend_chart(self.day_data, "MM-dd", 10)
            
    def update_trend_chart(self, data, date_format, tick_count):
        """更新趋势图"""
        if not data:
            return
            
        # 获取当前标签页中的图表
        chart = self.trend_chart_view.chart()
        
        # 清除所有系列
        chart.removeAllSeries()
        
        # 创建新系列
        fire_series = QLineSeries()
        fire_series.setName("火灾告警")
        fire_series.setColor(QColor(255, 100, 100))
        
        animal_series = QLineSeries()
        animal_series.setName("动物告警")
        animal_series.setColor(QColor(100, 255, 100))
        
        landslide_series = QLineSeries()
        landslide_series.setName("滑坡告警")
        landslide_series.setColor(QColor(100, 100, 255))
        
        pest_series = QLineSeries()
        pest_series.setName("病虫害告警")
        pest_series.setColor(QColor(180, 100, 200))
        
        # 添加数据点
        for i, d in enumerate(data):
            timestamp = d['time'].timestamp() * 1000  # 转换为毫秒
            fire_series.append(timestamp, d['fire'])
            animal_series.append(timestamp, d['animal'])
            landslide_series.append(timestamp, d['landslide'])
            pest_series.append(timestamp, d['pest'])
        
        # 添加系列到图表
        chart.addSeries(fire_series)
        chart.addSeries(animal_series)
        chart.addSeries(landslide_series)
        chart.addSeries(pest_series)
        
        # 更新图表标题
        chart.setTitle(f"{self.time_range_combo.currentText()}告警趋势")
        
        # 创建/更新坐标轴
        chart.createDefaultAxes()
        
        # 更新X轴
        x_axis = chart.axes(Qt.Horizontal)[0]
        if isinstance(x_axis, QDateTimeAxis):
            x_axis.setFormat(date_format)
            x_axis.setTickCount(tick_count)
            x_axis.setRange(data[0]['time'], data[-1]['time'])
        
        # 更新Y轴
        y_axis = chart.axes(Qt.Vertical)[0]
        if isinstance(y_axis, QValueAxis):
            # 寻找最大值
            max_value = 0
            for d in data:
                for t in ['fire', 'animal', 'landslide', 'forest_degradation', 'pest']:
                    max_value = max(max_value, d[t])
                    
            # 确保Y轴至少有一些高度，即使没有数据
            if max_value < 1:
                max_value = 1
                
            # 设置Y轴范围，上浮20%以便更好地查看
            y_axis.setRange(0, max_value * 1.2)
            
            # 根据数据范围确定合适的刻度数量
            if max_value <= 5:
                y_axis.setTickCount(max_value + 1)  # 每个值一个刻度
            else:
                y_axis.setTickCount(6)  # 较大范围使用5-6个刻度
        
    @pyqtSlot()
    def refresh_statistics(self):
        """刷新统计数据"""
        # 不重置数据，只刷新UI
        # 更新当前标签页
        current_tab = self.tab_widget.currentIndex()
        if current_tab == 0:
            # 更新概览标签页
            overview_tab = self.create_overview_tab()
            self.tab_widget.removeTab(0)
            self.tab_widget.insertTab(0, overview_tab, "概览")
        elif current_tab == 1:
            # 更新趋势图标签页
            self.change_time_range(self.time_range_combo.currentIndex())
        elif current_tab == 2:
            # 更新区域统计标签页
            region_tab = self.create_region_tab()
            self.tab_widget.removeTab(2)
            self.tab_widget.insertTab(2, region_tab, "区域统计")
            
        # 切换回当前标签页
        self.tab_widget.setCurrentIndex(current_tab)
        
        print("已刷新统计面板显示")
    
    @pyqtSlot()
    def auto_update_statistics(self):
        """自动更新统计数据（由定时器调用）"""
        # 更新数据
        self.update_statistics()
        
        # 动态更新UI
        self.update_current_tab()
        
    def update_current_tab(self):
        """更新所有标签页的UI，确保数据及时刷新"""
        # 更新概览标签页上的告警统计
        overview_tab = self.tab_widget.widget(0)
        if overview_tab:
            stats_group = overview_tab.findChild(QGroupBox, "stats_group")
            if stats_group:
                # 更新标签
                for i, (key, color) in enumerate([
                    ('fire', 'red'), 
                    ('animal', 'green'), 
                    ('landslide', 'blue'), 
                    ('pest', 'purple')
                ]):
                    label_name = f"{key}_label"
                    label = stats_group.findChild(QLabel, label_name)
                    if label:
                        label.setText(f"{key.capitalize()}告警: {self.alert_stats[key]}")
            
            # 更新饼图
            chart_view = overview_tab.findChild(QChartView)
            if chart_view:
                # 创建新饼图
                new_chart_view = self.create_pie_chart()
                # 替换旧饼图
                layout = overview_tab.layout()
                layout.replaceWidget(chart_view, new_chart_view)
                chart_view.deleteLater()
                
        # 更新趋势图
        self.change_time_range(self.time_range_combo.currentIndex())
        
        # 保存当前区域图表视图的引用，便于后续更新
        if not hasattr(self, 'region_chart_view'):
            self.region_chart_view = self.create_region_chart_view()
            
        # 更新区域统计图
        region_tab = self.tab_widget.widget(2)
        if region_tab:
            chart_view = region_tab.findChild(QChartView)
            if chart_view:
                # 创建新区域图
                new_chart_view = self.create_region_chart_view()
                # 替换旧区域图
                layout = region_tab.layout()
                layout.replaceWidget(chart_view, new_chart_view)
                chart_view.deleteLater()
                
                # 更新病虫害类型表格
                table = region_tab.findChild(QTableWidget)
                if table:
                    for row, (pest_type, count) in enumerate(self.pest_type_stats.items()):
                        if row < table.rowCount() and count > 0:
                            count_item = QTableWidgetItem(str(count))
                            count_item.setTextAlignment(Qt.AlignCenter)
                            table.setItem(row, 1, count_item)
                
        # 触发刷新
        self.update()  # 强制刷新UI
        print("已刷新所有统计图表")
        
    def update_statistics(self):
        """更新统计数据（由外部定时器调用）"""
        # 获取当前时间
        now = datetime.now()
        
        # 对所有数据点进行处理，实现自然衰减的效果
        for data in self.hour_data:
            for key in ['fire', 'animal', 'landslide', 'forest_degradation', 'pest']:
                # 如果是当前小时的数据，保持不变
                if data['time'].hour == now.hour and data['time'].day == now.day:
                    continue
                
                # 对于旧数据，每次更新减少20%，但不低于0
                # 这样可以实现数值的自然衰减，使图表能体现趋势变化
                if data[key] > 0:
                    data[key] = max(0, data[key] - 0.2)
        
        # 对日数据也进行类似处理
        for data in self.day_data:
            # 如果不是当前日期的数据，进行衰减
            if data['time'].day != now.day or data['time'].month != now.month:
                for key in ['fire', 'animal', 'landslide', 'forest_degradation', 'pest']:
                    if data[key] > 0:
                        data[key] = max(0, data[key] - 0.1)  # 日数据衰减更慢一些
        
        # 更新UI显示
        self.update_current_tab()

    def create_pie_chart(self):
        """创建新的饼图供外部使用"""
        pie_chart = QChart()
        pie_chart.setTitle("告警类型分布")
        pie_chart.setAnimationOptions(QChart.SeriesAnimations)
        pie_chart.setBackgroundBrush(QColor("#0a1a2a"))
        pie_chart.setTitleBrush(QColor("white"))
        pie_chart.setTitleFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        
        # 创建饼图系列
        series = QPieSeries()
        
        # 检查是否有数据
        total_alerts = sum(self.alert_stats.values())
        if total_alerts > 0:
            series.append("火灾告警", self.alert_stats['fire'])
            series.append("动物告警", self.alert_stats['animal'])
            series.append("滑坡告警", self.alert_stats['landslide'])
            series.append("病虫害告警", self.alert_stats['pest'])
            
            # 设置切片颜色
            if len(series.slices()) >= 5:
                series.slices()[0].setBrush(QColor(255, 100, 100))  # 红色
                series.slices()[1].setBrush(QColor(100, 255, 100))  # 绿色
                series.slices()[2].setBrush(QColor(100, 100, 255))  # 蓝色
                series.slices()[3].setBrush(QColor(255, 200, 100))  # 橙色
                series.slices()[4].setBrush(QColor(180, 100, 200))  # 紫色
                
                # 设置标签颜色
                for slice in series.slices():
                    slice.setLabelColor(QColor("white"))
                    slice.setLabelFont(QFont("Microsoft YaHei", 9))
                
                # 突出显示第一个切片
                series.slices()[0].setExploded(True)
                series.slices()[0].setLabelVisible(True)
        else:
            # 如果没有数据，添加一个空的占位切片
            placeholder = series.append("无告警数据", 1)
            placeholder.setBrush(QColor(100, 100, 100))  # 灰色
            placeholder.setLabelColor(QColor("white"))
            placeholder.setLabelFont(QFont("Microsoft YaHei", 9))
            placeholder.setLabelVisible(True)
        
        pie_chart.addSeries(series)
        pie_chart.legend().setLabelColor(QColor("white"))
        
        # 创建图表视图
        chart_view = QChartView(pie_chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        chart_view.setBackgroundBrush(QColor("#0a1a2a"))
        
        return chart_view

    def create_trend_chart_view(self):
        """创建新的趋势图视图供外部使用"""
        trend_chart = QChart()
        trend_chart.setTitle("24小时告警趋势")
        trend_chart.setAnimationOptions(QChart.SeriesAnimations)
        trend_chart.setBackgroundBrush(QColor("#0a1a2a"))
        trend_chart.setTitleBrush(QColor("white"))
        trend_chart.setTitleFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        
        # 设置图表边距，增加底部和左侧空间显示坐标文字
        trend_chart.setMargins(QMargins(10, 10, 10, 20))
        
        # 创建折线系列 - 火灾
        fire_series = QLineSeries()
        fire_series.setName("火灾告警")
        fire_series.setColor(QColor(255, 100, 100))
        
        # 创建折线系列 - 动物
        animal_series = QLineSeries()
        animal_series.setName("动物告警")
        animal_series.setColor(QColor(100, 255, 100))
        
        # 创建折线系列 - 滑坡
        landslide_series = QLineSeries()
        landslide_series.setName("滑坡告警")
        landslide_series.setColor(QColor(100, 100, 255))
        
        # 创建折线系列 - 病虫害
        pest_series = QLineSeries()
        pest_series.setName("病虫害告警")
        pest_series.setColor(QColor(180, 100, 200))
        
        # 添加数据点
        for i, data in enumerate(self.hour_data):
            timestamp = data['time'].timestamp() * 1000  # 转换为毫秒
            fire_series.append(timestamp, data['fire'])
            animal_series.append(timestamp, data['animal'])
            landslide_series.append(timestamp, data['landslide'])
            pest_series.append(timestamp, data['pest'])
        
        # 添加系列到图表
        trend_chart.addSeries(fire_series)
        trend_chart.addSeries(animal_series)
        trend_chart.addSeries(landslide_series)
        trend_chart.addSeries(pest_series)
        
        # 创建X轴(时间轴)
        axis_x = QDateTimeAxis()
        axis_x.setFormat("HH:mm")
        axis_x.setTitleText("时间")
        axis_x.setTickCount(8)  # 显示8个刻度
        axis_x.setRange(
            self.hour_data[0]['time'],
            self.hour_data[-1]['time']
        )
        axis_x.setTitleBrush(QColor("white"))
        axis_x.setLabelsColor(QColor("white"))
        axis_x.setLabelsFont(QFont("Microsoft YaHei", 8))
        axis_x.setTitleFont(QFont("Microsoft YaHei", 9, QFont.Bold))
        
        # 创建Y轴
        axis_y = QValueAxis()
        axis_y.setLabelFormat("%d")
        axis_y.setTitleText("告警数量")
        axis_y.setRange(0, 15)  # 增大Y轴范围，避免文字被裁剪
        axis_y.setTickCount(6)  # 增加刻度数量以更好显示
        axis_y.setTitleBrush(QColor("white"))
        axis_y.setLabelsColor(QColor("white")) 
        axis_y.setLabelsFont(QFont("Microsoft YaHei", 8))
        axis_y.setTitleFont(QFont("Microsoft YaHei", 9, QFont.Bold))
        
        # 添加坐标轴到图表
        trend_chart.addAxis(axis_x, Qt.AlignBottom)
        trend_chart.addAxis(axis_y, Qt.AlignLeft)
        
        # 将所有系列依附到坐标轴
        fire_series.attachAxis(axis_x)
        fire_series.attachAxis(axis_y)
        animal_series.attachAxis(axis_x)
        animal_series.attachAxis(axis_y)
        landslide_series.attachAxis(axis_x)
        landslide_series.attachAxis(axis_y)
        pest_series.attachAxis(axis_x)
        pest_series.attachAxis(axis_y)
        
        # 设置图例位置和样式
        trend_chart.legend().setVisible(True)
        trend_chart.legend().setAlignment(Qt.AlignBottom)
        trend_chart.legend().setLabelColor(QColor("white"))
        trend_chart.legend().setMarkerShape(QLegend.MarkerShapeCircle)
        trend_chart.legend().setFont(QFont("Microsoft YaHei", 8))
        
        # 创建图表视图
        chart_view = QChartView(trend_chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        chart_view.setMinimumHeight(280)  # 增加最小高度
        chart_view.setBackgroundBrush(QColor("#0a1a2a"))
        
        return chart_view

    def create_region_chart_view(self):
        """创建区域统计图视图"""
        chart = QChart()
        chart.setTitle("区域统计")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.setBackgroundBrush(QColor("#0a1a2a"))
        chart.setTitleBrush(QColor("white"))
        chart.setTitleFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        
        # 设置图表边距，增加底部和左侧空间显示坐标文字
        chart.setMargins(QMargins(10, 10, 10, 20))
        
        # 创建数据集
        barset = QBarSet("告警数量")
        barset.setColor(QColor(100, 200, 255))  # 设置柱状图颜色
        
        # 获取区域名称和数据
        regions = list(self.region_stats.keys())
        values = list(self.region_stats.values())
        
        # 如果区域统计为空，使用默认区域
        if not regions:
            regions = ['东北区', '西北区', '中部区', '东南区', '西南区']
            values = [0, 0, 0, 0, 0]
            print("警告: 区域统计数据为空，使用默认空值")
        
        # 打印当前区域统计数据用于调试
        print("区域统计数据:")
        for region, value in zip(regions, values):
            print(f"  {region}: {value}")
        
        # 添加数据到集合
        for value in values:
            barset.append(value)
        
        # 创建条形系列
        series = QBarSeries()
        series.append(barset)
        series.setLabelsVisible(True)
        series.setLabelsPosition(QBarSeries.LabelsInsideEnd)  # 标签位置在柱内端
        
        # 添加系列到图表
        chart.addSeries(series)
        
        # 创建X轴(区域)
        axis_x = QBarCategoryAxis()
        axis_x.append(regions)
        axis_x.setTitleText("区域")
        axis_x.setTitleBrush(QColor("white"))
        axis_x.setLabelsColor(QColor("white"))
        axis_x.setLabelsFont(QFont("Microsoft YaHei", 8))
        axis_x.setTitleFont(QFont("Microsoft YaHei", 9, QFont.Bold))
        
        # 创建Y轴
        axis_y = QValueAxis()
        axis_y.setLabelFormat("%d")
        axis_y.setTitleText("告警数量")
        
        # 设置Y轴范围，确保即使是小数值也能看到变化
        max_value = max(values) if values and max(values) > 0 else 1
        axis_y.setRange(0, max_value * 1.2 + 1)  # 最大值上浮20%，并确保至少有高度
        
        axis_y.setTickCount(6)
        axis_y.setTitleBrush(QColor("white"))
        axis_y.setLabelsColor(QColor("white"))
        axis_y.setLabelsFont(QFont("Microsoft YaHei", 8))
        axis_y.setTitleFont(QFont("Microsoft YaHei", 9, QFont.Bold))
        
        # 添加坐标轴到图表
        chart.addAxis(axis_x, Qt.AlignBottom)
        chart.addAxis(axis_y, Qt.AlignLeft)
        
        # 将系列附加到坐标轴
        series.attachAxis(axis_x)
        series.attachAxis(axis_y)
        
        # 图例设置
        chart.legend().setVisible(False)  # 隐藏图例
        
        # 创建图表视图
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        chart_view.setMinimumHeight(280)  # 增加最小高度
        chart_view.setBackgroundBrush(QColor("#0a1a2a"))
        
        return chart_view

    def handle_new_alert(self, alert_type, region):
        """处理新的告警信息
        
        Args:
            alert_type (str): 告警类型 ('fire', 'animal', 'landslide', 'forest_degradation', 'pest')
            region (str): 告警区域
        """
        print(f"统计面板收到新告警: 类型={alert_type}, 区域={region}")
        
        # 更新告警统计总数
        if alert_type in self.alert_stats:
            self.alert_stats[alert_type] += 1
            print(f"更新告警统计: {alert_type} = {self.alert_stats[alert_type]}")
            
        # 更新区域统计
        mapped_region = self.region_mapping.get(region, '中部区')  # 如果没有映射则默认为中部区
        if mapped_region not in self.region_stats:
            self.region_stats[mapped_region] = 0
        self.region_stats[mapped_region] += 1
        print(f"更新区域统计: {mapped_region} = {self.region_stats[mapped_region]}")
        
        # 更新趋势数据
        now = datetime.now()
        
        # 更新小时数据
        for data in self.hour_data:
            if data['time'].hour == now.hour and data['time'].day == now.day:
                if alert_type in data:
                    data[alert_type] += 1
                    print(f"更新小时趋势: {alert_type} = {data[alert_type]}")
                break
        
        # 更新日数据
        for data in self.day_data:
            if data['time'].day == now.day and data['time'].month == now.month:
                if alert_type in data:
                    data[alert_type] += 1
                    print(f"更新日趋势: {alert_type} = {data[alert_type]}")
                break
        
        # 更新月数据
        for data in self.month_data:
            if data['time'].day == now.day and data['time'].month == now.month:
                if alert_type in data:
                    data[alert_type] += 1
                    print(f"更新月趋势: {alert_type} = {data[alert_type]}")
                break
        
        # 更新UI显示
        self.update_current_tab()
        
        # 强制刷新UI
        from PyQt5.QtWidgets import QApplication
        QApplication.processEvents()

    def handle_alert_processed(self, alert_type, region):
        """处理告警已被处理的信号
        
        Args:
            alert_type (str): 告警类型 ('fire', 'animal', 'landslide', 'forest_degradation', 'pest')
            region (str): 告警区域
        """
        print(f"统计面板收到告警处理通知: 类型={alert_type}, 区域={region}")
        
        # 减少告警统计总数，但确保不会小于0
        if alert_type in self.alert_stats and self.alert_stats[alert_type] > 0:
            self.alert_stats[alert_type] -= 1
            print(f"减少告警统计: {alert_type} = {self.alert_stats[alert_type]}")
            
        # 区域名称映射（将告警区域名称映射到区域统计中的键）
        region_mapping = {
            '北部山区': '东北区',
            '南部林区': '东南区',
            '东部山脊': '东北区',
            '西部谷地': '西北区',
            '西部林区': '西北区',
            '中央林场': '中部区'
        }
        
        # 减少区域统计总数
        mapped_region = region_mapping.get(region, region)
        
        if mapped_region in self.region_stats and self.region_stats[mapped_region] > 0:
            self.region_stats[mapped_region] -= 1
            print(f"减少区域统计: {mapped_region} = {self.region_stats[mapped_region]}")
            
        # 如果是病虫害类型，减少一种随机病虫害
        if alert_type == 'pest':
            import random
            pest_types = [k for k, v in self.pest_type_stats.items() if v > 0]
            if pest_types:
                selected_pest = random.choice(pest_types)
                self.pest_type_stats[selected_pest] -= 1
                print(f"减少病虫害类型: {selected_pest} = {self.pest_type_stats[selected_pest]}")
            
        # 更新当前小时的趋势数据 - 减少告警量
        now = datetime.now()
        for data in self.hour_data:
            if data['time'].hour == now.hour and data['time'].day == now.day:
                if alert_type in data and data[alert_type] > 0:
                    data[alert_type] -= 1
                    print(f"减少小时趋势: {alert_type} = {data[alert_type]}")
                break
                
        # 更新当前日期的趋势数据 - 减少告警量
        for data in self.day_data:
            if data['time'].day == now.day and data['time'].month == now.month:
                if alert_type in data and data[alert_type] > 0:
                    data[alert_type] -= 1
                    print(f"减少日趋势: {alert_type} = {data[alert_type]}")
                break
                
        # 基于当前选择的时间范围更新趋势图
        current_index = self.time_range_combo.currentIndex() if hasattr(self, 'time_range_combo') else 0
        self.change_time_range(current_index)
            
        # 更新UI - 确保立即刷新所有标签页
        self.update_current_tab()
        
        # 强制刷新UI
        from PyQt5.QtWidgets import QApplication
        QApplication.processEvents() 