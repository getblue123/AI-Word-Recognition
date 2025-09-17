# gui_interface.py - GUI介面模組（改進版）
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
from video_processor import VideoProfanityFilter


class FilterGUI:
    """GUI介面類"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("影片特殊字詞過濾器")
        self.root.geometry("600x700")
        
        # 設置最小視窗大小
        self.root.minsize(500, 600)
        
        # 創建主框架
        self.main_frame = tk.Frame(root, bg="#f0f0f0")
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.filter = VideoProfanityFilter()
        
        # 建立界面
        self.create_widgets()
        
        # 綁定視窗調整事件
        self.root.bind('<Configure>', self.on_window_resize)
    
    def create_widgets(self):
        """創建GUI元件"""
        # 標題 - 固定在頂部
        title_label = tk.Label(self.main_frame, text="影片語音特殊字詞自動消音器", 
                             font=("Arial", 18, "bold"), 
                             bg="#f0f0f0", fg="#333333")
        title_label.pack(pady=15)
        
        # 創建滾動區域
        self.create_scrollable_area()
        
        # 在滾動區域內創建所有設定
        self._create_file_selection_frame()
        self._create_language_selection_frame()
        self._create_segment_settings_frame()
        self._create_muting_settings_frame()
        self._create_recognition_settings_frame()
        self._create_custom_words_frame()
        
        # 處理按鈕和進度顯示 - 固定在底部
        self._create_process_controls()
    
    def create_scrollable_area(self):
        """創建可滾動的設定區域"""
        # 創建容器框架
        container_frame = tk.Frame(self.main_frame, bg="#f0f0f0")
        container_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # 創建滾動畫布和滾動條
        self.canvas = tk.Canvas(container_frame, bg="#f0f0f0", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(container_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="#f0f0f0")
        
        # 配置滾動
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # 佈局滾動元件
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # 綁定滑鼠滾輪事件
        self._bind_mousewheel()
    
    def _bind_mousewheel(self):
        """綁定滑鼠滾輪事件"""
        def _on_mousewheel(event):
            # 檢查滾動是否需要（內容超出視窗）
            if self.canvas.winfo_height() < self.scrollable_frame.winfo_reqheight():
                self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _bind_to_mousewheel(event):
            self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        def _unbind_from_mousewheel(event):
            self.canvas.unbind_all("<MouseWheel>")
        
        # 當滑鼠進入canvas時綁定滾輪，離開時解綁
        self.canvas.bind('<Enter>', _bind_to_mousewheel)
        self.canvas.bind('<Leave>', _unbind_from_mousewheel)
        
        # 支援Linux/Mac的滾輪事件
        def _on_mousewheel_linux(event):
            if self.canvas.winfo_height() < self.scrollable_frame.winfo_reqheight():
                if event.num == 4:
                    self.canvas.yview_scroll(-1, "units")
                elif event.num == 5:
                    self.canvas.yview_scroll(1, "units")
        
        # 綁定Linux/Mac滾輪事件
        self.canvas.bind("<Button-4>", _on_mousewheel_linux)
        self.canvas.bind("<Button-5>", _on_mousewheel_linux)
    
    def on_window_resize(self, event):
        """處理視窗大小改變事件"""
        # 只處理主視窗的resize事件
        if event.widget == self.root:
            # 更新canvas寬度
            canvas_width = event.width - 50  # 減去padding和滾動條寬度
            self.canvas.configure(width=canvas_width)
    
    def _create_file_selection_frame(self):
        """檔案選擇區域"""
        file_frame = tk.LabelFrame(self.scrollable_frame, text="📁 檔案選擇", 
                                 font=("Arial", 12, "bold"), 
                                 bg="#f0f0f0", padx=10, pady=10)
        file_frame.pack(pady=5, padx=10, fill="x")
        
        tk.Label(file_frame, text="選擇影片檔案:", 
                font=("Arial", 11), bg="#f0f0f0").pack(anchor="w")
        
        entry_frame = tk.Frame(file_frame, bg="#f0f0f0")
        entry_frame.pack(fill="x", pady=5)
        
        self.file_path = tk.StringVar()
        file_entry = tk.Entry(entry_frame, textvariable=self.file_path, 
                            font=("Arial", 10), relief="solid", borderwidth=1)
        file_entry.pack(side="left", fill="x", expand=True)
        
        browse_btn = tk.Button(entry_frame, text="📁 瀏覽", 
                             command=self.browse_file,
                             bg="#e0e0e0", 
                             font=("Arial", 10),
                             relief="raised",
                             cursor="hand2")
        browse_btn.pack(side="right", padx=(10, 0), ipadx=10)
    
    def _create_language_selection_frame(self):
        """語言選擇區域"""
        lang_frame = tk.LabelFrame(self.scrollable_frame, text="🌐 語言設定", 
                                 font=("Arial", 12, "bold"), 
                                 bg="#f0f0f0", padx=10, pady=10)
        lang_frame.pack(pady=5, padx=10, fill="x")
        
        tk.Label(lang_frame, text="語言選擇:", 
                font=("Arial", 11), bg="#f0f0f0").pack(anchor="w")
        
        lang_container = tk.Frame(lang_frame, bg="#f0f0f0")
        lang_container.pack(anchor="w", pady=2)
        
        self.language = tk.StringVar(value="chinese")
        lang_combo = ttk.Combobox(lang_container, textvariable=self.language,
                                values=["chinese", "english", "auto"], 
                                width=20, state="readonly")
        lang_combo.pack(side="left")
        
        # 語言說明
        lang_info = tk.Label(lang_container, 
                           text="  (chinese=中文, english=英文, auto=自動檢測)", 
                           font=("Arial", 9), fg="gray", bg="#f0f0f0")
        lang_info.pack(side="left")
    
    def _create_segment_settings_frame(self):
        """音頻分割設定區域"""
        segment_frame = tk.LabelFrame(self.scrollable_frame, text="🎵 音頻分割設定", 
                                    font=("Arial", 12, "bold"),
                                    bg="#f0f0f0", padx=10, pady=10)
        segment_frame.pack(pady=5, padx=10, fill="x")

        tk.Label(segment_frame, text="分割時間長度:", 
                font=("Arial", 11), bg="#f0f0f0").pack(anchor="w")
        
        # 滑桿容器
        scale_frame = tk.Frame(segment_frame, bg="#f0f0f0")
        scale_frame.pack(fill="x", pady=5)
        
        self.segment_duration = tk.IntVar(value=10)
        segment_scale = tk.Scale(scale_frame, from_=3, to=30, orient="horizontal", 
                                variable=self.segment_duration, 
                                length=400, bg="#f0f0f0",
                                font=("Arial", 9))
        segment_scale.pack(side="left", fill="x", expand=True)

        # 顯示當前值的標籤
        self.segment_label = tk.Label(scale_frame, text="10 秒", 
                                    font=("Arial", 11, "bold"), 
                                    bg="#f0f0f0", fg="#0066cc",
                                    width=8)
        self.segment_label.pack(side="right", padx=(10, 0))
        
        # 說明文字
        info_label = tk.Label(segment_frame, 
                            text="較短的分割可提高精確度，但會增加處理時間", 
                            font=("Arial", 9), fg="gray", bg="#f0f0f0")
        info_label.pack(anchor="w", pady=(5, 0))
        
        # 更新顯示標籤
        def update_segment_label():
            self.segment_label.config(text=f"{self.segment_duration.get()} 秒")
            self.root.after(100, update_segment_label)
        update_segment_label()
    
    def _create_muting_settings_frame(self):
        """精確消音設定區域"""
        precise_frame = tk.LabelFrame(self.scrollable_frame, text="🔇 消音設定", 
                                    font=("Arial", 12, "bold"),
                                    bg="#f0f0f0", padx=10, pady=10)
        precise_frame.pack(pady=5, padx=10, fill="x")

        self.precise_muting = tk.BooleanVar(value=True)
        precise_check = tk.Checkbutton(precise_frame, text="啟用精確消音 (只消音髒話部分)", 
                                    variable=self.precise_muting, bg="#f0f0f0")
        precise_check.pack(anchor="w")

        tk.Label(precise_frame, text="髒話前後緩衝時間:", 
                font=("Arial", 11), bg="#f0f0f0").pack(anchor="w")
        
        # 緩衝時間滑桿
        padding_frame = tk.Frame(precise_frame, bg="#f0f0f0")
        padding_frame.pack(fill="x", pady=5)
        
        self.mute_padding = tk.DoubleVar(value=0.5)
        padding_scale = tk.Scale(padding_frame, from_=0.1, to=2.0, resolution=0.1,
                                orient="horizontal", variable=self.mute_padding, 
                                length=400, bg="#f0f0f0")
        padding_scale.pack(side="left", fill="x", expand=True)
        
        padding_label = tk.Label(padding_frame, text="0.5 秒", 
                               font=("Arial", 11, "bold"), 
                               bg="#f0f0f0", fg="#0066cc",
                               width=8)
        padding_label.pack(side="right", padx=(10, 0))
        
        def update_padding_label():
            padding_label.config(text=f"{self.mute_padding.get():.1f} 秒")
            self.root.after(100, update_padding_label)
        update_padding_label()
        
        self.use_ffmpeg = tk.BooleanVar(value=True)
        ffmpeg_check = tk.Checkbutton(precise_frame, text="使用 FFmpeg 處理 (推薦，速度更快)", 
                                    variable=self.use_ffmpeg, bg="#f0f0f0")
        ffmpeg_check.pack(anchor="w")
    
    def _create_recognition_settings_frame(self):
        """識別增強設定區域"""
        recognition_frame = tk.LabelFrame(self.scrollable_frame, text="🎤 語音識別增強", 
                                        font=("Arial", 12, "bold"),
                                        bg="#f0f0f0", padx=10, pady=10)
        recognition_frame.pack(pady=5, padx=10, fill="x")

        self.fuzzy_matching = tk.BooleanVar(value=True)
        fuzzy_check = tk.Checkbutton(recognition_frame, text="啟用模糊匹配 (處理重音、延遲)", 
                                    variable=self.fuzzy_matching, bg="#f0f0f0")
        fuzzy_check.pack(anchor="w")

        self.multi_recognition = tk.BooleanVar(value=False)
        multi_check = tk.Checkbutton(recognition_frame, text="啟用多重識別策略 (較慢但更準確)", 
                                    variable=self.multi_recognition, bg="#f0f0f0")
        multi_check.pack(anchor="w")

        self.overlap_segments = tk.BooleanVar(value=False)
        overlap_check = tk.Checkbutton(recognition_frame, text="使用重疊片段分析 (避免詞彙被切斷)", 
                                    variable=self.overlap_segments, bg="#f0f0f0")
        overlap_check.pack(anchor="w")
    
    def _create_custom_words_frame(self):
        """自定義詞彙區域"""
        custom_frame = tk.LabelFrame(self.scrollable_frame, text="📝 自定義過濾詞彙", 
                                   font=("Arial", 12, "bold"),
                                   bg="#f0f0f0", padx=10, pady=10)
        custom_frame.pack(pady=5, padx=10, fill="x")
        
        tk.Label(custom_frame, text="輸入要過濾的詞彙 (用逗號分隔):", 
                font=("Arial", 11), bg="#f0f0f0").pack(anchor="w")
        
        self.custom_words = tk.Text(custom_frame, height=3, font=("Arial", 10))
        self.custom_words.pack(fill="x", pady=5)
        
        # 預設詞彙說明
        info_label = tk.Label(custom_frame, 
                            text="預設已包含常見髒話詞庫，可額外添加自定義詞彙", 
                            font=("Arial", 9), fg="gray", bg="#f0f0f0")
        info_label.pack(anchor="w")
    
    def _create_process_controls(self):
        """處理按鈕和進度控制 - 固定在底部"""
        # 固定在main_frame底部
        button_container = tk.Frame(self.main_frame, bg="#f0f0f0")
        button_container.pack(side="bottom", fill="x", padx=20, pady=10)
        
        # 按鈕框架 - 置中
        button_frame = tk.Frame(button_container, bg="#f0f0f0")
        button_frame.pack(expand=False)  # 不展開，保持原始大小
        
        # 主處理按鈕
        self.process_btn = tk.Button(button_frame, 
                                   text="🚀 開始處理", 
                                   command=self.process_video, 
                                   bg="#4CAF50",
                                   fg="white",
                                   font=("Arial", 14, "bold"),
                                   relief="raised",
                                   borderwidth=2,
                                   cursor="hand2")
        self.process_btn.pack(ipadx=50, ipady=15)  # 使用內邊距控制大小
        
        # 按鈕懸浮效果
        def on_enter(event):
            if self.process_btn['state'] != 'disabled':
                self.process_btn.config(bg="#45a049", relief="raised")
        
        def on_leave(event):
            if self.process_btn['state'] != 'disabled':
                self.process_btn.config(bg="#4CAF50", relief="raised")
        
        def on_click(event):
            if self.process_btn['state'] != 'disabled':
                self.process_btn.config(relief="sunken")
        
        def on_release(event):
            if self.process_btn['state'] != 'disabled':
                self.process_btn.config(relief="raised")
        
        self.process_btn.bind("<Enter>", on_enter)
        self.process_btn.bind("<Leave>", on_leave)
        self.process_btn.bind("<Button-1>", on_click)
        self.process_btn.bind("<ButtonRelease-1>", on_release)
        
        # 進度顯示區域
        progress_container = tk.Frame(button_container, bg="#f0f0f0")
        progress_container.pack(fill="x", pady=(10, 0))
        
        # 進度文字
        self.progress_var = tk.StringVar(value="等待處理...")
        progress_label = tk.Label(progress_container, 
                                textvariable=self.progress_var, 
                                font=("Arial", 11),
                                fg="#666666", bg="#f0f0f0")
        progress_label.pack(pady=(0, 5))
        
        # 進度條
        self.progress_bar = ttk.Progressbar(progress_container, 
                                          mode='indeterminate',
                                          length=400)
        self.progress_bar.pack(expand=True, fill="x")
    
    def browse_file(self):
        """瀏覽並選擇檔案"""
        filename = filedialog.askopenfilename(
            title="選擇影片文件",
            filetypes=[
                ("影片文件", "*.mp4 *.avi *.mov *.mkv *.flv *.wmv"),
                ("MP4 文件", "*.mp4"),
                ("AVI 文件", "*.avi"),
                ("所有文件", "*.*")
            ]
        )
        if filename:
            self.file_path.set(filename)
    
    def apply_settings_to_filter(self):
        """將GUI設定應用到過濾器"""
        settings = {
            'chunk_duration': self.segment_duration.get(),
            'precise_muting': self.precise_muting.get(),
            'mute_padding': self.mute_padding.get(),
            'use_fuzzy_matching': self.fuzzy_matching.get(),
            'use_multi_recognition': self.multi_recognition.get(),
            'use_overlap_segments': self.overlap_segments.get(),
            'use_ffmpeg': self.use_ffmpeg.get()
        }
        
        self.filter.configure_settings(**settings)
    
    def process_video(self):
        """處理影片"""
        video_path = self.file_path.get()
        
        if not video_path:
            messagebox.showerror("錯誤", "請選擇影片文件！")
            return
        
        # 檢查檔案是否存在
        import os
        if not os.path.exists(video_path):
            messagebox.showerror("錯誤", "選擇的檔案不存在！")
            return
        
        # 禁用處理按鈕
        self.process_btn.config(state="disabled", text="處理中...", bg="#cccccc")
        
        # 添加自定義詞彙
        custom_text = self.custom_words.get("1.0", tk.END).strip()
        if custom_text:
            words = [w.strip() for w in custom_text.split(",") if w.strip()]
            self.filter.add_custom_profanity(words)
        
        # 在新線程中處理，避免界面凍結
        def process_thread():
            try:
                # 更新進度
                self.progress_var.set("正在配置設定...")
                self.progress_bar.start(10)  # 較慢的動畫速度
                self.root.update()
                
                # 應用設定
                self.apply_settings_to_filter()
                
                self.progress_var.set("正在處理影片，請耐心等候...")
                self.root.update()
                
                # 生成輸出檔案路徑
                output_path = video_path.rsplit('.', 1)[0] + '_cleaned.mp4'
                
                # 處理影片
                result = self.filter.process_video(video_path, output_path, 
                                                 self.language.get())
                
                # 停止進度條
                self.progress_bar.stop()
                
                # 恢復按鈕
                self.process_btn.config(state="normal", text="🚀 開始處理", bg="#4CAF50")
                
                if result:
                    self.progress_var.set("✅ 處理完成！")
                    messagebox.showinfo("處理成功", 
                                      f"影片處理完成！\n\n"
                                      f"📁 輸入檔案:\n{video_path}\n\n"
                                      f"📁 輸出檔案:\n{result}\n\n"
                                      f"🎉 您可以在輸出檔案位置找到處理後的影片")
                else:
                    self.progress_var.set("❌ 處理失敗！")
                    messagebox.showerror("處理失敗", 
                                      "處理失敗！\n\n可能的原因：\n"
                                      "• 影片格式不支援\n"
                                      "• 網路連接問題\n"
                                      "• FFmpeg未正確安裝\n"
                                      "• 磁碟空間不足")
                    
            except Exception as e:
                self.progress_bar.stop()
                self.process_btn.config(state="normal", text="🚀 開始處理", bg="#4CAF50")
                self.progress_var.set("❌ 處理失敗！")
                messagebox.showerror("錯誤", f"處理過程中發生錯誤:\n\n{str(e)}")
        
        # 啟動處理線程
        threading.Thread(target=process_thread, daemon=True).start()


def create_gui():
    """創建並啟動GUI應用"""
    root = tk.Tk()
    app = FilterGUI(root)
    root.mainloop()


if __name__ == "__main__":
    create_gui()