import os
import shutil
import time
import subprocess
import sys
import threading
import traceback
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QLineEdit, QPushButton, 
                            QFileDialog, QTextEdit, QVBoxLayout, QHBoxLayout, QWidget, 
                            QGroupBox, QMessageBox, QSpacerItem, QSizePolicy)
from PyQt5.QtGui import QColor, QFont, QTextCursor
from PyQt5.QtCore import Qt, QObject, pyqtSignal

# ================================
# 核心配置与全局变量（简化线程管理）
# ================================
MODS_FOLDER = r"D:\MCLDownload\Game\.minecraft\mods"
MODS_BACKUP_FOLDER = r"D:\MCLDownload\Game\.minecraft\mods_backup"
TARGET_JAR_PATH = r"D:\MCLDownload\Game\.minecraft\mods\4681704866889354274@3@0.jar"
CONFIG_FOLDER = r"D:\MCLDownload\Game\.minecraft\config"
CONFIG_BACKUP_FOLDER = r"D:\MCLDownload\Game\.minecraft\config_backup"
SHADERPACKS_FOLDER = r"D:\MCLDownload\Game\.minecraft\shaderpacks"
JAVA_PROCESS_NAME = "java.exe"
is_running = False  # 仅用一个标记控制所有功能启停
observer_config = None
observer_mods = None
monitor_thread = None

# ================================
# 日志信号（稳定的跨线程通信）
# ================================
class LogEmitter(QObject):
    log_signal = pyqtSignal(str, str)  # 日志内容 + 颜色（red/green/yellow/gray）

log_emitter = LogEmitter()

# ================================
# 核心功能函数（简化线程逻辑，避免冲突）
# ================================
def 复制所有_mods_from_backup():
    if not os.path.exists(MODS_BACKUP_FOLDER):
        log_emitter.log_signal.emit(f"模组备份文件夹未找到: {MODS_BACKUP_FOLDER}", "red")
        return False
    if not os.path.exists(MODS_FOLDER):
        try:
            os.makedirs(MODS_FOLDER)
            log_emitter.log_signal.emit(f"已创建模组文件夹: {MODS_FOLDER}", "green")
        except Exception as e:
            log_emitter.log_signal.emit(f"创建模组文件夹失败: {e}", "red")
            return False

    log_emitter.log_signal.emit("正在复制模组从备份到模组文件夹...", "green")
    复制数量 = 0
    跳过数量 = 0
    for 文件名 in os.listdir(MODS_BACKUP_FOLDER):
        if 文件名.endswith('.jar') and is_running:  # 仅运行中执行
            源路径 = os.path.join(MODS_BACKUP_FOLDER, 文件名)
            目标路径 = os.path.join(MODS_FOLDER, 文件名)
            if os.path.exists(源路径):
                if not os.path.exists(目标路径):
                    try:
                        shutil.copy2(源路径, 目标路径)
                        log_emitter.log_signal.emit(f"已复制: {文件名}", "green")
                        复制数量 += 1
                    except Exception as e:
                        log_emitter.log_signal.emit(f"复制失败 {文件名}: {e}", "red")
                else:
                    log_emitter.log_signal.emit(f"已存在: {文件名}", "gray")
                    跳过数量 += 1
    log_emitter.log_signal.emit(f"复制完成: {复制数量}个已复制, {跳过数量}个已跳过", "green")
    return True

def 备份配置文件():
    if not is_running:
        return False
    if not os.path.exists(CONFIG_BACKUP_FOLDER):
        try:
            os.makedirs(CONFIG_BACKUP_FOLDER)
            log_emitter.log_signal.emit(f"已创建配置备份文件夹: {CONFIG_BACKUP_FOLDER}", "yellow")
        except Exception as e:
            log_emitter.log_signal.emit(f"创建备份文件夹失败: {e}", "red")
            return False
    if not os.path.exists(CONFIG_FOLDER):
        log_emitter.log_signal.emit(f"配置文件夹未找到: {CONFIG_FOLDER}", "gray")
        return True

    log_emitter.log_signal.emit("正在备份配置文件...", "green")
    备份数量 = 0
    错误数量 = 0
    for 文件名 in os.listdir(CONFIG_FOLDER):
        if is_running:  # 仅运行中执行
            源路径 = os.path.join(CONFIG_FOLDER, 文件名)
            备份路径 = os.path.join(CONFIG_BACKUP_FOLDER, 文件名)
            if os.path.isfile(源路径):
                try:
                    shutil.copy2(源路径, 备份路径)
                    log_emitter.log_signal.emit(f"已备份: {文件名}", "yellow")
                    备份数量 += 1
                except Exception as e:
                    log_emitter.log_signal.emit(f"备份失败 {文件名}: {e}", "red")
                    错误数量 += 1
    log_emitter.log_signal.emit(f"备份完成: {备份数量}个已备份, {错误数量}个错误", "green")
    return 错误数量 == 0

def 恢复配置文件():
    if not is_running:
        return False
    if not os.path.exists(CONFIG_BACKUP_FOLDER):
        log_emitter.log_signal.emit(f"配置备份文件夹未找到: {CONFIG_BACKUP_FOLDER}", "red")
        return False
    if not os.path.exists(CONFIG_FOLDER):
        try:
            os.makedirs(CONFIG_FOLDER)
            log_emitter.log_signal.emit(f"已创建配置文件夹: {CONFIG_FOLDER}", "green")
        except Exception as e:
            log_emitter.log_signal.emit(f"创建配置文件夹失败: {e}", "red")
            return False

    log_emitter.log_signal.emit("正在恢复配置文件...", "green")
    恢复数量 = 0
    错误数量 = 0
    for 文件名 in os.listdir(CONFIG_BACKUP_FOLDER):
        if is_running:  # 仅运行中执行
            源路径 = os.path.join(CONFIG_BACKUP_FOLDER, 文件名)
            目标路径 = os.path.join(CONFIG_FOLDER, 文件名)
            if os.path.isfile(源路径):
                try:
                    shutil.copy2(源路径, 目标路径)
                    log_emitter.log_signal.emit(f"已恢复: {文件名}", "green")
                    恢复数量 += 1
                except Exception as e:
                    log_emitter.log_signal.emit(f"恢复失败 {文件名}: {e}", "red")
                    错误数量 += 1
    log_emitter.log_signal.emit(f"恢复完成: {恢复数量}个已恢复, {错误数量}个错误", "green")
    return 错误数量 == 0

def 删除指定的_jar():
    if not is_running:
        return True
    if os.path.exists(TARGET_JAR_PATH):
        try:
            os.remove(TARGET_JAR_PATH)
            log_emitter.log_signal.emit(f"已删除: {TARGET_JAR_PATH}", "red")
            return True
        except Exception as e:
            log_emitter.log_signal.emit(f"删除失败: {e}", "red")
            return False
    else:
        log_emitter.log_signal.emit(f"文件不存在: {TARGET_JAR_PATH}", "gray")
        return True

def 检测java进程():
    try:
        if os.name == 'nt':
            result = subprocess.run(['tasklist', '/FI', f'IMAGENAME eq {JAVA_PROCESS_NAME}'], 
                                  capture_output=True, text=True, timeout=5)
            return JAVA_PROCESS_NAME in result.stdout
        else:
            result = subprocess.run(['pgrep', '-f', JAVA_PROCESS_NAME], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
    except Exception as e:
        log_emitter.log_signal.emit(f"检测Java进程时出错: {e}", "red")
        return False

def java进程监控器():
    log_emitter.log_signal.emit("启动Java进程监控...", "yellow")
    java_was_running = 检测java进程()
    while is_running:  # 运行标记控制循环
        time.sleep(5)
        if not is_running:
            break
        java_is_running = 检测java进程()
        if java_was_running != java_is_running:
            if java_is_running and is_running:
                log_emitter.log_signal.emit("检测到Java进程启动", "green")
            else:
                log_emitter.log_signal.emit("检测到Java进程关闭", "yellow")
            java_was_running = java_is_running

# ================================
# Watchdog监控（简化事件处理，避免线程泄漏）
# ================================
class ConfigMonitorHandler(FileSystemEventHandler):
    def on_any_event(self, event):
        if not event.is_directory and is_running:
            config_path = os.path.abspath(event.src_path)
            if config_path.startswith(os.path.abspath(CONFIG_FOLDER)):
                log_emitter.log_signal.emit(f"检测到配置变更: {event.event_type} - {os.path.basename(event.src_path)}", "yellow")
                if is_running:
                    threading.Timer(2.0, 备份配置文件).start()  # 简单定时器，避免线程追踪

class ModsMonitorHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and os.path.abspath(event.src_path) == os.path.abspath(TARGET_JAR_PATH) and is_running:
            log_emitter.log_signal.emit(f"检测到目标文件创建: {TARGET_JAR_PATH}", "red")
            if is_running:
                threading.Timer(2.0, 删除指定的_jar).start()

    def on_modified(self, event):
        if not event.is_directory and os.path.abspath(event.src_path) == os.path.abspath(TARGET_JAR_PATH) and is_running:
            log_emitter.log_signal.emit(f"检测到目标文件修改: {TARGET_JAR_PATH}", "red")
            if is_running:
                threading.Timer(2.0, 删除指定的_jar).start()

def 启动监控线程():
    global observer_config, observer_mods, monitor_thread
    if not is_running:
        return

    # 启动配置监控
    try:
        observer_config = Observer()
        observer_config.schedule(ConfigMonitorHandler(), CONFIG_FOLDER, recursive=True)
        observer_config.start()
        log_emitter.log_signal.emit("配置文件夹监控已启动", "green")
    except Exception as e:
        log_emitter.log_signal.emit(f"配置监控启动失败: {e}", "red")

    # 启动模组监控
    try:
        observer_mods = Observer()
        observer_mods.schedule(ModsMonitorHandler(), MODS_FOLDER, recursive=False)
        observer_mods.start()
        log_emitter.log_signal.emit("模组文件夹监控已启动", "green")
    except Exception as e:
        log_emitter.log_signal.emit(f"模组监控启动失败: {e}", "red")

    # 启动Java监控
    try:
        threading.Thread(target=java进程监控器, daemon=True).start()
    except Exception as e:
        log_emitter.log_signal.emit(f"Java监控启动失败: {e}", "red")

    # 保持监控运行
    while is_running:
        time.sleep(1)

def 启动高级检测工具():
    global is_running, monitor_thread
    if is_running:
        log_emitter.log_signal.emit("高级检测工具已在运行中", "yellow")
        return

    # 启动前初始化
    is_running = True
    log_emitter.log_signal.emit("正在启动高级检测工具...", "green")
    try:
        # 初始操作
        复制所有_mods_from_backup()
        删除指定的_jar()
        备份配置文件()

        # 启动监控（守护线程，随主程序退出）
        monitor_thread = threading.Thread(target=启动监控线程, daemon=True)
        monitor_thread.start()
    except Exception as e:
        log_emitter.log_signal.emit(f"启动失败: {e}", "red")
        is_running = False

# ================================
# 其他基础功能（无线程操作，稳定）
# ================================
def 备份所有模组():
    if not os.path.exists(MODS_BACKUP_FOLDER):
        os.makedirs(MODS_BACKUP_FOLDER)
    if not os.path.exists(MODS_FOLDER):
        log_emitter.log_signal.emit(f"模组文件夹未找到: {MODS_FOLDER}", "red")
        return

    log_emitter.log_signal.emit("正在备份所有模组...", "green")
    备份数量 = 0
    for 文件 in os.listdir(MODS_FOLDER):
        if 文件.endswith('.jar'):
            源路径 = os.path.join(MODS_FOLDER, 文件)
            备份路径 = os.path.join(MODS_BACKUP_FOLDER, 文件)
            try:
                shutil.copy2(源路径, 备份路径)
                log_emitter.log_signal.emit(f"已备份: {文件}", "yellow")
                备份数量 += 1
            except Exception as e:
                log_emitter.log_signal.emit(f"备份失败 {文件}: {e}", "red")
    log_emitter.log_signal.emit(f"备份完成: {备份数量}个模组已备份", "green")

def 从备份恢复模组():
    log_emitter.log_signal.emit("正在从备份恢复模组...", "green")
    复制所有_mods_from_backup()

def 手动备份配置文件():
    log_emitter.log_signal.emit("正在手动备份配置文件...", "green")
    备份配置文件()

def 手动恢复配置文件():
    log_emitter.log_signal.emit("正在手动恢复配置文件...", "green")
    恢复配置文件()

def 删除所有模组():
    确认 = QMessageBox.question(None, "确认删除", "确定删除所有模组? (不可恢复)", 
                               QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
    if 确认 != QMessageBox.Yes:
        log_emitter.log_signal.emit("删除操作已取消", "gray")
        return

    删除数量 = 0
    for 文件 in os.listdir(MODS_FOLDER):
        if 文件.endswith('.jar'):
            try:
                os.remove(os.path.join(MODS_FOLDER, 文件))
                log_emitter.log_signal.emit(f"已删除: {文件}", "red")
                删除数量 += 1
            except Exception as e:
                log_emitter.log_signal.emit(f"删除失败 {文件}: {e}", "red")
    log_emitter.log_signal.emit(f"删除完成: {删除数量}个模组已删除", "green")

# ================================
# UI界面（无复杂线程操作，彻底解决闪退）
# ================================
class MCtoolUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.bind_signals()

    def init_ui(self):
        # 窗口基础设置
        self.setWindowTitle("Netease_MC_tool")
        self.resize(1000, 700)
        self.setStyleSheet("background-color: #202020;")

        # 颜色配置
        self.color_surface = "#303030"
        self.color_yellow = "#FFC145"
        self.color_green = "#33FF33"
        self.color_red = "#FF3333"
        self.color_blue = "#4A90E2"
        self.color_white = "#FFFFFF"
        self.color_gray = "#AAAAAA"

        # 主布局（左右分栏）
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(20)

        # 左侧：终端区（60%）
        left_layout = QVBoxLayout()
        left_layout.setSpacing(15)

        # 终端上侧按钮
        top_btn_layout = QHBoxLayout()
        top_btn_layout.setSpacing(12)
        self.btn_open_mods = self._create_btn("打开模组文件夹", self.color_yellow, "#000")
        self.btn_open_mc = self._create_btn("打开.minecraft文件夹", self.color_yellow, "#000")
        self.btn_open_shader = self._create_btn("打开Shaderpacks文件夹", self.color_yellow, "#000")
        self.btn_create_shader = self._create_btn("创建Shaderpacks文件夹", self.color_blue, self.color_white)
        self.btn_select_launcher = self._create_btn("选择启动器路径", self.color_blue, self.color_white)
        top_btn_layout.addWidget(self.btn_open_mods)
        top_btn_layout.addWidget(self.btn_open_mc)
        top_btn_layout.addWidget(self.btn_open_shader)
        top_btn_layout.addSpacing(20)
        top_btn_layout.addWidget(self.btn_create_shader)
        top_btn_layout.addWidget(self.btn_select_launcher)
        left_layout.addLayout(top_btn_layout)

        # 终端输出框
        terminal_group = QGroupBox("终端输出")
        terminal_group.setStyleSheet(f"""
            QGroupBox {{ color: {self.color_white}; background: {self.color_surface}; border: none; border-radius: 8px; padding: 10px; font-weight: bold; }}
            QGroupBox::title {{ left: 20px; padding: 0 5px; }}
        """)
        self.terminal = QTextEdit()
        self.terminal.setReadOnly(True)
        self.terminal.setStyleSheet(f"background: #202020; color: {self.color_white}; border-radius: 6px; padding: 10px;")
        terminal_layout = QVBoxLayout(terminal_group)
        terminal_layout.addWidget(self.terminal)
        left_layout.addWidget(terminal_group, 1)
        main_layout.addLayout(left_layout, 6)

        # 右侧：功能区（40%）
        right_layout = QVBoxLayout()
        right_layout.setSpacing(20)

        # 关键路径配置（已放大）
        path_frame = QWidget()
        path_frame.setStyleSheet(f"background: {self.color_surface}; border-radius: 8px;")
        path_layout = QVBoxLayout(path_frame)
        path_layout.setContentsMargins(20, 20, 20, 20)
        path_label = QLabel("关键路径配置：")
        path_label.setStyleSheet(f"color: {self.color_white}; font-size:14px; font-weight: bold;")
        self.path_text = QTextEdit()
        self.path_text.setReadOnly(True)
        self.path_text.setStyleSheet(f"background: #202020; color: {self.color_gray}; border-radius: 6px; padding:12px; font-size:13px;")
        self.path_text.setFixedHeight(120)
        self._update_path_text()
        path_layout.addWidget(path_label)
        path_layout.addWidget(self.path_text)
        right_layout.addWidget(path_frame)

        # 核心功能按钮
        core_btn_layout = QVBoxLayout()
        core_btn_layout.setSpacing(12)
        self.btn_backup_mods = self._create_btn("备份所有模组", self.color_green, "#000")
        self.btn_restore_mods = self._create_btn("从备份恢复模组", self.color_green, "#000")
        self.btn_backup_config = self._create_btn("手动备份配置", self.color_blue, self.color_white)
        self.btn_restore_config = self._create_btn("手动恢复配置", self.color_blue, self.color_white)
        self.btn_delete_mods = self._create_btn("删除所有模组", self.color_red, self.color_white)
        core_btn_layout.addWidget(self.btn_backup_mods)
        core_btn_layout.addWidget(self.btn_restore_mods)
        core_btn_layout.addWidget(self.btn_backup_config)
        core_btn_layout.addWidget(self.btn_restore_config)
        core_btn_layout.addWidget(self.btn_delete_mods)
        right_layout.addLayout(core_btn_layout)

        # 底部启停按钮
        bottom_btn_layout = QHBoxLayout()
        bottom_btn_layout.setSpacing(15)
        self.btn_stop = self._create_btn("关闭工具", self.color_red, self.color_white)
        self.btn_start = self._create_btn("启用工具（高级检测）", self.color_green, "#000")
        self.btn_stop.setFixedSize(120, 40)
        self.btn_start.setFixedSize(180, 40)
        bottom_btn_layout.addWidget(self.btn_stop)
        bottom_btn_layout.addWidget(self.btn_start)
        right_layout.addLayout(bottom_btn_layout)
        main_layout.addLayout(right_layout, 4)

    def _create_btn(self, text, bg, text_color):
        """创建稳定的按钮样式"""
        btn = QPushButton(text)
        btn.setStyleSheet(f"""
            QPushButton {{ background: {bg}; color: {text_color}; border: none; border-radius: 8px; padding: 8px 15px; font-weight: bold; font-size:12px; }}
            QPushButton:hover {{ opacity: 0.9; }}
            QPushButton:pressed {{ opacity: 0.8; }}
        """)
        return btn

    def _update_path_text(self):
        """显示完整路径"""
        path_content = f"""模组文件夹：{MODS_FOLDER}
模组备份文件夹：{MODS_BACKUP_FOLDER}
配置文件夹：{CONFIG_FOLDER}
配置备份文件夹：{CONFIG_BACKUP_FOLDER}
Shaderpacks文件夹：{SHADERPACKS_FOLDER}
目标JAR文件：{TARGET_JAR_PATH}"""
        self.path_text.setText(path_content)

    def bind_signals(self):
        """绑定信号（无复杂逻辑，避免闪退）"""
        # 顶部按钮
        self.btn_open_mods.clicked.connect(lambda: os.startfile(MODS_FOLDER))
        self.btn_open_mc.clicked.connect(lambda: os.startfile(os.path.dirname(MODS_FOLDER)))
        self.btn_open_shader.clicked.connect(lambda: os.startfile(SHADERPACKS_FOLDER))
        self.btn_create_shader.clicked.connect(self._create_shader)
        self.btn_select_launcher.clicked.connect(self._select_launcher)

        # 核心功能按钮
        self.btn_backup_mods.clicked.connect(备份所有模组)
        self.btn_restore_mods.clicked.connect(从备份恢复模组)
        self.btn_backup_config.clicked.connect(手动备份配置文件)
        self.btn_restore_config.clicked.connect(手动恢复配置文件)
        self.btn_delete_mods.clicked.connect(删除所有模组)

        # 启停按钮
        self.btn_start.clicked.connect(启动高级检测工具)
        self.btn_stop.clicked.connect(self._close_tool)

        # 日志更新
        log_emitter.log_signal.connect(self._update_terminal)

    def _create_shader(self):
        os.makedirs(SHADERPACKS_FOLDER, exist_ok=True)
        log_emitter.log_signal.emit(f"Shaderpacks文件夹已创建：{SHADERPACKS_FOLDER}", "green")

    def _select_launcher(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择网易启动器", "", "EXE文件 (*.exe)")
        if path:
            log_emitter.log_signal.emit(f"已选择启动器路径：{path}", "green")

    def _close_tool(self):
        """安全关闭：仅修改标记，依赖守护线程自动退出"""
        global is_running, observer_config, observer_mods
        if not is_running:
            self.close()
            return

        # 1. 修改运行标记，触发所有循环退出
        is_running = False
        log_emitter.log_signal.emit("正在关闭所有功能...", "yellow")

        # 2. 停止watchdog观察者（安全方式）
        if observer_config:
            observer_config.stop()
            observer_config.join(timeout=1)
            observer_config = None
            log_emitter.log_signal.emit("配置监控已关闭", "yellow")
        if observer_mods:
            observer_mods.stop()
            observer_mods.join(timeout=1)
            observer_mods = None
            log_emitter.log_signal.emit("模组监控已关闭", "yellow")

        # 3. 延迟关闭窗口，确保所有功能退出
        threading.Timer(1.0, self.close).start()

    def _update_terminal(self, content, color):
        """稳定的终端更新"""
        color_map = {"red":"#FF3333", "green":"#33FF33", "yellow":"#FFC145", "gray":"#AAAAAA"}
        time_str = time.strftime("[%H:%M:%S]", time.localtime())
        self.terminal.insertHtml(f'<span style="color:{color_map.get(color,"#FFF")};">{time_str} {content}</span><br>')
        self.terminal.moveCursor(QTextCursor.End)

    def closeEvent(self, event):
        """窗口关闭时确保功能停止"""
        global is_running
        is_running = False
        event.accept()

# ================================
# 程序入口（无额外依赖，稳定启动）
# ================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MCtoolUI()
    window.show()
    sys.exit(app.exec_())
