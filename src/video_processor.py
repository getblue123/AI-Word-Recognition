# video_processor.py - 主要影片處理器
import os
from typing import List, Dict
from audio_processor import AudioProcessor
from speech_recognition_engine import SpeechRecognitionEngine
from profanity_detector import ProfanityDetector
from video_muting_processor import VideoMutingProcessor


class VideoProfanityFilter:
    """影片髒話過濾器 - 主控制器"""
    
    def __init__(self):
        # 初始化各個模組
        self.audio_processor = AudioProcessor()
        self.speech_engine = SpeechRecognitionEngine()
        self.profanity_detector = ProfanityDetector()
        self.muting_processor = VideoMutingProcessor()
        
        # 配置參數
        self.chunk_duration = 10
        self.precise_muting = False
        self.mute_padding = 0.5
        self.use_fuzzy_matching = True
        self.use_multi_recognition = False
        self.use_overlap_segments = False
        self.use_ffmpeg = True
    
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
    
    def add_custom_profanity(self, words: List[str]):
        """添加自定義髒話詞庫"""
        self.profanity_detector.add_custom_profanity(words)
    
    def process_video_segments(self, video_path: str, audio_path: str, language: str = 'chinese') -> List[Dict]:
        """處理影片片段，返回需要消音的時間段"""
        print("開始語音辨識和髒話檢測...")
        
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
            
            if text:
                print(f"識別文字: {text}")
                
                # 檢測髒話
                profanity_found = self.profanity_detector.detect_profanity(
                    text, 
                    use_fuzzy=self.use_fuzzy_matching
                )
                
                if profanity_found:
                    print(f"發現髒話: {profanity_found}")
                    
                    if self.precise_muting:
                        # 精確定位每個髒話的時間
                        for word in profanity_found:
                            word_timings = self.audio_processor.find_word_timing_in_segment(
                                chunk_path, text, word, start_time
                            )
                            
                            for precise_start, precise_end in word_timings:
                                # 加上緩衝時間
                                buffered_start = precise_start - self.mute_padding
                                buffered_end = precise_end + self.mute_padding
                                
                                # 確保不超出原片段範圍
                                buffered_start = max(start_time, buffered_start)
                                buffered_end = min(end_time, buffered_end)
                                
                                print(f"      精確消音: {buffered_start:.1f}s - {buffered_end:.1f}s (詞彙: {word})")
                                
                                profanity_segments.append({
                                    'start_time': buffered_start,
                                    'end_time': buffered_end,
                                    'text': word,
                                    'profanity': [word],
                                    'duration': buffered_end - buffered_start
                                })
                    else:
                        # 整段消音
                        profanity_segments.append({
                            'start_time': start_time,
                            'end_time': end_time,
                            'text': text,
                            'profanity': profanity_found,
                            'duration': end_time - start_time
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
            
            # 2. 語音辨識和髒話檢測
            profanity_segments = self.process_video_segments(video_path, audio_path, language)
            
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
            self._display_results(profanity_segments)
            
            return result_path
            
        except Exception as e:
            print(f"處理影片時發生錯誤: {e}")
            return None
    
    def _display_results(self, profanity_segments: List[Dict]):
        """顯示處理結果"""
        if profanity_segments:
            print(f"\n處理完成！共檢測到 {len(profanity_segments)} 個不當用詞片段:")
            for i, segment in enumerate(profanity_segments, 1):
                duration = segment.get('duration', 0)
                print(f"  {i}. {segment['start_time']:.1f}s-{segment['end_time']:.1f}s: "
                      f"{segment['profanity']} (時長: {duration:.1f}s)")
        else:
            print("\n處理完成！沒有檢測到需要過濾的內容。")