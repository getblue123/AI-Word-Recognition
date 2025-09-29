# gui_interface.py - GUI介面模組（改進版）
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
from video_processor import VideoProfanityFilter
import os
import sys

# 確保能找到音質處理模組
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class FilterGUI:
    """GUI介面類"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("智能影片特殊詞語過濾器 v2.0")
        self.root.geometry("700x800")
        self.root.minsize(650, 700)
        
        # 使用增強版的處理器
        self.filter = VideoProfanityFilter()
        
        # 訓練相關變數
        self.training_segments = []
        self.current_training_index = 0
        self.training_annotations = []
        
        # 創建主框架
        self.main_frame = tk.Frame(root, bg="#f0f0f0")
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.create_widgets()
        self.root.bind('<Configure>', self.on_window_resize)
    
    def check_dependencies(self):
        """檢查必要的依賴和文件"""
        try:
            from audio_quality_processor import AudioQualityProcessor
            return True
        except ImportError as e:
            messagebox.showerror("依賴錯誤", f"缺少音質處理模組: {e}")
            return False
    
    def create_widgets(self):
        """創建GUI元件"""
        # 標題
        title_label = tk.Label(self.main_frame, text="智能影片特殊詞語過濾器 v2.0", 
                             font=("Arial", 18, "bold"), 
                             bg="#f0f0f0", fg="#333333")
        title_label.pack(pady=10)
        
        # 創建筆記本（分頁）
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill="both", expand=True)
        
        # 分頁1: 影片處理
        self.process_frame = tk.Frame(self.notebook, bg="#f0f0f0")
        self.notebook.add(self.process_frame, text="🎬 影片處理")
        
        # 分頁2: 模型訓練
        self.training_frame = tk.Frame(self.notebook, bg="#f0f0f0")
        self.notebook.add(self.training_frame, text="🤖 自適應訓練")
        
        # 分頁3: 系統設定
        self.settings_frame = tk.Frame(self.notebook, bg="#f0f0f0")
        self.notebook.add(self.settings_frame, text="⚙️ 系統設定")
        
        # 創建各分頁內容
        self.create_process_tab()
        self.create_training_tab()
        self.create_settings_tab()
    
    def create_process_tab(self):
        """創建影片處理分頁"""
        # 滾動區域
        canvas = tk.Canvas(self.process_frame, bg="#f0f0f0", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.process_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#f0f0f0")
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 檔案選擇
        file_frame = tk.LabelFrame(scrollable_frame, text="📁 檔案選擇", 
                                 font=("Arial", 12, "bold"), bg="#f0f0f0", padx=10, pady=10)
        file_frame.pack(fill="x", padx=10, pady=5)
        
        entry_frame = tk.Frame(file_frame, bg="#f0f0f0")
        entry_frame.pack(fill="x", pady=5)
        
        self.file_path = tk.StringVar()
        tk.Entry(entry_frame, textvariable=self.file_path, font=("Arial", 10)).pack(side="left", fill="x", expand=True)
        tk.Button(entry_frame, text="瀏覽", command=self.browse_video).pack(side="right", padx=(10,0))
        
        # 檢測設定
        detection_frame = tk.LabelFrame(scrollable_frame, text="🔍 檢測設定", 
                                      font=("Arial", 12, "bold"), bg="#f0f0f0", padx=10, pady=10)
        detection_frame.pack(fill="x", padx=10, pady=5)
        
        self.use_fuzzy = tk.BooleanVar(value=True)
        tk.Checkbutton(detection_frame, text="啟用模糊匹配", variable=self.use_fuzzy, bg="#f0f0f0").pack(anchor="w")
        
        self.use_adaptive = tk.BooleanVar(value=False)
        adaptive_check = tk.Checkbutton(detection_frame, text="啟用自適應檢測（需要訓練模型）", 
                                      variable=self.use_adaptive, bg="#f0f0f0")
        adaptive_check.pack(anchor="w")
        
        # 自適應模型狀態
        self.adaptive_status = tk.StringVar(value="未載入模型")
        tk.Label(detection_frame, textvariable=self.adaptive_status, 
                font=("Arial", 9), fg="gray", bg="#f0f0f0").pack(anchor="w", padx=20)
        
        # 模型管理按鈕
        model_frame = tk.Frame(detection_frame, bg="#f0f0f0")
        model_frame.pack(fill="x", pady=5)
        
        tk.Button(model_frame, text="載入模型", command=self.load_model, 
                 bg="#3498db", fg="white").pack(side="left", padx=2)
        tk.Button(model_frame, text="保存模型", command=self.save_model, 
                 bg="#2ecc71", fg="white").pack(side="left", padx=2)
        
        # 消音設定
        muting_frame = tk.LabelFrame(scrollable_frame, text="🔇 消音設定", 
                                   font=("Arial", 12, "bold"), bg="#f0f0f0", padx=10, pady=10)
        muting_frame.pack(fill="x", padx=10, pady=5)
        
        self.precise_muting = tk.BooleanVar(value=True)
        tk.Checkbutton(muting_frame, text="精確消音", variable=self.precise_muting, bg="#f0f0f0").pack(anchor="w")
        
        # 處理按鈕
        button_frame = tk.Frame(scrollable_frame, bg="#f0f0f0")
        button_frame.pack(fill="x", padx=10, pady=20)
        
        self.process_btn = tk.Button(button_frame, text="🚀 開始處理", 
                                   command=self.process_video, 
                                   bg="#4CAF50", fg="white", 
                                   font=("Arial", 14, "bold"))
        self.process_btn.pack(ipadx=30, ipady=10)
        
        # 進度顯示
        self.progress_var = tk.StringVar(value="等待處理...")
        tk.Label(scrollable_frame, textvariable=self.progress_var, 
                font=("Arial", 11), bg="#f0f0f0").pack(pady=10)
        
        self.progress_bar = ttk.Progressbar(scrollable_frame, mode='indeterminate')
        self.progress_bar.pack(fill="x", padx=10, pady=5)
    
    def create_training_tab(self):
        """創建訓練分頁"""
        # 訓練步驟指示
        steps_frame = tk.LabelFrame(self.training_frame, text="訓練步驟", 
                                  font=("Arial", 12, "bold"), bg="#f0f0f0")
        steps_frame.pack(fill="x", padx=10, pady=5)
        
        steps_text = ("1. 選擇包含特殊詞語的影片檔案\n"
                     "2. 系統自動分割並初步檢測\n"
                     "3. 手動標註音頻片段\n"
                     "4. 訓練自適應模型\n"
                     "5. 在影片處理中啟用自適應檢測")
        
        tk.Label(steps_frame, text=steps_text, justify="left", 
                font=("Arial", 10), bg="#f0f0f0").pack(padx=10, pady=5)
        
        # 步驟1: 選擇訓練影片
        step1_frame = tk.LabelFrame(self.training_frame, text="步驟1: 選擇訓練影片", 
                                  font=("Arial", 11, "bold"), bg="#f0f0f0")
        step1_frame.pack(fill="x", padx=10, pady=5)
        
        train_file_frame = tk.Frame(step1_frame, bg="#f0f0f0")
        train_file_frame.pack(fill="x", padx=10, pady=5)
        
        self.training_file_path = tk.StringVar()
        tk.Entry(train_file_frame, textvariable=self.training_file_path).pack(side="left", fill="x", expand=True)
        tk.Button(train_file_frame, text="選擇", command=self.browse_training_video).pack(side="right", padx=(10,0))
        
        tk.Button(step1_frame, text="創建訓練片段", command=self.create_training_segments).pack(pady=5)
        
        # 步驟2: 標註介面
        step2_frame = tk.LabelFrame(self.training_frame, text="步驟2: 標註片段", 
                                  font=("Arial", 11, "bold"), bg="#f0f0f0")
        step2_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 片段資訊
        self.segment_info = tk.StringVar(value="尚未載入片段")
        tk.Label(step2_frame, textvariable=self.segment_info, 
                font=("Arial", 11), bg="#f0f0f0").pack(pady=5)
        
        # 識別結果顯示
        tk.Label(step2_frame, text="語音識別:", font=("Arial", 10, "bold"), bg="#f0f0f0").pack(anchor="w", padx=10)
        self.recognition_display = tk.Text(step2_frame, height=3, width=50)
        self.recognition_display.pack(fill="x", padx=10, pady=2)
        
        # 標註按鈕
        annotation_frame = tk.Frame(step2_frame, bg="#f0f0f0")
        annotation_frame.pack(pady=10)
        
        tk.Button(annotation_frame, text="🤬 特殊詞語", command=lambda: self.annotate_segment('profanity'), 
                 bg="#e74c3c", fg="white", width=10).pack(side="left", padx=5)
        tk.Button(annotation_frame, text="😊 正常", command=lambda: self.annotate_segment('normal'), 
                 bg="#2ecc71", fg="white", width=10).pack(side="left", padx=5)
        tk.Button(annotation_frame, text="❓ 不確定", command=lambda: self.annotate_segment('uncertain'), 
                 bg="#f39c12", fg="white", width=10).pack(side="left", padx=5)
        tk.Button(annotation_frame, text="⏭️ 跳過", command=self.skip_annotation, 
                 bg="#95a5a6", fg="white", width=10).pack(side="left", padx=5)
        
        # 標註進度
        self.annotation_progress = tk.StringVar(value="進度: 0/0")
        tk.Label(step2_frame, textvariable=self.annotation_progress, bg="#f0f0f0").pack()
        
        self.annotation_progressbar = ttk.Progressbar(step2_frame, mode='determinate')
        self.annotation_progressbar.pack(fill="x", padx=10, pady=5)
        
        # 步驟3: 訓練模型
        step3_frame = tk.LabelFrame(self.training_frame, text="步驟3: 訓練模型", 
                                  font=("Arial", 11, "bold"), bg="#f0f0f0")
        step3_frame.pack(fill="x", padx=10, pady=5)
        
        train_options_frame = tk.Frame(step3_frame, bg="#f0f0f0")
        train_options_frame.pack(pady=5)
        
        tk.Label(train_options_frame, text="訓練模式:", bg="#f0f0f0").pack(side="left")
        
        self.training_mode = tk.StringVar(value="new")
        tk.Radiobutton(train_options_frame, text="全新訓練", 
                    variable=self.training_mode, value="new", bg="#f0f0f0").pack(side="left", padx=5)
        tk.Radiobutton(train_options_frame, text="增量訓練", 
                    variable=self.training_mode, value="incremental", bg="#f0f0f0").pack(side="left", padx=5)
        
        # 在現有的訓練狀態標籤後添加訓練歷史
        history_frame = tk.LabelFrame(step3_frame, text="訓練歷史", 
                                    font=("Arial", 10, "bold"), bg="#f0f0f0")
        history_frame.pack(fill="x", padx=10, pady=5)
        
        self.training_history = tk.Text(history_frame, height=4, width=50, font=("Arial", 9))
        self.training_history.pack(fill="x", padx=5, pady=5)

        train_buttons_frame = tk.Frame(step3_frame, bg="#f0f0f0")
        train_buttons_frame.pack(pady=10)

        tk.Button(train_buttons_frame, text="開始訓練", command=self.train_adaptive_model, 
                 bg="#9b59b6", fg="white", font=("Arial", 12, "bold")).pack(side="left", padx=5)
        
        self.training_status = tk.StringVar(value="尚未開始訓練")
        tk.Label(step3_frame, textvariable=self.training_status, bg="#f0f0f0").pack()
    
    def create_settings_tab(self):
        """創建設定分頁"""

        # 音質處理設定
        quality_frame = tk.LabelFrame(self.settings_frame, text="音質處理", 
                                    font=("Arial", 12, "bold"), bg="#f0f0f0")
        quality_frame.pack(fill="x", padx=10, pady=5)
        
        self.enable_quality_processing = tk.BooleanVar(value=False)
        tk.Checkbutton(quality_frame, text="啟用音質自動改善", 
                    variable=self.enable_quality_processing, bg="#f0f0f0").pack(anchor="w")
        
        # 音質分析按鈕
        tk.Button(quality_frame, text="分析當前影片音質", 
                command=self.analyze_video_quality).pack(pady=5)
        
        # 語音識別設定
        speech_frame = tk.LabelFrame(self.settings_frame, text="語音識別設定", 
                                   font=("Arial", 12, "bold"), bg="#f0f0f0")
        speech_frame.pack(fill="x", padx=10, pady=5)
        
        # 語音引擎選擇 (新增)
        engine_frame = tk.Frame(speech_frame, bg="#f0f0f0")
        engine_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(engine_frame, text="語音識別引擎:", bg="#f0f0f0").pack(anchor="w")

        self.prefer_whisper = tk.BooleanVar(value=True)
        whisper_check = tk.Checkbutton(engine_frame, text="優先使用 Whisper (離線，準確率更高)", 
                                    variable=self.prefer_whisper, bg="#f0f0f0",
                                    command=self.on_whisper_toggle)
        whisper_check.pack(anchor="w", padx=20)

        # Whisper 模型大小選擇
        model_frame = tk.Frame(speech_frame, bg="#f0f0f0")
        model_frame.pack(fill="x", padx=10, pady=2)

        tk.Label(model_frame, text="Whisper 模型大小:", bg="#f0f0f0").pack(anchor="w", padx=20)
        self.whisper_model_size = tk.StringVar(value="base")
        model_combo = ttk.Combobox(model_frame, textvariable=self.whisper_model_size,
                                values=["tiny (快速)", "base (推薦)", "small (平衡)", "medium (準確)", "large (最準確)"],
                                state="readonly", width=20)
        model_combo.pack(anchor="w", padx=40, pady=2)

        # Whisper 狀態顯示
        self.whisper_status = tk.StringVar(value="未載入")
        whisper_status_label = tk.Label(speech_frame, textvariable=self.whisper_status, 
                                    font=("Arial", 9), fg="gray", bg="#f0f0f0")
        whisper_status_label.pack(anchor="w", padx=40)

        # 分隔線
        tk.Frame(speech_frame, height=1, bg="gray").pack(fill="x", padx=10, pady=5)


        tk.Label(speech_frame, text="語言:", bg="#f0f0f0").pack(anchor="w", padx=10)
        self.language = tk.StringVar(value="chinese")
        ttk.Combobox(speech_frame, textvariable=self.language, 
                    values=["chinese", "english", "auto"], state="readonly").pack(anchor="w", padx=10)
        
        self.multi_recognition = tk.BooleanVar(value=False)
        tk.Checkbutton(speech_frame, text="多重識別策略", 
                      variable=self.multi_recognition, bg="#f0f0f0").pack(anchor="w", padx=10)
        
        # 音頻處理設定
        audio_frame = tk.LabelFrame(self.settings_frame, text="音頻處理設定", 
                                  font=("Arial", 12, "bold"), bg="#f0f0f0")
        audio_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(audio_frame, text="分割時間長度 (秒):", bg="#f0f0f0").pack(anchor="w", padx=10)
        self.chunk_duration = tk.IntVar(value=10)
        tk.Scale(audio_frame, from_=3, to=30, orient="horizontal", 
                variable=self.chunk_duration, bg="#f0f0f0").pack(fill="x", padx=10)
        
        self.overlap_segments = tk.BooleanVar(value=False)
        tk.Checkbutton(audio_frame, text="重疊片段分析", 
                      variable=self.overlap_segments, bg="#f0f0f0").pack(anchor="w", padx=10)
        
        # 系統狀態
        status_frame = tk.LabelFrame(self.settings_frame, text="系統狀態", 
                                   font=("Arial", 12, "bold"), bg="#f0f0f0")
        status_frame.pack(fill="x", padx=10, pady=5)
        
        self.system_status = tk.Text(status_frame, height=8, width=50)
        self.system_status.pack(fill="both", expand=True, padx=10, pady=5)
        
        tk.Button(status_frame, text="刷新狀態", command=self.update_system_status).pack(pady=5)
        
        # 初始化顯示狀態
        self.update_system_status()
    
    def on_window_resize(self, event):
        """處理視窗大小改變"""
        if event.widget == self.root:
            pass  # 可以在這裡添加響應式調整
    
    def browse_video(self):
        """選擇要處理的影片"""
        filename = filedialog.askopenfilename(
            title="選擇影片檔案",
            filetypes=[("影片檔案", "*.mp4 *.avi *.mov *.mkv")]
        )
        if filename:
            self.file_path.set(filename)
    
    def browse_training_video(self):
        """選擇訓練影片"""
        filename = filedialog.askopenfilename(
            title="選擇訓練影片",
            filetypes=[("影片檔案", "*.mp4 *.avi *.mov *.mkv")]
        )
        if filename:
            self.training_file_path.set(filename)
    
    def apply_settings(self):
        """應用設定到處理器"""
        settings = {
            'chunk_duration': self.chunk_duration.get(),
            'precise_muting': self.precise_muting.get(),
            'use_fuzzy_matching': self.use_fuzzy.get(),
            'use_multi_recognition': self.multi_recognition.get(),
            'use_overlap_segments': self.overlap_segments.get(),
            'enable_adaptive_detection': self.use_adaptive.get(),
            # 新增 Whisper 設定
            'prefer_whisper': self.prefer_whisper.get(),
            'whisper_model_size': self.whisper_model_size.get().split()[0]
        }
        self.filter.configure_settings(**settings)
    
    def process_video(self):
        """處理影片"""
        video_path = self.file_path.get()
        if not video_path or not os.path.exists(video_path):
            messagebox.showerror("錯誤", "請選擇有效的影片檔案")
            return
        
        self.process_btn.config(state="disabled", text="處理中...")
        
        def process_thread():
            try:
                self.progress_var.set("正在配置設定...")
                self.progress_bar.start()
                self.root.update()
                
                self.apply_settings()
                
                self.progress_var.set("正在處理影片...")
                output_path = video_path.rsplit('.', 1)[0] + '_cleaned.mp4'
                
                result = self.filter.process_video(video_path, output_path, self.language.get())
                
                self.progress_bar.stop()
                self.process_btn.config(state="normal", text="🚀 開始處理")
                
                if result:
                    self.progress_var.set("✅ 處理完成！")
                    messagebox.showinfo("成功", f"處理完成！\n輸出檔案: {result}")
                else:
                    self.progress_var.set("❌ 處理失敗！")
                    messagebox.showerror("錯誤", "處理失敗")
                    
            except Exception as e:
                self.progress_bar.stop()
                self.process_btn.config(state="normal", text="🚀 開始處理")
                messagebox.showerror("錯誤", f"處理失敗: {str(e)}")
        
        threading.Thread(target=process_thread, daemon=True).start()
    
    def create_training_segments(self):
        """創建訓練片段"""
        video_path = self.training_file_path.get()
        if not video_path or not os.path.exists(video_path):
            messagebox.showerror("錯誤", "請選擇有效的訓練影片")
            return
        
        def create_thread():
            try:
                self.training_status.set("正在創建訓練片段...")
                self.root.update()
                
                self.training_segments = self.filter.create_training_segments_from_video(video_path, 4)
                
                if self.training_segments:
                    self.current_training_index = 0
                    self.annotation_progressbar['maximum'] = len(self.training_segments)
                    self.update_training_display()
                    
                    messagebox.showinfo("成功", f"已創建 {len(self.training_segments)} 個訓練片段")
                else:
                    messagebox.showerror("錯誤", "創建訓練片段失敗")
                    
            except Exception as e:
                messagebox.showerror("錯誤", f"創建失敗: {str(e)}")
        
        threading.Thread(target=create_thread, daemon=True).start()
    
    def update_training_display(self):
        """更新訓練顯示"""
        if not self.training_segments or self.current_training_index >= len(self.training_segments):
            self.segment_info.set("所有片段標註完成")
            return
        
        segment = self.training_segments[self.current_training_index]
        
        self.segment_info.set(f"片段 {self.current_training_index + 1}/{len(self.training_segments)} "
                             f"({segment['start_time']:.1f}s - {segment['end_time']:.1f}s)")
        
        self.recognition_display.delete(1.0, tk.END)
        self.recognition_display.insert(tk.END, f"識別: {segment['text']}\n")
        self.recognition_display.insert(tk.END, f"建議: {segment['suggested_label']}")
        
        self.annotation_progress.set(f"進度: {len(self.training_annotations)}/{len(self.training_segments)}")
        self.annotation_progressbar['value'] = len(self.training_annotations)
    
    def annotate_segment(self, label):
        """標註片段"""
        if not self.training_segments or self.current_training_index >= len(self.training_segments):
            return
        
        segment = self.training_segments[self.current_training_index].copy()
        segment['label'] = label
        
        self.training_annotations.append(segment)
        self.current_training_index += 1
        
        if self.current_training_index >= len(self.training_segments):
            messagebox.showinfo("完成", f"標註完成！共標註 {len(self.training_annotations)} 個片段")
        else:
            self.update_training_display()
    
    def skip_annotation(self):
        """跳過標註"""
        self.current_training_index += 1
        if self.current_training_index >= len(self.training_segments):
            messagebox.showinfo("完成", "所有片段處理完畢")
        else:
            self.update_training_display()
    
    def train_adaptive_model(self):
        # 將現有方法的內容替換為支持多種訓練模式的版本
        if not self.training_annotations:
            messagebox.showerror("錯誤", "請先標註一些片段")
            return
        
        training_type = getattr(self, 'training_mode', tk.StringVar(value="new")).get()
        
        def train_thread():
            try:
                if training_type == "incremental":
                    self.training_status.set("正在進行增量訓練...")
                    result = self.filter.incremental_train_model(self.training_annotations)
                else:  # new training
                    self.training_status.set("正在進行全新訓練...")
                    result = self.filter.train_adaptive_model(self.training_annotations)
                
                # 記錄訓練歷史
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                training_type_text = "增量訓練" if training_type == "incremental" else "全新訓練"
                history_entry = f"[{timestamp}] {training_type_text} - 準確率: {result.get('accuracy', 0):.3f} - 樣本數: {result.get('sample_count', 0)}\n"
                
                # 更新UI需要在主線程中執行
                def update_history():
                    if hasattr(self, 'training_history'):
                        self.training_history.insert(tk.END, history_entry)
                        self.training_history.see(tk.END)
                
                self.root.after(0, update_history)
                
                # 其餘原有代碼...
                
            except Exception as e:
                self.training_status.set(f"訓練失敗: {str(e)}")
        
        threading.Thread(target=train_thread, daemon=True).start()

    
    def update_adaptive_status(self):
        """更新自適應檢測狀態"""
        status = self.filter.profanity_detector.get_detection_status()
        if status['adaptive_trained']:
            self.adaptive_status.set(f"模型已訓練，準確率: {status['adaptive_accuracy']:.3f}")
        else:
            self.adaptive_status.set("未載入模型")
    
    def load_model(self):
        """載入模型"""
        filename = filedialog.askopenfilename(
            title="載入模型",
            filetypes=[("模型檔案", "*.pkl")]
        )
        if filename and os.path.exists(filename):
            if self.filter.load_adaptive_model(filename):
                self.update_adaptive_status()
                messagebox.showinfo("成功", "模型載入成功")
            else:
                messagebox.showerror("錯誤", "模型載入失敗")
    
    def save_model(self):
        """保存模型"""
        filename = filedialog.asksaveasfilename(
            title="保存模型",
            defaultextension=".pkl",
            filetypes=[("模型檔案", "*.pkl")]
        )
        if filename:
            try:
                self.filter.save_adaptive_model(filename)
                messagebox.showinfo("成功", f"模型已保存: {filename}")
            except Exception as e:
                messagebox.showerror("錯誤", f"保存失敗: {str(e)}")
    
    def update_system_status(self):
        """更新系統狀態"""
        status = self.filter.profanity_detector.get_detection_status()
        
        status_text = f"""=== 特殊詞語檢測系統狀態 ===
基本檢測: {'啟用' if status['basic_detection'] else '停用'}
模糊匹配: {'啟用' if status['fuzzy_detection'] else '停用'}
自適應檢測: {'啟用' if status['adaptive_detection'] else '停用'}
模型已訓練: {'是' if status['adaptive_trained'] else '否'}
模型準確率: {status['adaptive_accuracy']:.3f}
詞庫大小: {status['profanity_words_count']} 個詞彙

=== 系統設定 ===
音頻分割長度: {self.chunk_duration.get()} 秒
語言設定: {self.language.get()}
多重識別: {'啟用' if self.multi_recognition.get() else '停用'}
重疊分析: {'啟用' if self.overlap_segments.get() else '停用'}

=== 訓練狀態 ===
已標註片段: {len(self.training_annotations)}
訓練片段總數: {len(self.training_segments)}"""
        
        self.system_status.delete(1.0, tk.END)
        self.system_status.insert(tk.END, status_text)

    def analyze_video_quality(self):
        """分析影片音質"""
        video_path = self.file_path.get()
        if not video_path or not os.path.exists(video_path):
            messagebox.showwarning("警告", "請先選擇影片檔案")
            return
        
        def analysis_thread():
            try:
                self.root.after(0, lambda: self.progress_var.set("正在分析音質..."))
                
                # 先檢查是否能載入音質處理器
                try:
                    from audio_quality_processor import AudioQualityProcessor
                    processor = AudioQualityProcessor()
                except ImportError:
                    self.root.after(0, lambda: messagebox.showerror("錯誤", "音質處理模組未找到"))
                    return
                
                # 提取音頻進行分析
                print(f"開始提取音頻: {video_path}")
                audio_path = self.filter.audio_processor.extract_audio_from_video(video_path)
                
                if not audio_path or not os.path.exists(audio_path):
                    self.root.after(0, lambda: messagebox.showerror("錯誤", "音頻提取失敗"))
                    return
                
                print(f"音頻已提取到: {audio_path}")
                
                # 分析音質
                quality_report = processor.analyze_audio_quality(audio_path)
                
                # 清理臨時音頻文件
                try:
                    if os.path.exists(audio_path):
                        os.remove(audio_path)
                        print(f"已清理臨時文件: {audio_path}")
                except Exception as cleanup_error:
                    print(f"清理文件失敗: {cleanup_error}")
                
                # 在主線程中顯示結果
                def show_results():
                    self.progress_var.set("分析完成")
                    
                    if 'error' in quality_report:
                        messagebox.showerror("錯誤", quality_report['error'])
                    else:
                        # 格式化報告
                        report_text = f"""音質分析報告：

    基本信息：
    - 檔案：{os.path.basename(video_path)}
    - 時長：{quality_report.get('duration_ms', 0)/1000:.1f} 秒
    - 聲道：{quality_report.get('channels', '未知')}
    - 採樣率：{quality_report.get('frame_rate', '未知')} Hz
    - 音量級別：{quality_report.get('dBFS', 0):.1f} dB

    檢測到的問題："""
                        
                        issues = quality_report.get('issues', [])
                        if issues:
                            for issue in issues:
                                report_text += f"\n• {issue}"
                            report_text += f"\n\n建議：啟用音質處理來改善這些問題"
                        else:
                            report_text += "\n• 未檢測到明顯問題"
                            report_text += f"\n\n建議：音質良好，可選擇性使用音質處理"
                        
                        messagebox.showinfo("音質分析結果", report_text)
                
                self.root.after(0, show_results)
                
            except Exception as e:
                error_msg = f"分析失敗: {str(e)}"
                print(f"詳細錯誤: {e}")
                self.root.after(0, lambda: messagebox.showerror("錯誤", error_msg))
                self.root.after(0, lambda: self.progress_var.set("分析失敗"))
        
        threading.Thread(target=analysis_thread, daemon=True).start()

    def on_whisper_toggle(self):
        """處理 Whisper 開關"""
        if self.prefer_whisper.get():
            # 初始化 Whisper
            self.whisper_status.set("正在載入...")
            self.root.update()
            
            def load_whisper():
                success = self.filter.speech_engine.load_whisper_model(
                    self.whisper_model_size.get().split()[0]  # 取出模型名稱
                )
                
                def update_status():
                    if success:
                        self.whisper_status.set("已載入，可用")
                    else:
                        self.whisper_status.set("載入失敗")
                        self.prefer_whisper.set(False)
                
                self.root.after(0, update_status)
            
            threading.Thread(target=load_whisper, daemon=True).start()
        else:
            self.whisper_status.set("未載入")

def create_gui():
    """創建並啟動GUI應用"""
    root = tk.Tk()
    app = FilterGUI(root)
    root.mainloop()


if __name__ == "__main__":
    create_gui()