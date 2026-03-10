import customtkinter as ctk
import threading
import json
import os
import time
from main import HotPepperScraper
import logging
import queue
import sys
from tkinter import messagebox  # エラー表示用

# --- Macでのリソース読み込み問題を解決するパッチ ---
if getattr(sys, 'frozen', False):
    # .app内のResourcesフォルダを取得
    bundle_dir = os.path.join(os.path.dirname(sys.executable), "..", "Resources")
    ctk_path = os.path.join(bundle_dir, "customtkinter")
    if os.path.exists(ctk_path):
        import customtkinter
        customtkinter.windows.widgets.appearance_mode.AppearanceModeTracker.init_appearance_mode()
        ctk.set_default_color_theme(os.path.join(ctk_path, "assets", "themes", "blue.json"))

# GUIのログ表示用のカスタムハンドラ
class TextboxHandler(logging.Handler):
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        try:
            msg = self.format(record)
            # GUIを操作せず、キューにメッセージを入れるだけ（スレッドセーフ）
            self.log_queue.put(msg)
        except Exception:
            pass

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # ログメッセージを貯めるための安全なキュー(サブスレッドから使用)
        self.log_queue = queue.Queue()

        self.logger = logging.getLogger("Scraper")
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        log_path = self.get_external_path("scraper.log")
        fh = logging.FileHandler(log_path, encoding='utf-8')
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

        # TextboxHandlerを、直接afterを呼ばずキューに積む設計に修正
        tbh = TextboxHandler(self.log_queue) 
        self.logger.addHandler(tbh)

        self.title("HotPepper Scraper")
        self.geometry("500x500")

        self.var_area = ctk.StringVar(value="読み込み中...")
        self.var_genre = ctk.StringVar(value="読み込み中...")

        # 2. 入力フォームに textvariable を指定
        ctk.CTkLabel(self, text="ターゲットエリア:").pack(pady=(20, 0))
        self.entry_area = ctk.CTkEntry(self, width=300, textvariable=self.var_area)
        self.entry_area.pack(pady=10)

        ctk.CTkLabel(self, text="ターゲットジャンル:").pack(pady=(10, 0))
        self.entry_genre = ctk.CTkEntry(self, width=300, textvariable=self.var_genre)
        self.entry_genre.pack(pady=10)

        self.button = ctk.CTkButton(self, text="実行開始", command=self.start_thread, state="disabled")
        self.button.pack(pady=20)

        self.log_textbox = ctk.CTkTextbox(self, width=400, height=200)
        self.log_textbox.pack(pady=10)

        # 100ミリ秒ごとにキューをチェックする定期処理を開始
        self.check_log_queue()

        # --- 設定の読み込み ---
        # App クラス内で以下のように読み込む
        try:
            self.config_path = self.get_external_path("config.json")
            if not os.path.exists(self.config_path):
                self.logger.error(f"エラー: config.json が見つかりません。探した場所: {self.config_path}")
                return

            with open(self.config_path, "r", encoding="utf-8") as f:
                self.base_config = json.load(f)

            # 1. StringVar を使って値を管理する
            self.var_area.set(self.base_config["search"]["target_area_key"])
            self.var_genre.set(self.base_config["search"]["target_genre_key"])
            self.button.configure(state="normal")
            self.logger.info("アプリが正常に起動しました。")
        except Exception as e:
            error_msg = f"初期化エラー: {e}\n場所: {getattr(self, 'config_path', '不明')}"
            messagebox.showerror("起動失敗", error_msg)
            print(error_msg) # ターミナル用

    @staticmethod
    def get_external_path(relative_path):
        """
        .app の「外側」（ユーザーに見える場所）のパスを取得
        config.json, scraper.log, shop_list.csv 用
        """
        if getattr(sys, 'frozen', False):
            # 実行ファイルから遡って .app の親ディレクトリを探す
            p = os.path.abspath(sys.executable)
            while p != "/":
                if p.endswith(".app"):
                    return os.path.join(os.path.dirname(p), relative_path)
                p = os.path.dirname(p)
            return os.path.join(os.path.dirname(os.path.abspath(sys.executable)), relative_path)
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)
    
    @staticmethod
    def get_internal_resource_path(relative_path):
        """
        .app の「内部」（PyInstallerの一時展開先）のパスを取得
        ライブラリや同梱リソース用
        """
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)

    def check_log_queue(self):
        try:
            while True:
                msg = self.log_queue.get_nowait()
                # 終了合図をチェック
                if msg == "__FINISH__":
                    self._on_finish()
                else:
                    self._add_log_main_thread(msg)
        except queue.Empty:
            pass

        # 継続してチェックをスケジュール
        self.after(100, self.check_log_queue)

    def _add_log_main_thread(self, message):
        self.log_textbox.insert("end", message + "\n")
        self.log_textbox.see("end")

    def start_thread(self):
        self.button.configure(state="disabled")
        self.log_textbox.delete("1.0", "end")

        # 【重要】メインスレッドで値を取得しておく
        area = self.var_area.get()
        genre = self.var_genre.get()

        # 引数として値を渡す
        thread = threading.Thread(target=self.run_logic, args=(area, genre), daemon=True)
        thread.start()

    def run_logic(self, area, genre):
        self.logger.info("処理を開始します...")
        
        try:            
            # 設定の更新
            import copy
            new_config = copy.deepcopy(self.base_config)
            new_config["search"]["target_area_key"] = area
            new_config["search"]["target_genre_key"] = genre

            self.logger.info(f"開始: {area} - {genre}")

            # 2. スクレイピング実行
            scraper = HotPepperScraper(new_config, gui_mode=True)
            scraper.run()

            # 修正：after を使わず、確実に動作しているキューに「終了合図」を送る
            self.log_queue.put("__FINISH__")

        except Exception as e:
            self.logger.error(f"エラー: {e}")
            self.log_queue.put("__FINISH__")

    def _on_finish(self):
        # これが必ずメインスレッド上で動く
        self.button.configure(state="normal")
        self.logger.info("--- データ収集完了 ---")

if __name__ == "__main__":
    app = App()
    app.mainloop()