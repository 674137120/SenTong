import os
import requests
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QComboBox, QGroupBox, QToolBar, QAction, QGridLayout)
from PyQt5.QtCore import Qt, QUrl, pyqtSlot, QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineProfile, QWebEngineSettings
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor

class RequestInterceptor(QWebEngineUrlRequestInterceptor):
    """网络请求拦截器，用于调试地图加载问题"""
    def interceptRequest(self, info):
        print(f"请求URL: {info.requestUrl().toString()}")
        print(f"请求方法: {info.requestMethod()}")
        print(f"请求头: {info.requestHeaders()}")

class CustomWebEnginePage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, line, source):
        level_str = {
            0: "INFO",
            1: "WARNING",
            2: "ERROR"
        }.get(level, "UNKNOWN")
        print(f"JS控制台 [{level_str}] {message} (第{line}行, 来源: {source})")

class MapView(QWidget):
    """地图视图组件，用于在地理信息系统上显示监测区域和告警位置"""
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        # 创建主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建地图容器
        map_container = QWidget()
        map_layout = QVBoxLayout(map_container)
        map_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建工具栏
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(16, 16))
        
        # 添加地图类型选择下拉框
        self.map_type_combo = QComboBox()
        self.map_type_combo.addItems(["卫星图", "地形图", "道路图", "混合图"])
        self.map_type_combo.setCurrentIndex(0)  # 设置默认选中卫星图
        self.map_type_combo.currentIndexChanged.connect(self.change_map_type)
        toolbar.addWidget(QLabel("地图类型: "))
        toolbar.addWidget(self.map_type_combo)
        
        toolbar.addSeparator()
        
        # 添加区域选择下拉框
        self.region_combo = QComboBox()
        for region in self.config.get('monitor_regions', []):
            self.region_combo.addItem(region['name'], region)
        self.region_combo.currentIndexChanged.connect(self.change_region)
        toolbar.addWidget(QLabel("监测区域: "))
        toolbar.addWidget(self.region_combo)
        
        toolbar.addSeparator()
        
        # 添加缩放按钮
        self.zoom_in_btn = QPushButton("放大")
        self.zoom_in_btn.setIcon(QIcon(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'zoom_in.png')))
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        toolbar.addWidget(self.zoom_in_btn)
        
        self.zoom_out_btn = QPushButton("缩小")
        self.zoom_out_btn.setIcon(QIcon(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'zoom_out.png')))
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        toolbar.addWidget(self.zoom_out_btn)
        
        toolbar.addSeparator()
        
        # 显示/隐藏告警点
        self.show_alerts_btn = QPushButton("显示告警")
        self.show_alerts_btn.setCheckable(True)
        self.show_alerts_btn.setChecked(True)
        self.show_alerts_btn.clicked.connect(self.toggle_alerts)
        toolbar.addWidget(self.show_alerts_btn)
        
        toolbar.addSeparator()
        
        # 添加定位按钮
        self.location_btn = QPushButton("定位")
        self.location_btn.setIcon(QIcon(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'location.png')))
        self.location_btn.clicked.connect(self.locate_current_position)
        toolbar.addWidget(self.location_btn)
        
        # 添加工具栏到地图布局
        map_layout.addWidget(toolbar)
        
        # 创建Web视图用于显示地图
        self.web_view = QWebEngineView()
        
        # 配置Edge浏览器引擎
        profile = QWebEngineProfile.defaultProfile()
        profile.setHttpUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59")
        
        # 添加请求拦截器
        interceptor = RequestInterceptor()
        profile.setUrlRequestInterceptor(interceptor)
        
        # 启用必要的Web功能
        settings = profile.settings()
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebGLEnabled, True)
        settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
        settings.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
        
        # 启用跨域访问
        profile.setHttpCacheType(QWebEngineProfile.DiskHttpCache)
        profile.setPersistentCookiesPolicy(QWebEngineProfile.AllowPersistentCookies)
        
        # 设置页面
        page = CustomWebEnginePage(self.web_view)
        self.web_view.setPage(page)
        map_layout.addWidget(self.web_view)
        
        # 将地图容器添加到主布局
        layout.addWidget(map_container)
        
        # 加载初始地图
        self.load_map()
        
    def load_map(self):
        """加载百度地图"""
        try:
            # 获取地图配置
            center = self.config.get('map_center', [39.915, 116.404])
            zoom = self.config.get('map_zoom', 15)
            
            # 使用临时文件加载地图
            import tempfile
            temp_path = os.path.join(tempfile.gettempdir(), "map_temp.html")
            
            # 构建HTML
            html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <meta name="viewport" content="initial-scale=1.0, user-scalable=no" />
    <title>森林监测地图</title>
    <script type="text/javascript" src="https://api.map.baidu.com/api?v=3.0&ak={self.config.get('baidu_map_key', '')}&type=webgl"></script>
    <style type="text/css">
        html, body, #map {{
            height: 100%;
            width: 100%;
            margin: 0;
            padding: 0;
        }}
        .loading {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            text-align: center;
            font-family: Arial, sans-serif;
        }}
        .offline-map {{
            width: 100%;
            height: 100%;
            background-color: #eee;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            font-family: Arial, sans-serif;
        }}
        .info-window {{
            padding: 5px;
            min-width: 150px;
        }}
        .info-window .title {{
            font-weight: bold;
            margin-bottom: 5px;
            color: #3a8ee6;
        }}
    </style>
</head>
<body>
    <div id="map">
        <div class="loading">加载百度地图中...</div>
    </div>
    
    <script type="text/javascript">
        // 全局变量
        var map;
        var alertMarkers = [];
        var isMapLoaded = false;
        
        // 初始化函数
        function initMap() {{
            try {{
                console.log("开始初始化地图...");
                
                // 检查BMap对象是否存在
                if (typeof BMapGL === "undefined") {{
                    throw new Error("BMapGL未定义，百度地图API未正确加载");
                }}
                
                console.log("创建地图实例...");
                // 创建地图实例
                map = new BMapGL.Map("map");
                
                console.log("设置地图中心点...");
                // 创建点坐标（注意经纬度顺序：经度在前，纬度在后）
                var point = new BMapGL.Point({center[1]}, {center[0]});
                
                console.log("初始化地图视图...");
                // 初始化地图
                map.centerAndZoom(point, {zoom});
                
                // 设置默认地图类型为卫星图
                map.setMapType(BMAP_SATELLITE_MAP);
                
                // 设置默认显示选项，隐藏POI图标
                map.setDisplayOptions({{
                    poi: false,  // 隐藏POI图标
                    poiText: false,  // 隐藏POI文字
                    building: false  // 隐藏3D建筑物
                }});
                
                // 开启鼠标滚轮缩放
                map.enableScrollWheelZoom(true);
                
                console.log("添加地图控件...");
                // 添加地图控件
                map.addControl(new BMapGL.NavigationControl());    // 导航控件
                map.addControl(new BMapGL.ScaleControl());         // 比例尺控件
                map.addControl(new BMapGL.ZoomControl());          // 缩放控件
                map.addControl(new BMapGL.LocationControl());      // 定位控件
                
                // 地图初始化成功标记
                isMapLoaded = true;
                console.log("地图初始化完成");

                // 自动定位到当前位置
                setTimeout(function() {{
                    // 定义错误状态处理函数
                    function handleLocationError(status) {{
                        var errorMsg = "";
                        switch(status) {{
                            case 6:
                                errorMsg = "定位权限被拒绝，请在浏览器设置中允许获取位置信息";
                                break;
                            case 2:
                            case 8:
                                errorMsg = "定位不可用或超时，尝试使用IP定位";
                                break;
                            default:
                                errorMsg = "定位失败(错误码:" + status + ")，尝试使用IP定位";
                        }}
                        console.error(errorMsg);
                        return errorMsg;
                    }}

                    // 显示定位结果的函数
                    function showLocationResult(point, accuracy, address, locationType, errorMsg) {{
                        var marker = new BMapGL.Marker(point);
                        map.addOverlay(marker);
                        map.centerAndZoom(point, locationType === 'ip' ? 12 : 18);

                        // 如果是精确定位，显示精度圈
                        if (accuracy && locationType !== 'ip') {{
                            var circle = new BMapGL.Circle(point, accuracy, {{
                                strokeColor: "#1E90FF",
                                strokeWeight: 1,
                                strokeOpacity: 0.5,
                                fillColor: "#1E90FF",
                                fillOpacity: 0.1
                            }});
                            map.addOverlay(circle);
                        }}

                        var locationTypeText = {{
                            'sdk': '手机GPS',
                            'h5': '浏览器定位',
                            'ip': 'IP定位'
                        }}[locationType] || '未知方式';

                        var infoWindow = new BMapGL.InfoWindow(
                            '<div class="info-window">' +
                            '<div class="title">当前位置</div>' +
                            '<div>定位方式: ' + locationTypeText + '</div>' +
                            '<div>经度: ' + point.lng.toFixed(6) + '</div>' +
                            '<div>纬度: ' + point.lat.toFixed(6) + '</div>' +
                            '<div>地址: ' + address + '</div>' +
                            (accuracy && locationType !== 'ip' ? '<div>定位精度: ' + accuracy.toFixed(1) + '米</div>' : '') +
                            (errorMsg ? '<div style="color: #ff9900;">' + errorMsg + '</div>' : '') +
                            '</div>'
                        );
                        marker.openInfoWindow(infoWindow);
                    }}

                    // 先尝试SDK定位
                    var geolocation = new BMapGL.Geolocation();
                    geolocation.enableSDKLocation();
                    geolocation.getCurrentPosition(function(r) {{
                        if(this.getStatus() == BMAP_STATUS_SUCCESS) {{
                            // SDK定位成功
                            var geoc = new BMapGL.Geocoder();
                            geoc.getLocation(r.point, function(rs) {{
                                var addComp = rs.addressComponents;
                                var address = addComp.province + addComp.city + 
                                            addComp.district + addComp.street + 
                                            addComp.streetNumber;
                                showLocationResult(r.point, r.accuracy, address, 'sdk');
                            }});
                        }} else {{
                            // SDK定位失败，尝试浏览器H5定位
                            var h5geolocation = new BMapGL.Geolocation();
                            h5geolocation.getCurrentPosition(function(r) {{
                                if(this.getStatus() == BMAP_STATUS_SUCCESS) {{
                                    // H5定位成功
                                    var geoc = new BMapGL.Geocoder();
                                    geoc.getLocation(r.point, function(rs) {{
                                        var addComp = rs.addressComponents;
                                        var address = addComp.province + addComp.city + 
                                                    addComp.district + addComp.street + 
                                                    addComp.streetNumber;
                                        showLocationResult(r.point, r.accuracy, address, 'h5');
                                    }});
                                }} else {{
                                    // H5定位也失败，使用IP定位
                                    var errorMsg = handleLocationError(this.getStatus());
                                    var myCity = new BMapGL.LocalCity();
                                    myCity.get(function(result) {{
                                        var geoc = new BMapGL.Geocoder();
                                        geoc.getLocation(result.center, function(rs) {{
                                            var addComp = rs.addressComponents;
                                            var address = addComp.province + addComp.city + 
                                                        addComp.district + addComp.street + 
                                                        addComp.streetNumber;
                                            showLocationResult(result.center, null, address, 'ip', 
                                                '注意：由于无法获取精确位置，已切换到IP定位（精度较低）');
                                        }});
                                    }});
                                }}
                            }}, {{
                                enableHighAccuracy: true,
                                timeout: 5000,
                                maximumAge: 0
                            }});
                        }}
                    }}, {{
                        enableHighAccuracy: true,
                        timeout: 5000,
                        maximumAge: 0,
                        SDKLocation: true,
                        coordType: 'bd09ll',
                        poiDistance: true,
                        poiNumber: 1
                    }});
                }}, 1000);
                
                // 定义对外接口
                window.mapFunctions = {{
                    setMapType: function(type) {{
                        if (!isMapLoaded) return false;
                        try {{
                            switch(type) {{
                                case 0: // 卫星图
                                    map.setMapType(BMAP_SATELLITE_MAP);
                                    map.setDisplayOptions({{
                                        poi: false,
                                        poiText: false,
                                        building: false
                                    }});
                                    map.setTilt(0);
                                    break;
                                case 1: // 地形图
                                    map.setMapType(BMAP_NORMAL_MAP);
                                    map.setDisplayOptions({{
                                        poi: false,
                                        poiText: false,
                                        building: false
                                    }});
                                    break;
                                case 2: // 道路图
                                    map.setMapType(BMAP_NORMAL_MAP);
                                    map.setDisplayOptions({{
                                        poi: false,
                                        poiText: false,
                                        building: false
                                    }});
                                    break;
                                case 3: // 混合图
                                    map.setMapType(BMAP_SATELLITE_MAP);
                                    map.setDisplayOptions({{
                                        poi: false,
                                        poiText: false,
                                        building: true
                                    }});
                                    break;
                            }}
                            return true;
                        }} catch(e) {{
                            console.error("切换地图类型出错:", e);
                            return false;
                        }}
                    }},
                    
                    zoomIn: function() {{
                        if (!isMapLoaded) return false;
                        try {{
                            map.zoomIn();
                            return true;
                        }} catch(e) {{
                            console.error("地图放大出错:", e);
                            return false;
                        }}
                    }},
                    
                    zoomOut: function() {{
                        if (!isMapLoaded) return false;
                        try {{
                            map.zoomOut();
                            return true;
                        }} catch(e) {{
                            console.error("地图缩小出错:", e);
                            return false;
                        }}
                    }},
                    
                    panTo: function(lat, lng) {{
                        if (!isMapLoaded) return false;
                        try {{
                            var point = new BMapGL.Point(lng, lat);
                            map.panTo(point);
                            return true;
                        }} catch(e) {{
                            console.error("地图平移出错:", e);
                            return false;
                        }}
                    }},
                    
                    toggleAlerts: function(show) {{
                        if (!isMapLoaded) return false;
                        try {{
                            if (alertMarkers.length > 0) {{
                                alertMarkers.forEach(function(marker) {{
                                    if (show) marker.show();
                                    else marker.hide();
                                }});
                            }}
                            return true;
                        }} catch(e) {{
                            console.error("切换告警显示出错:", e);
                            return false;
                        }}
                    }},
                    
                    locateCurrentPosition: function() {{
                        if (!isMapLoaded) {{
                            console.error('地图未加载完成');
                            return false;
                        }}
                        
                        // 创建定位控件
                        var locationControl = new BMapGL.LocationControl();
                        locationControl.addEventListener("locationSuccess", function(e){{
                            var address = '';
                            address += e.addressComponent.province;
                            address += e.addressComponent.city;
                            address += e.addressComponent.district;
                            address += e.addressComponent.street;
                            address += e.addressComponent.streetNumber;
                            
                            // 在marker上显示信息窗口
                            var infoWindow = new BMapGL.InfoWindow(
                                '<div class="info-window">' +
                                '<div class="title">当前位置</div>' +
                                '<div>经度: ' + e.point.lng + '</div>' +
                                '<div>纬度: ' + e.point.lat + '</div>' +
                                '<div>地址: ' + address + '</div>' +
                                '</div>'
                            );
                            var marker = new BMapGL.Marker(e.point);
                            map.addOverlay(marker);
                            marker.openInfoWindow(infoWindow);
                            
                            console.log('定位成功');
                        }});
                        locationControl.addEventListener("locationError", function(e){{
                            console.error('定位失败：' + e.message);
                        }});
                        locationControl.location();
                        return true;
                    }}
                }};
                
            }} catch (e) {{
                console.error("地图初始化失败:", e);
                document.getElementById("map").innerHTML = 
                    '<div class="offline-map"><h2>百度地图初始化失败</h2><p>错误信息: ' + e.message + '</p></div>';
            }}
        }}
        
        // 添加示例告警点
        function addExampleAlerts() {{
            // 清空告警点数组
            alertMarkers = [];
            // 暂时不添加示例告警点
        }}

        // 页面加载完成后初始化地图
        window.onload = initMap;
    </script>
</body>
</html>"""
            
            # 将HTML保存到临时文件
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(html)
            
            # 从本地文件加载
            self.web_view.load(QUrl.fromLocalFile(temp_path))
            print("正在从本地文件加载百度地图...")
            
        except Exception as e:
            print(f"地图加载失败: {e}")
            # 显示错误信息
            error_html = f"""
            <html>
            <body style="background-color: #f0f0f0; color: #333; font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                <h2>地图加载失败</h2>
                <p>错误信息: {str(e)}</p>
                <p>请检查以下内容:</p>
                <ol style="text-align: left; max-width: 500px; margin: 0 auto;">
                    <li>确认网络连接正常</li>
                    <li>确认百度地图API密钥有效</li>
                    <li>检查PyQt WebEngine设置</li>
                    <li>查看控制台输出的详细错误信息</li>
                </ol>
            </body>
            </html>
            """
            self.web_view.setHtml(error_html)
      
    @pyqtSlot(int)
    def change_map_type(self, index):
        """改变地图类型"""
        # 通过JS调用地图函数
        script = f"""
            try {{
                console.log('调用地图类型切换，类型索引:', {index});
                if (window.mapFunctions && typeof window.mapFunctions.setMapType === 'function') {{
                    window.mapFunctions.setMapType({index});
                    return true;
                }} else {{
                    console.error('地图类型切换函数不可用');
                    return false;
                }}
            }} catch(e) {{
                console.error('执行地图类型切换时出错:', e);
                return false;
            }}
        """
        self.web_view.page().runJavaScript(script)
        
    @pyqtSlot(int)
    def change_region(self, index):
        """改变监测区域"""
        if index >= 0 and index < len(self.config.get('monitor_regions', [])):
            region = self.config['monitor_regions'][index]
            # 通过JS调用地图函数
            script = """
                try {
                    if (window.mapFunctions && typeof window.mapFunctions.panTo === 'function') {
                        window.mapFunctions.panTo(0, 0);
                        return true;
                    } else {
                        console.error('地图平移函数不可用');
                        return false;
                    }
                } catch(e) {
                    console.error('平移到区域时出错:', e);
                    return false;
                }
            """
            self.web_view.page().runJavaScript(script)
        
    @pyqtSlot()
    def zoom_in(self):
        """地图放大"""
        script = """
            try {
                if (window.mapFunctions && typeof window.mapFunctions.zoomIn === 'function') {
                    window.mapFunctions.zoomIn();
                    return true;
                } else {
                    console.error('地图放大函数不可用');
                    return false;
                }
            } catch(e) {
                console.error('地图放大时出错:', e);
                return false;
            }
        """
        self.web_view.page().runJavaScript(script)
        
    @pyqtSlot()
    def zoom_out(self):
        """地图缩小"""
        script = """
            try {
                if (window.mapFunctions && typeof window.mapFunctions.zoomOut === 'function') {
                    window.mapFunctions.zoomOut();
                    return true;
                } else {
                    console.error('地图缩小函数不可用');
                    return false;
                }
            } catch(e) {
                console.error('地图缩小时出错:', e);
                return false;
            }
        """
        self.web_view.page().runJavaScript(script)
        
    @pyqtSlot(bool)
    def toggle_alerts(self, checked):
        """切换告警点显示状态"""
        script = f"""
            try {{
                if (window.mapFunctions && typeof window.mapFunctions.toggleAlerts === 'function') {{
                    window.mapFunctions.toggleAlerts({str(checked).lower()});
                    return true;
                }} else {{
                    console.error('告警点切换函数不可用');
                    return false;
                }}
            }} catch(e) {{
                console.error('切换告警点时出错:', e);
                return false;
            }}
        """
        self.web_view.page().runJavaScript(script)
        
    def locate_current_position(self):
        """定位当前位置"""
        script = """
            try {
                if (!isMapLoaded) {
                    console.error('地图未加载完成');
                    return false;
                }
                
                // 创建定位控件
                var locationControl = new BMapGL.LocationControl();
                locationControl.addEventListener("locationSuccess", function(e){{
                    var address = '';
                    address += e.addressComponent.province;
                    address += e.addressComponent.city;
                    address += e.addressComponent.district;
                    address += e.addressComponent.street;
                    address += e.addressComponent.streetNumber;
                    
                    // 在marker上显示信息窗口
                    var infoWindow = new BMapGL.InfoWindow(
                        '<div class="info-window">' +
                        '<div class="title">当前位置</div>' +
                        '<div>经度: ' + e.point.lng + '</div>' +
                        '<div>纬度: ' + e.point.lat + '</div>' +
                        '<div>地址: ' + address + '</div>' +
                        '</div>'
                    );
                    var marker = new BMapGL.Marker(e.point);
                    map.addOverlay(marker);
                    marker.openInfoWindow(infoWindow);
                    
                    console.log('定位成功');
                }});
                locationControl.addEventListener("locationError", function(e){{
                    console.error('定位失败：' + e.message);
                }});
                locationControl.location();
                return true;
            } catch(e) {
                console.error('执行定位时出错:', e);
                return false;
            }
        """
        self.web_view.page().runJavaScript(script)
        
    def update_view(self):
        """更新地图视图"""
        # 实际项目中可以在这里添加刷新告警点等逻辑
        pass

    def get_accurate_ip_location(self):
        """获取更精确的IP定位信息"""
        try:
            # 使用腾讯位置服务
            response = requests.get(
                'https://apis.map.qq.com/ws/location/v1/ip',
                params={
                    'key': self.config.get('qq_map_key', ''),  # 需要在配置中添加腾讯地图密钥
                    'output': 'json'
                },
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                if data['status'] == 0:
                    location = data['result']['location']
                    return {
                        'lng': location['lng'],
                        'lat': location['lat'],
                        'accuracy': data['result'].get('accuracy', 0)
                    }
        except Exception as e:
            print(f"腾讯地图IP定位失败: {e}")
        return None