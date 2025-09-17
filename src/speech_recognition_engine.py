# speech_recognition_engine.py - 語音辨識模組
import os
import speech_recognition as sr
from pydub import AudioSegment
from typing import List, Tuple


class SpeechRecognitionEngine:
    """語音辨識引擎"""
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        
        # 語音辨識設定
        self.language_codes = {
            'chinese': 'zh-TW',
            'english': 'en-US',
            'auto': None  # 自動檢測
        }
    
    def enhance_audio_for_recognition(self, audio_path: str) -> str:
        """增強音頻以提高識別率"""
        try:
            audio = AudioSegment.from_wav(audio_path)
            
            # 1. 音量正規化
            target_dBFS = -20
            change_in_dBFS = target_dBFS - audio.dBFS
            if change_in_dBFS < 30:  # 避免過度放大
                audio = audio.apply_gain(change_in_dBFS)
            
            # 2. 降噪處理
            # 移除過低和過高頻率
            audio = audio.high_pass_filter(300).low_pass_filter(3400)
            
            # 3. 壓縮動態範圍
            audio = audio.compress_dynamic_range()
            
            # 4. 保存增強後的音頻
            enhanced_path = audio_path.replace('.wav', '_enhanced.wav')
            audio.export(enhanced_path, format="wav")
            
            return enhanced_path
        except Exception as e:
            print(f"音頻增強失敗: {e}")
            return audio_path
    
    def speech_to_text_basic(self, audio_path: str, language: str = 'zh-TW') -> str:
        """基本語音轉文字"""
        try:
            with sr.AudioFile(audio_path) as source:
                # 調整環境噪音
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio_data = self.recognizer.record(source)
            
            # 選擇語言
            lang_code = self.language_codes.get(language, 'zh-TW')
            
            # 使用 Google 語音辨識
            text = self.recognizer.recognize_google(audio_data, language=lang_code)
            return text.lower()
            
        except sr.UnknownValueError:
            # 無法識別語音
            return ""
        except sr.RequestError as e:
            print(f"語音辨識服務錯誤: {e}")
            return ""
        except Exception as e:
            print(f"語音辨識失敗: {e}")
            return ""
    
    def speech_to_text_adjusted(self, audio_path: str, language: str = 'zh-TW') -> str:
        """調整參數的語音識別"""
        try:
            with sr.AudioFile(audio_path) as source:
                # 更長的環境噪音適應時間
                self.recognizer.adjust_for_ambient_noise(source, duration=1.0)
                
                # 調整能量閾值
                self.recognizer.energy_threshold = 300
                self.recognizer.dynamic_energy_threshold = True
                
                audio_data = self.recognizer.record(source)
            
            # 嘗試不同的語音識別引擎設定
            text = self.recognizer.recognize_google(
                audio_data, 
                language=language,
                show_all=False  # 只要最佳結果
            )
            return text.lower()
            
        except Exception as e:
            return ""
    
    def multi_recognition_strategy(self, audio_path: str, language: str = 'zh-TW') -> str:
        """多重語音識別策略"""
        results = []
        
        try:
            # 策略1: 原始音頻識別
            original_text = self.speech_to_text_basic(audio_path, language)
            if original_text:
                results.append(original_text)
            
            # 策略2: 增強音頻識別
            enhanced_path = self.enhance_audio_for_recognition(audio_path)
            enhanced_text = self.speech_to_text_basic(enhanced_path, language)
            if enhanced_text:
                results.append(enhanced_text)
            
            # 策略3: 調整語音識別參數
            adjusted_text = self.speech_to_text_adjusted(audio_path, language)
            if adjusted_text:
                results.append(adjusted_text)
            
            # 清理臨時文件
            try:
                if enhanced_path != audio_path:
                    os.remove(enhanced_path)
            except:
                pass
            
            # 合併所有結果
            combined_text = " ".join(results)
            print(f"      多重識別結果: {results}")
            
            return combined_text
        
        except Exception as e:
            print(f"多重識別失敗: {e}")
            return ""
    
    def speech_to_text(self, audio_chunk_path: str, language: str = 'chinese', 
                      use_multi_strategy: bool = False) -> str:
        """語音轉文字 - 統一接口"""
        # 選擇語言代碼
        lang_code = self.language_codes.get(language, 'zh-TW')
        
        if use_multi_strategy:
            return self.multi_recognition_strategy(audio_chunk_path, lang_code)
        else:
            return self.speech_to_text_basic(audio_chunk_path, lang_code)