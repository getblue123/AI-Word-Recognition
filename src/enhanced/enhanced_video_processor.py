# enhanced_video_processor.py - 整合自適應訓練的影片處理器
import os
from typing import List, Dict
from audio_processor import AudioProcessor
from speech_recognition_engine import SpeechRecognitionEngine
from enhanced_profanity_detector import EnhancedProfanityDetector
from video_muting_processor import VideoMutingProcessor

class EnhancedVideoProfanityFilter:
    """整合自適應訓練的影片特殊詞語過濾器"""
    
    def __init__(self):
        # 初始化各個模組
        self.audio_processor = AudioProcessor()
        self.speech_engine = SpeechRecognitionEngine()
        self.profanity_detector = EnhancedProfanityDetector()  # 使用增強版
        self.muting_processor = VideoMutingProcessor()
        
        # 配置參數
        self.chunk_duration = 10
        self.precise_muting = False
        self.mute_padding = 0.5
        self.use_fuzzy_matching = True
        self.use_multi_recognition = False
        self.use_overlap_segments = False
        self.use_ffmpeg = True
        
        # 新增：訓練相關參數
        self.training_mode = False
        self.training_annotations = []
    
    def configure_settings(self, **kwargs):
        """配置系統設定"""
        if 'chunk_duration' in kwargs:
            self.chunk_duration = kwargs['chunk_duration']
            self.audio_processor.chunk_duration = kwargs['chunk_duration']
        
        if 'precise_muting' in kwargs:
            self.precise_muting = kwargs['precise_muting']
        
        if 'mute_padding' in kwargs:
            self.mute_padding = kwargs['mute_padding']
        
        if 'use_fuzzy_matching' in kwargs:
            self.use_fuzzy_matching = kwargs['use_fuzzy_matching']
        
        if 'use_multi_recognition' in kwargs:
            self.use_multi_recognition = kwargs['use_multi_recognition']
        
        if 'use_overlap_segments' in kwargs:
            self.use_overlap_segments = kwargs['use_overlap_segments']
        
        if 'use_ffmpeg' in kwargs:
            self.use_ffmpeg = kwargs['use_ffmpeg']
            
        # 新增：自適應檢測相關設定
        if 'enable_adaptive_detection' in kwargs:
            if kwargs['enable_adaptive_detection']:
                model_path = kwargs.get('adaptive_model_path', 'adaptive_model.pkl')
                self.profanity_detector.enable_adaptive_detection(model_path)
            else:
                self.profanity_detector.disable_adaptive_detection()
    
    def add_custom_profanity(self, words: List[str]):
        """添加自定義特殊詞語詞庫"""
        self.profanity_detector.add_custom_profanity(words)
    
    def process_video_segments_enhanced(self, video_path: str, audio_path: str, language: str = 'chinese') -> List[Dict]:
        """增強的影片片段處理"""
        print("開始語音辨識和特殊詞語檢測...")
        
        # 選擇分割策略
        if self.use_overlap_segments:
            chunks = self.audio_processor.split_audio_with_overlap(audio_path)
        else:
            chunks = self.audio_processor.split_audio_chunks(audio_path, self.chunk_duration)
        
        profanity_segments = []
        
        for i, (chunk_path, start_time, end_time) in enumerate(chunks):
            print(f"處理片段 {i+1}/{len(chunks)}: {start_time:.1f}s - {end_time:.1f}s")
            
            # 語音轉文字
            text = self.speech_engine.speech_to_text(
                chunk_path, 
                language, 
                use_multi_strategy=self.use_multi_recognition
            )
            
            print(f"識別文字: {text}")
            
            # 增強的特殊詞語檢測（整合文字和音頻）
            detection_result = self.profanity_detector.detect_profanity(
                text=text,
                audio_segment_path=chunk_path,
                use_fuzzy=self.use_fuzzy_matching
            )
            
            if detection_result['found_profanity']:
                print(f"檢測結果: {detection_result}")
                
                # 如果是訓練模式，記錄數據供後續標註
                if self.training_mode:
                    self.training_annotations.append({
                        'segment_path': chunk_path,
                        'start_time': start_time,
                        'end_time': end_time,
                        'text': text,
                        'detection_result': detection_result,
                        'auto_label': 'profanity' if detection_result['confidence'] > 0.7 else 'uncertain'
                    })
                
                if self.precise_muting:
                    # 精確定位每個特殊詞語的時間
                    for word in detection_result['found_profanity']:
                        if word != '訓練模型檢測':  # 跳過自適應檢測的標記
                            word_timings = self.audio_processor.find_word_timing_in_segment(
                                chunk_path, text, word, start_time
                            )
                            
                            for precise_start, precise_end in word_timings:
                                buffered_start = precise_start - self.mute_padding
                                buffered_end = precise_end + self.mute_padding
                                
                                buffered_start = max(start_time, buffered_start)
                                buffered_end = min(end_time, buffered_end)
                                
                                profanity_segments.append({
                                    'start_time': buffered_start,
                                    'end_time': buffered_end,
                                    'text': word,
                                    'profanity': [word],
                                    'duration': buffered_end - buffered_start,
                                    'confidence': detection_result['confidence'],
                                    'methods': detection_result['methods_used']
                                })
                else:
                    # 整段消音
                    profanity_segments.append({
                        'start_time': start_time,
                        'end_time': end_time,
                        'text': text,
                        'profanity': detection_result['found_profanity'],
                        'duration': end_time - start_time,
                        'confidence': detection_result['confidence'],
                        'methods': detection_result['methods_used']
                    })
            
            # 清理臨時文件
            try:
                os.remove(chunk_path)
            except:
                pass
        
        return profanity_segments
    
    def process_video(self, video_path: str, output_path: str = None, language: str = 'chinese') -> str:
        """完整的影片處理流程"""
        print(f"開始處理影片: {video_path}")
        
        try:
            # 1. 提取音頻
            audio_path = self.audio_processor.extract_audio_from_video(video_path)
            if not audio_path:
                return None
            
            # 2. 增強的語音辨識和特殊詞語檢測
            profanity_segments = self.process_video_segments_enhanced(video_path, audio_path, language)
            
            # 3. 創建消音影片
            result_path = self.muting_processor.create_muted_video(
                video_path, 
                profanity_segments, 
                output_path, 
                use_ffmpeg=self.use_ffmpeg
            )
            
            # 4. 清理臨時文件
            try:
                os.remove(audio_path)
            except:
                pass
            
            self.audio_processor.cleanup_temp_files()
            
            # 5. 顯示處理結果
            self._display_enhanced_results(profanity_segments)
            
            return result_path
            
        except Exception as e:
            print(f"處理影片時發生錯誤: {e}")
            return None
    
    def _display_enhanced_results(self, profanity_segments: List[Dict]):
        """顯示增強的處理結果"""
        if profanity_segments:
            print(f"\n處理完成！共檢測到 {len(profanity_segments)} 個不當用詞片段:")
            
            # 統計檢測方法
            method_stats = {}
            for segment in profanity_segments:
                for method in segment.get('methods', []):
                    method_stats[method] = method_stats.get(method, 0) + 1
            
            print(f"檢測方法統計: {method_stats}")
            
            for i, segment in enumerate(profanity_segments, 1):
                duration = segment.get('duration', 0)
                confidence = segment.get('confidence', 0)
                methods = segment.get('methods', [])
                
                print(f"  {i}. {segment['start_time']:.1f}s-{segment['end_time']:.1f}s: "
                      f"{segment['profanity']} (時長: {duration:.1f}s, "
                      f"信心度: {confidence:.2f}, 方法: {methods})")
        else:
            print("\n處理完成！沒有檢測到需要過濾的內容。")
        
        # 顯示檢測系統狀態
        status = self.profanity_detector.get_detection_status()
        print(f"\n檢測系統狀態:")
        print(f"  基本檢測: {'啟用' if status['basic_detection'] else '停用'}")
        print(f"  模糊匹配: {'啟用' if status['fuzzy_detection'] else '停用'}")
        print(f"  自適應檢測: {'啟用' if status['adaptive_detection'] else '停用'}")
        if status['adaptive_detection']:
            print(f"  模型準確率: {status['adaptive_accuracy']:.3f}")
    
    # === 新增：訓練相關功能 ===
    
    def enable_training_mode(self):
        """啟用訓練模式"""
        self.training_mode = True
        self.training_annotations = []
        print("訓練模式已啟用")
    
    def disable_training_mode(self):
        """停用訓練模式"""
        self.training_mode = False
        print("訓練模式已停用")
    
    def get_training_annotations(self) -> List[Dict]:
        """獲取訓練標註數據"""
        return self.training_annotations.copy()
    
    def train_adaptive_model(self, annotations: List[Dict] = None) -> Dict:
        """訓練自適應模型"""
        if annotations is None:
            annotations = self.training_annotations
        
        if not annotations:
            return {'error': '沒有訓練數據'}
        
        return self.profanity_detector.train_adaptive_model(annotations)
    
    def save_adaptive_model(self, model_path: str):
        """保存自適應模型"""
        self.profanity_detector.save_adaptive_model(model_path)
    
    def load_adaptive_model(self, model_path: str) -> bool:
        """載入自適應模型"""
        return self.profanity_detector.enable_adaptive_detection(model_path)
    
    def create_training_segments_from_video(self, video_path: str, segment_duration: int = 4) -> List[Dict]:
        """從影片創建訓練片段"""
        try:
            # 提取音頻
            audio_path = self.audio_processor.extract_audio_from_video(video_path)
            if not audio_path:
                return []
            
            # 創建短片段用於標註
            original_duration = self.audio_processor.chunk_duration
            self.audio_processor.chunk_duration = segment_duration
            
            chunks = self.audio_processor.split_audio_chunks(audio_path, segment_duration)
            
            training_segments = []
            for i, (chunk_path, start_time, end_time) in enumerate(chunks):
                # 執行初步語音識別
                text = self.speech_engine.speech_to_text(chunk_path)
                
                # 執行初步檢測
                detection_result = self.profanity_detector.detect_profanity(
                    text=text, 
                    use_fuzzy=True
                )
                
                training_segments.append({
                    'segment_id': i,
                    'segment_path': chunk_path,
                    'start_time': start_time,
                    'end_time': end_time,
                    'text': text,
                    'initial_detection': detection_result,
                    'suggested_label': 'profanity' if detection_result['found_profanity'] else 'normal',
                    'label': None  # 待用戶標註
                })
            
            # 恢復原設定
            self.audio_processor.chunk_duration = original_duration
            
            # 清理音頻文件
            try:
                os.remove(audio_path)
            except:
                pass
            
            print(f"已創建 {len(training_segments)} 個訓練片段")
            return training_segments
            
        except Exception as e:
            print(f"創建訓練片段失敗: {e}")
            return []