import sys
import requests
import cv2 as cv
import numpy as np
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout,
                             QHBoxLayout, QLineEdit, QPushButton,QDesktopWidget)
from PyQt5.QtCore import Qt, QThread, QObject, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap

class SkyChecker(QObject):
    frame_signal = pyqtSignal(np.ndarray)
    data_signal = pyqtSignal(float,str)

    def __init__(self, camera_index = 0):
        super().__init__()
        self.camera_index = camera_index
        self.is_running = False

    def start_camera(self):
        self.is_running = True
        cap = cv.VideoCapture(self.camera_index)

        while self.is_running:
            ret, frame = cap.read()
            if not ret:
                continue

            frame = cv.resize(frame, (400,300))

            hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)
            lower_cloud = np.array([0,0,150])
            upper_cloud = np.array([180,50,255])
            cloud_mask = cv.inRange(hsv, lower_cloud, upper_cloud)

            total_pixel = frame.shape[1] * frame.shape[0]
            cloud_pixel = np.count_nonzero(cloud_mask)
            cloud_calc = round((cloud_pixel/total_pixel) * 100, 1)

            if cloud_calc > 65:
                status = "Heavy Clouds / Impending Rain 🌧️"
            elif cloud_calc > 30:
                status = "Partly Cloudy ⛅"
            else:
                status = "Clear Sky ☀️"

            self.frame_signal.emit(frame)
            self.data_signal.emit(cloud_calc, status)

            QThread.msleep(60)

        cap.release()

    def stop_camera(self):
        self.is_running = False


class WeatherApp(QWidget):
    def __init__(self):
        super().__init__()
        self.city_label = QLabel("Enter city name: ",self)
        self.input_city = QLineEdit(self)
        self.get_weather_button = QPushButton("Click Here To Get Weather",self)
        self.temp_label = QLabel(self)
        self.emoji = QLabel(self)
        self.description_label = QLabel(self)

        self.camera_title = QLabel("Open CV Weather Detection App by Ak", self)
        self.camera_feed_label = QLabel("Camera Feed Off (Click Start Live)", self)
        self.cv_stats_label = QLabel("Local Sky Coverage: N/A | Status: Idle", self)
        self.toggle_cam_button = QPushButton("Start Live Sky Scan 📷", self)

        self.camera_active = False
        self.setup_vision()
        self.iniui()

    def iniui(self, bg_image="default_background.jpg"):
        self.setWindowTitle("Weather app by Ak")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.resize(1000,700)

        screen_geometry =  QDesktopWidget().availableGeometry().center()
        frame_geometry = self.frameGeometry()
        frame_geometry.moveCenter(screen_geometry)
        self.move(frame_geometry.topLeft())


        vbox_left = QVBoxLayout()
        vbox_left.addWidget(self.city_label)
        vbox_left.addWidget(self.input_city)
        vbox_left.addWidget(self.get_weather_button)
        vbox_left.addWidget(self.temp_label)
        vbox_left.addWidget(self.emoji)
        vbox_left.addWidget(self.description_label)

        vbox_right = QVBoxLayout()
        vbox_right.addWidget(self.camera_title)
        vbox_right.addWidget(self.camera_feed_label)
        vbox_right.addWidget(self.cv_stats_label)
        vbox_right.addWidget(self.toggle_cam_button)

        main_hbox = QHBoxLayout()
        main_hbox.addLayout(vbox_left, stretch=1)
        main_hbox.addLayout(vbox_right, stretch=1)
        self.setLayout(main_hbox)

        # Here i am Aligning them
        self.city_label.setAlignment(Qt.AlignCenter)
        self.input_city.setAlignment(Qt.AlignCenter)
        self.temp_label.setAlignment(Qt.AlignCenter)
        self.emoji.setAlignment(Qt.AlignCenter)
        self.description_label.setAlignment(Qt.AlignCenter)

        self.camera_title.setAlignment(Qt.AlignCenter)
        self.camera_feed_label.setAlignment(Qt.AlignCenter)
        self.cv_stats_label.setAlignment(Qt.AlignCenter)

        # Giving object names for css styling
        self.city_label.setObjectName("cl")
        self.input_city.setObjectName("ic")
        self.get_weather_button.setObjectName("wb")
        self.temp_label.setObjectName("tl")
        self.emoji.setObjectName("em")
        self.description_label.setObjectName("dl")

        self.camera_title.setObjectName("ct")
        self.camera_feed_label.setObjectName("cfl")
        self.cv_stats_label.setObjectName("cvs")
        self.toggle_cam_button.setObjectName("tcb")

        self.setStyleSheet(f"""
            WeatherApp{{
                border-image: url("{bg_image}") 0 0 0 0 stretch stretch;
                background-position: center;
                background-repeat: no-repeat;
            }}
            
            QLabel, QPushButton{{
                font-family: calibri;
                background: transparent;
            }}
            QLabel#cl{{
                font-size: 40px;
                font-style: Italic;
            }}
            QLineEdit#ic{{
                font-size: 40px;
            }}
            QPushButton#wb{{
                font-size: 40px;
                font-weight: Bold;
            }}
            QLabel#tl{{
                font-size: 75px;
                color: black;
                font-weight Bold;
            }}
            QLabel#em{{
                font-size: 120px;
                font-family: Segoe UI emoji;
            }}
            QLabel#dl{{
                font-size: 80px;
            }}
            QLabel#ct{{
                font-size: 35px;
                font-weight: bold;
                color: #090136;
            }}
            QLabel#cfl{{
                font-size: 20px;
                color: #021d30;
                background-color: #a0cbeb;
                border: 2px dashed #89b4fa;
                border-radius: 10px;
                min-height: 300px;
            }}
            QLabel#cvs{{
                font-size: 40px;
                color: black;
                font-weight: bold;
            }}
            QPushButton#tcb{{
                font-size: 45px;
                color: #bf0d10;
                font-weight: bold; 
            }}
        """)

        self.get_weather_button.clicked.connect(self.get_Weather)
        self.toggle_cam_button.clicked.connect(self.toggle_camera)

    def setup_vision(self):
        self.vision_thread = None
        self.vision_worker = None

    def toggle_camera(self):
        if not self.camera_active:
            self.vision_thread = QThread()
            self.vision_worker = SkyChecker(camera_index=0)
            self.vision_worker.moveToThread(self.vision_thread)

            self.vision_thread.started.connect(self.vision_worker.start_camera)
            self.vision_worker.frame_signal.connect(self.update_camera_feed)
            self.vision_worker.data_signal.connect(self.update_cv_stats)

            self.camera_active = True
            self.toggle_cam_button.setText("Stop Sky Scan 🛑")
            self.vision_thread.start()
        else:
            self.camera_active = False
            self.toggle_cam_button.setText("Start Live Sky Scan 📷")

            if self.vision_worker:
                self.vision_worker.stop_camera()

            if self.vision_thread:
                self.vision_thread.quit()
                self.vision_thread.wait()
                self.vision_thread = None
                self.vision_worker = None

            self.camera_feed_label.clear()
            self.camera_feed_label.setText("Camera Feed Off (Click Start Live)")
    def update_camera_feed(self, frame):
        rgb_frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        qt_format = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888).copy()
        pixmap = QPixmap.fromImage(qt_format)
        self.camera_feed_label.setPixmap(pixmap.scaled(self.camera_feed_label.width(),
                                                       self.camera_feed_label.height(),
                                                       Qt.KeepAspectRatio))

    def update_cv_stats(self, cloud_pct, status):
        self.cv_stats_label.setText(f"Cloud Cover: {cloud_pct}% | Sky State: {status}")

    def get_Weather(self):
        api_key = "615a2a1150da842f48695ace9d162d25"
        city = self.input_city.text()
        url  = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}"

        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            if data["cod"] == 200:
                self.display_weather(data)
        except requests.exceptions.HTTPError as  http_error:
            match response.status_code:
                case 400:
                    self.display_error("Bad request:\nPlease Check your input:")
                case 401:
                    self.display_error("Unauthorized:\nInvalid API Key:")
                case 403:
                    self.display_error("Forbidden:\nAccess is denied:")
                case 404:
                    self.display_error("Not Found:\nCity Not Found:")
                case 500:
                    self.display_error("Internal Server Error:\nPlease try again later:")
                case 502:
                    self.display_error("Bad gateway:\nInvalid response from the server:")
                case 503:
                    self.display_error("Service Unavailable:\nServer is down:")
                case 504:
                    self.display_error("Gateway Timeout:\nNo Response:")
                case _:
                    self.display_error(f"HTTP Error occurred:\n{http_error}")

        except requests.exceptions.ConnectionError:
            self.display_error("Connection Error:\nNo Internet Check your Internet Connection")

        except requests.exceptions.Timeout:
            self.display_error("Request Timeout:")

        except requests.exceptions.TooManyRedirects:
            self.display_error("Too Many Redirect\nCheck Your url:")

        except requests.exceptions.RequestException as req_error:
            self.display_error(f"Request Error:\n{req_error}")


    def display_error(self, message):
        self.temp_label.setText(message)
        self.emoji.clear()
        self.description_label.clear()

    def display_weather(self, data):
        temperature_k = data["main"]["temp"]
        temperature_c = temperature_k - 273.15
        temperature_f = (temperature_k * 9/5) - 459.67
        weather_description = data["weather"][0]["description"]
        weather_id = data["weather"][0]["id"]

        self.temp_label.setText(f"{temperature_c:.0f}℃")
        self.description_label.setText(weather_description)
        self.emoji.setText(get_weather_emoji(weather_id))

        bg_image = get_weather_bg(weather_id)
        self.setStyleSheet(self.styleSheet() + f"""
                    WeatherApp{{
                        border-image: url("{bg_image}") 0 0 0 0 stretch stretch;
                    }}
                """)

    def closeEvent(self, event):
        if self.camera_active:
            self.vision_worker.stop_camera()
            self.vision_thread.quit()
            self.vision_thread.wait()
        event.accept()


def get_weather_emoji(weather_id):

    if 200 <= weather_id <= 232:
        return "⛈️"
    elif 300 <= weather_id <= 321:
        return "🌦️"
    elif 500 <= weather_id <= 531:
        return "🌧️"
    elif 600 <= weather_id <= 622:
        return "🌨️"
    elif 701 <= weather_id <= 741:
        return  "🌫️"
    elif weather_id == 762:
        return "🌋"
    elif weather_id == 771:
        return "💨"
    elif weather_id == 781:
        return "🌪️"
    elif weather_id == 800:
        return "☀️"
    elif 801 <= weather_id <= 804:
        return "☁️"
    else:
        return ""

def get_weather_bg(weather_id):
    if 200 <= weather_id <= 232:
        return "thunderstorm.jpg"
    elif 300 <= weather_id <= 321:
        return "drizzle.jpg"
    elif 500 <= weather_id <= 531:
        return "rain.jpg"
    elif 600 <= weather_id <= 622:
        return "snow.jpg"
    elif 701 <= weather_id <= 781:
        return "tornado.jpg"
    elif weather_id == 800:
        return "sunny.jpg"
    elif 801 <= weather_id <= 804:
        return "cloudy.jpg"
    else:
        return "default_background.jpg"

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ww = WeatherApp()
    ww.show()
    sys.exit(app.exec_())
