import sys
import re
from PyQt5.QtWidgets import QApplication, QTextEdit, QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPoint
from PyQt5.QtGui import QTextCursor, QTextCharFormat, QColor
import Drissionpage

class CrawlerThread(QThread):
    progress_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()
    def __init__(self, url):
        super().__init__()
        self.url = url
    def run(self):
        try:
            Drissionpage.run_crawler(self.url, self.progress_signal.emit)
        except Exception as e:
            self.progress_signal.emit(f"[錯誤] 爬蟲執行時發生錯誤: {e}")
        finally:
            self.finished_signal.emit()

class CmdEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: black; color: white; font-family: Consolas, monospace; font-size: 15px;")
        self.setLineWrapMode(QTextEdit.WidgetWidth)
        self.setUndoRedoEnabled(False)
        self.setAcceptRichText(False)
        self.setTabChangesFocus(True)
        self.setCursorWidth(10)
        self.setReadOnly(False)
        self.prompt = '> '
        self.cmd_mode = True
        self.history = []
        self.history_idx = -1
        self.resize(800, 500)
        # LOGO設計
        logo = [
            "      ██████╗  ██████╗ ██╗   ██╗██╗███╗   ██╗ ",
            "     ██╔════╝ ██╔═══██╗██║   ██║██║████╗  ██║ ",
            "     ██║  ███╗██║   ██║██║   ██║██║██╔██╗ ██║ ",
            "     ██║   ██║██║   ██║╚██╗ ██╔╝██║██║╚██╗██║ ",
            "     ╚██████╔╝╚██████╔╝ ╚████╔╝ ██║██║ ╚████║ ",
            "      ╚═════╝  ╚═════╝   ╚═══╝  ╚═╝╚═╝  ╚═══╝ ",
            "         抖音爬蟲工具  DOUYIN SPIDER CMD      ",
        ]
        for line in logo:
            self.append(line.center(48))
        self.append("作者: 545ii".center(48))
        self.append("----------------------------------------")
        self.append("請輸入目標抖音網址，然後按 Enter：")
        self.append("或輸入 'headers' 查詢環境變數設置狀態")
        self.append("或輸入 'create-env' 創建 .env 文件")
        self.append("或輸入 'clear' 清空並重置")
        self.new_prompt()
        self.last_prompt_pos = self.textCursor().position()
        self.crawler_thread = None
        self.waiting_url = True
        self.creating_env = False
        self.env_step = 0
        self.env_data = {}
        self.setFocus()

    def new_prompt(self):
        doc = self.toPlainText()
        lines = doc.splitlines()
        # 如果最後一行已經是 prompt，不要重複加
        if lines and lines[-1].startswith(self.prompt):
            return
        self.append(self.prompt)
        self.moveCursor(QTextCursor.End)
        self.ensureCursorVisible()
        self.last_prompt_pos = self.textCursor().position()

    def keyPressEvent(self, event):
        cursor = self.textCursor()
        if cursor.position() < self.last_prompt_pos:
            cursor.setPosition(self.document().characterCount()-1)
            self.setTextCursor(cursor)
        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_C:
            self.copy()
            return
        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_V:
            self.paste()
            return
        if event.key() == Qt.Key_Up and self.history:
            if self.history_idx == -1:
                self.history_idx = len(self.history)-1
            else:
                self.history_idx = max(0, self.history_idx-1)
            self.replace_input(self.history[self.history_idx])
            return
        if event.key() == Qt.Key_Down and self.history:
            if self.history_idx == -1:
                return
            self.history_idx += 1
            if self.history_idx >= len(self.history):
                self.replace_input('')
                self.history_idx = -1
            else:
                self.replace_input(self.history[self.history_idx])
            return
        if event.key() in (Qt.Key_Backspace, Qt.Key_Left):
            if self.textCursor().position() <= self.last_prompt_pos:
                return
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            user_input = self.get_current_input().strip()
            self.append("")
            self.history.append(user_input)
            self.history_idx = -1
            self.handle_input(user_input)
            return
        super().keyPressEvent(event)
        if self.textCursor().position() < self.last_prompt_pos:
            cursor = self.textCursor()
            cursor.setPosition(self.document().characterCount()-1)
            self.setTextCursor(cursor)

    def get_current_input(self):
        doc = self.toPlainText()
        lines = doc.splitlines()
        if not lines:
            return ''
        last = lines[-1]
        if last.startswith(self.prompt):
            return last[len(self.prompt):]
        return ''

    def replace_input(self, text):
        doc = self.toPlainText()
        lines = doc.splitlines()
        if not lines:
            return
        if lines[-1].startswith(self.prompt):
            lines[-1] = self.prompt + text
            self.setPlainText('\n'.join(lines))
            self.moveCursor(QTextCursor.End)
            self.last_prompt_pos = self.textCursor().position() - len(text)

    def print_line(self, text):
        doc = self.toPlainText()
        lines = doc.splitlines()
        # 如果最後一行是 prompt，先移除
        if lines and lines[-1].startswith(self.prompt):
            lines = lines[:-1]
        lines.append(text)
        self.setPlainText('\n'.join(lines))
        
        # 應用顏色格式
        self.apply_color_formatting()
        
        self.moveCursor(QTextCursor.End)
        self.ensureCursorVisible()
        self.last_prompt_pos = self.textCursor().position()

    def apply_color_formatting(self):
        """應用顏色格式到文本"""
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.Start)
        cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
        
        # 創建顏色格式
        error_format = QTextCharFormat()
        error_format.setForeground(QColor(255, 0, 0))  # 紅色
        
        message_format = QTextCharFormat()
        message_format.setForeground(QColor(0, 255, 0))  # 綠色
        
        hint_format = QTextCharFormat()
        hint_format.setForeground(QColor(255, 255, 0))  # 黃色
        
        normal_format = QTextCharFormat()
        normal_format.setForeground(QColor(255, 255, 255))  # 白色
        
        # 獲取所有文本
        text = self.toPlainText()
        
        # 重置格式為白色
        cursor.setCharFormat(normal_format)
        
        # 查找並應用顏色
        import re
        
        # 處理 [錯誤] 為紅色
        error_pattern = r'\[錯誤\]'
        for match in re.finditer(error_pattern, text):
            cursor.setPosition(match.start())
            cursor.setPosition(match.end(), QTextCursor.KeepAnchor)
            cursor.setCharFormat(error_format)
        
        # 處理 [訊息] 為綠色
        message_pattern = r'\[訊息\]'
        for match in re.finditer(message_pattern, text):
            cursor.setPosition(match.start())
            cursor.setPosition(match.end(), QTextCursor.KeepAnchor)
            cursor.setCharFormat(message_format)
        
        # 處理 [提示] 為黃色
        hint_pattern = r'\[提示\]'
        for match in re.finditer(hint_pattern, text):
            cursor.setPosition(match.start())
            cursor.setPosition(match.end(), QTextCursor.KeepAnchor)
            cursor.setCharFormat(hint_format)
        
        # 處理 [警告] 為黃色
        warning_pattern = r'\[警告\]'
        for match in re.finditer(warning_pattern, text):
            cursor.setPosition(match.start())
            cursor.setPosition(match.end(), QTextCursor.KeepAnchor)
            cursor.setCharFormat(hint_format)
        
        # 處理 [完成] 為綠色
        complete_pattern = r'\[完成\]'
        for match in re.finditer(complete_pattern, text):
            cursor.setPosition(match.start())
            cursor.setPosition(match.end(), QTextCursor.KeepAnchor)
            cursor.setCharFormat(message_format)
        
        # 處理 [載入] 為綠色
        loading_pattern = r'\[載入\]'
        for match in re.finditer(loading_pattern, text):
            cursor.setPosition(match.start())
            cursor.setPosition(match.end(), QTextCursor.KeepAnchor)
            cursor.setCharFormat(message_format)

    def handle_input(self, user_input):
        self.print_line(f"> {user_input}")
        
        # 如果正在創建環境變數，優先處理
        if self.creating_env:
            self.handle_env_creation(user_input)
            return
        
        # 新增 headers 查詢指令
        if user_input.lower() in ['headers', 'header', 'h']:
            self.print_line("[訊息] 查詢 Headers 內容...")
            try:
                import os
                from dotenv import load_dotenv
                
                # 重新加載環境變數
                load_dotenv()
                
                # 獲取環境變數
                cookie = os.getenv("DOUYIN_COOKIE")
                referer = os.getenv("DOUYIN_REFERER")
                user_agent = os.getenv("DOUYIN_UA")
                
                self.print_line("=== Headers 內容 ===")
                self.print_line(f"Cookie: {'已設置' if cookie else '未設置'}")
                if cookie:
                    self.print_line(f"  Cookie 長度: {len(cookie)} 字符")
                    self.print_line(f"  Cookie 預覽: {cookie[:50]}...")
                else:
                    self.print_line("  [警告] DOUYIN_COOKIE 環境變數未設置")
                
                self.print_line(f"Referer: {'已設置' if referer else '未設置'}")
                if referer:
                    self.print_line(f"  Referer: {referer}")
                else:
                    self.print_line("  [警告] DOUYIN_REFERER 環境變數未設置")
                
                self.print_line(f"User-Agent: {'已設置' if user_agent else '未設置'}")
                if user_agent:
                    self.print_line(f"  User-Agent 長度: {len(user_agent)} 字符")
                    self.print_line(f"  User-Agent 預覽: {user_agent[:50]}...")
                else:
                    self.print_line("  [警告] DOUYIN_UA 環境變數未設置")
                
                # 檢查 .env 文件是否存在
                env_file_exists = os.path.exists(".env")
                self.print_line(f".env 文件: {'存在' if env_file_exists else '不存在'}")
                
                if not env_file_exists:
                    self.print_line("[提示] 請創建 .env 文件並設置以下環境變數:")
                    self.print_line("  DOUYIN_COOKIE=你的抖音Cookie")
                    self.print_line("  DOUYIN_REFERER=你的抖音Referer")
                    self.print_line("  DOUYIN_UA=你的User-Agent")
                    self.print_line("[提示] 或輸入 'create-env' 來創建 .env 文件")
                
                self.print_line("==================")
                
            except Exception as e:
                self.print_line(f"[錯誤] 查詢 Headers 時發生錯誤: {e}")
            
            self.new_prompt()
            return
        
        # 新增創建 .env 文件指令
        if user_input.lower() in ['create-env', 'createenv', 'env']:
            self.start_env_creation()
            return
        
        # 新增清空指令
        if user_input.lower() in ['clear', 'cls', '清空', '重置']:
            self.reset_to_initial_state()
            return
        
        if self.waiting_url:
            if not self.is_valid_url(user_input):
                self.print_line("[錯誤] 請輸入有效的抖音網址！")
                self.new_prompt()
                return
            self.clear_all()
            self.print_line("[訊息] 網址有效，開始檢測帳戶總影片數量...")
            self.waiting_url = False
            self.start_crawler(user_input)
        else:
            # 如果爬蟲正在運行，檢查是否有停止命令
            if user_input.lower() in ['stop', '停止', 'quit', '退出']:
                if self.crawler_thread and self.crawler_thread.isRunning():
                    self.print_line("[訊息] 正在停止爬蟲...")
                    self.crawler_thread.terminate()
                    self.crawler_thread.wait()
                    self.crawler_thread = None
                    self.waiting_url = True
                    self.print_line("[完成] 爬蟲已停止。請輸入新的抖音網址：")
                    self.new_prompt()
                else:
                    self.print_line("[提示] 目前只需等待爬蟲完成，無其他指令。")
                    self.new_prompt()
            else:
                self.print_line("[提示] 目前只需等待爬蟲完成，無其他指令。")
                self.new_prompt()

    def is_valid_url(self, url):
        pattern = r'^https?://(www\.)?douyin\.com/.*'
        return re.match(pattern, url)

    def start_crawler(self, url):
        self.crawler_thread = CrawlerThread(url)
        self.crawler_thread.progress_signal.connect(self.print_line)
        self.crawler_thread.finished_signal.connect(self.on_crawler_finished)
        self.crawler_thread.start()

    def on_crawler_finished(self):
        # 清除爬蟲線程
        if self.crawler_thread:
            self.crawler_thread.quit()
            self.crawler_thread.wait()
            self.crawler_thread = None
        
        # 重置狀態
        self.waiting_url = True
        
        self.print_line("[完成] 爬蟲任務已結束。")
        self.print_line("請輸入新的抖音網址，然後按 Enter：")
        self.new_prompt()

    def start_env_creation(self):
        """開始創建 .env 文件的流程"""
        self.creating_env = True
        self.env_step = 0
        self.env_data = {}
        
        self.clear_all()
        self.print_line("[訊息] 開始創建 .env 文件...")
        self.print_line("請按照以下順序輸入環境變數內容：")
        self.print_line("")
        self.print_line("步驟 1/3: 請輸入 DOUYIN_COOKIE")
        self.print_line("提示: 從瀏覽器開發者工具中複製抖音網站的 Cookie")
        self.print_line("格式範例: sessionid=abc123; ttwid=def456; msToken=ghi789")
        self.new_prompt()

    def handle_env_creation(self, user_input):
        """處理環境變數創建過程中的用戶輸入"""
        if self.env_step == 0:  # 輸入 Cookie
            if not user_input.strip():
                self.print_line("[錯誤] Cookie 不能為空，請重新輸入：")
                self.new_prompt()
                return
            
            self.env_data['DOUYIN_COOKIE'] = user_input.strip()
            self.env_step = 1
            
            self.print_line(f"[訊息] Cookie 已設置 (長度: {len(user_input.strip())} 字符)")
            self.print_line("")
            self.print_line("步驟 2/3: 請輸入 DOUYIN_REFERER")
            self.print_line("提示: 通常是抖音用戶頁面的 URL")
            self.print_line("格式範例: https://www.douyin.com/user/MS4wLjABAAAA...")
            self.new_prompt()
            
        elif self.env_step == 1:  # 輸入 Referer
            if not user_input.strip():
                self.print_line("[錯誤] Referer 不能為空，請重新輸入：")
                self.new_prompt()
                return
            
            # 簡單驗證 URL 格式
            if not user_input.strip().startswith(('http://', 'https://')):
                self.print_line("[警告] Referer 應該是一個有效的 URL，但將繼續保存")
            
            self.env_data['DOUYIN_REFERER'] = user_input.strip()
            self.env_step = 2
            
            self.print_line(f"[訊息] Referer 已設置: {user_input.strip()}")
            self.print_line("")
            self.print_line("步驟 3/3: 請輸入 DOUYIN_UA (User-Agent)")
            self.print_line("提示: 從瀏覽器開發者工具中複製 User-Agent")
            self.print_line("格式範例: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit...")
            self.new_prompt()
            
        elif self.env_step == 2:  # 輸入 User-Agent
            if not user_input.strip():
                self.print_line("[錯誤] User-Agent 不能為空，請重新輸入：")
                self.new_prompt()
                return
            
            self.env_data['DOUYIN_UA'] = user_input.strip()
            
            # 創建 .env 文件
            try:
                with open('.env', 'w', encoding='utf-8') as f:
                    f.write(f"DOUYIN_COOKIE={self.env_data['DOUYIN_COOKIE']}\n")
                    f.write(f"DOUYIN_REFERER={self.env_data['DOUYIN_REFERER']}\n")
                    f.write(f"DOUYIN_UA={self.env_data['DOUYIN_UA']}\n")
                
                self.print_line(f"[訊息] User-Agent 已設置 (長度: {len(user_input.strip())} 字符)")
                self.print_line("")
                self.print_line("✅ .env 文件創建成功！")
                self.print_line("文件內容已保存到 .env 文件中")
                self.print_line("")
                self.print_line("您現在可以：")
                self.print_line("1. 輸入 'headers' 查看設置狀態")
                self.print_line("2. 輸入抖音網址開始爬蟲")
                
            except Exception as e:
                self.print_line(f"[錯誤] 創建 .env 文件時發生錯誤: {e}")
            
            # 重置狀態
            self.creating_env = False
            self.env_step = 0
            self.env_data = {}
            self.waiting_url = True
            self.new_prompt()

    def reset_to_initial_state(self):
        """重置到初始狀態，顯示 LOGO 和初始提示"""
        # 停止正在運行的爬蟲
        if self.crawler_thread and self.crawler_thread.isRunning():
            self.print_line("[訊息] 正在停止爬蟲...")
            self.crawler_thread.terminate()
            self.crawler_thread.wait()
            self.crawler_thread = None
        
        # 重置所有狀態
        self.waiting_url = True
        self.creating_env = False
        self.env_step = 0
        self.env_data = {}
        
        # 清空內容並重新顯示 LOGO
        self.clear_all()
        
        # 重新顯示 LOGO
        logo = [
            "      ██████╗  ██████╗ ██╗   ██╗██╗███╗   ██╗ ",
            "     ██╔════╝ ██╔═══██╗██║   ██║██║████╗  ██║ ",
            "     ██║  ███╗██║   ██║██║   ██║██║██╔██╗ ██║ ",
            "     ██║   ██║██║   ██║╚██╗ ██╔╝██║██║╚██╗██║ ",
            "     ╚██████╔╝╚██████╔╝ ╚████╔╝ ██║██║ ╚████║ ",
            "      ╚═════╝  ╚═════╝   ╚═══╝  ╚═╝╚═╝  ╚═══╝ ",
            "         抖音爬蟲工具  DOUYIN SPIDER CMD      ",
        ]
        for line in logo:
            self.append(line.center(48))
        self.append("作者: 545ii".center(48))
        self.append("----------------------------------------")
        self.append("請輸入目標抖音網址，然後按 Enter：")
        self.append("或輸入 'headers' 查詢環境變數設置狀態")
        self.append("或輸入 'create-env' 創建 .env 文件")
        self.append("或輸入 'clear' 清空並重置")
        self.new_prompt()

    def clear_all(self):
        self.setPlainText("")
        # 重置顏色格式
        cursor = self.textCursor()
        cursor.select(QTextCursor.Document)
        normal_format = QTextCharFormat()
        normal_format.setForeground(QColor(255, 255, 255))  # 白色
        cursor.setCharFormat(normal_format)
        cursor.clearSelection()
        
        self.moveCursor(QTextCursor.End)
        self.ensureCursorVisible()
        self.last_prompt_pos = self.textCursor().position()

    def focusInEvent(self, event):
        self.moveCursor(QTextCursor.End)
        self.ensureCursorVisible()
        super().focusInEvent(event)

    def mousePressEvent(self, event):
        self.moveCursor(QTextCursor.End)
        self.ensureCursorVisible()
        super().mousePressEvent(event)

class CustomFrame(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(800, 500)
        self.drag_pos = None
        # 內容主體圓角（無灰底）
        self.bg = QWidget(self)
        self.bg.setStyleSheet('''
            background-color: transparent;
            border-radius: 10px;
        ''')
        self.bg.setGeometry(0, 0, 800, 500)
        # 標題列（僅上方有灰底、白字、圓角）
        self.title_bar = QWidget(self.bg)
        self.title_bar.setStyleSheet('''
            background-color: #444444;
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
            border-bottom-left-radius: 0px;
            border-bottom-right-radius: 0px;
        ''')
        self.title_bar.setFixedHeight(32)
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(10, 0, 6, 0)
        title_layout.setSpacing(0)
        self.title_label = QTextEdit('抖音爬蟲工具', self.title_bar)
        self.title_label.setReadOnly(True)
        self.title_label.setStyleSheet('background: transparent; color: white; border: none; font-size: 15px; font-weight: bold;')
        self.title_label.setMaximumHeight(28)
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()
        self.close_btn = QPushButton('✕', self.title_bar)
        self.close_btn.setFixedSize(24, 24)
        self.close_btn.setStyleSheet('''
            QPushButton { background: #888888; color: white; border: none; border-radius: 12px; font-size: 14px; }
            QPushButton:hover { background: #ff4444; }
        ''')
        self.close_btn.clicked.connect(self.close)
        title_layout.addWidget(self.close_btn)
        # 內容區
        self.cmd = CmdEdit(self.bg)
        self.cmd.move(0, 32)
        self.cmd.resize(800, 468)
        # 佈局
        self.bg.move(0, 0)
        self.bg.resize(800, 500)
        self.title_bar.move(0, 0)
        self.title_bar.resize(800, 32)
    def resizeEvent(self, event):
        self.bg.resize(self.width(), self.height())
        self.title_bar.resize(self.width(), 32)
        self.cmd.resize(self.width(), self.height()-32)
        self.cmd.move(0, 32)
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and event.y() < 32:
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_pos:
            self.move(event.globalPos() - self.drag_pos)
            event.accept()
    def mouseReleaseEvent(self, event):
        self.drag_pos = None

def main():
    app = QApplication(sys.argv)
    win = CustomFrame()
    win.show()
    win.setFocus()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
