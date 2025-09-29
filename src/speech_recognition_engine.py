# speech_recognition_engine.py - 語音辨識模組
import os
import speech_recognition as sr
from pydub import AudioSegment
from typing import List, Tuple
from pydub.silence import detect_nonsilent

# Whisper 
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("Whisper 未安裝，使用 'pip install openai-whisper' 安裝")



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

        # Whisper 相關設定
        self.whisper_model = None
        self.use_whisper = False
        
        if WHISPER_AVAILABLE:
            self.available_engines = ['google', 'whisper']
        else:
            self.available_engines = ['google']

    
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
    
    def multi_engine_recognition(self, audio_path: str) -> str:
        """使用多個語音引擎識別"""
        results = []
        
        # 引擎1: Google (多語言嘗試)
        languages = ['zh-TW', 'zh-CN', 'zh', 'en-US']
        for lang in languages:
            try:
                with sr.AudioFile(audio_path) as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    audio_data = self.recognizer.record(source)
                
                text = self.recognizer.recognize_google(audio_data, language=lang)
                if text and len(text) > 2:
                    results.append(f"[Google-{lang}] {text}")
                    print(f"      Google-{lang}: {text}")
            except:
                continue
        
        # 引擎2: Sphinx (離線，對中文支援較差但可以嘗試)
        try:
            with sr.AudioFile(audio_path) as source:
                audio_data = self.recognizer.record(source)
            text = self.recognizer.recognize_sphinx(audio_data)
            if text:
                results.append(f"[Sphinx] {text}")
                print(f"      Sphinx: {text}")
        except:
            pass
        
        # 引擎3: Google的詳細結果
        try:
            with sr.AudioFile(audio_path) as source:
                audio_data = self.recognizer.record(source)
            
            # 獲取詳細結果
            response = self.recognizer.recognize_google(
                audio_data, 
                language='zh-TW', 
                show_all=True
            )
            
            if response and 'alternative' in response:
                for alt in response['alternative'][:3]:  # 取前3個結果
                    if 'transcript' in alt:
                        results.append(f"[Google-Alt] {alt['transcript']}")
                        print(f"      Google替代: {alt['transcript']}")
        except:
            pass
        
        # 返回最長的結果
        if results:
            best_result = max(results, key=len)
            return best_result.split('] ', 1)[1] if '] ' in best_result else best_result
        
        return ""

    def aggressive_audio_enhancement(self, audio_path: str) -> str:
        """激進的音頻增強"""
        try:
            audio = AudioSegment.from_wav(audio_path)
            
            # 1. 強化音量
            if audio.dBFS < -30:
                audio = audio + (20 - audio.dBFS)  # 大幅提升音量
            
            # 2. 減少背景噪音
            # 使用更激進的濾波
            audio = audio.high_pass_filter(200)  # 移除低頻噪音
            audio = audio.low_pass_filter(8000)  # 保留語音頻率
            
            # 3. 壓縮和正規化
            audio = audio.compress_dynamic_range(threshold=-25.0, ratio=6.0)
            audio = audio.normalize()
            
            # 4. 去除靜音片段
            from pydub.silence import detect_nonsilent
            nonsilent_ranges = detect_nonsilent(
                audio, 
                min_silence_len=200,  # 最小靜音長度
                silence_thresh=audio.dBFS - 20
            )
            
            if nonsilent_ranges:
                # 只保留有聲音的部分
                combined = AudioSegment.empty()
                for start_ms, end_ms in nonsilent_ranges:
                    combined += audio[start_ms:end_ms]
                audio = combined
            
            # 5. 保存
            enhanced_path = audio_path.replace('.wav', '_super_enhanced.wav')
            audio.export(enhanced_path, format="wav", parameters=["-ar", "16000"])  # 16kHz採樣率
            
            return enhanced_path
            
        except Exception as e:
            print(f"激進音頻增強失敗: {e}")
            return audio_path

    ### Whisper
    def clear_whisper_cache(self):
        """清理損壞的 Whisper 模型快取"""
        import os
        import shutil
        from pathlib import Path
        
        cache_dir = Path.home() / ".cache" / "whisper"
        
        if cache_dir.exists():
            try:
                shutil.rmtree(cache_dir)
                print(f"已清理 Whisper 快取: {cache_dir}")
                return True
            except Exception as e:
                print(f"清理快取失敗: {e}")
                return False
        else:
            print("快取目錄不存在")
            return True
        
    def load_whisper_model(self, model_size: str = "base"):
        """載入 Whisper 模型 - 避免重複載入"""
        if not WHISPER_AVAILABLE:
            return False
     
        # 檢查是否已經載入相同模型
        if (self.whisper_model is not None and 
            hasattr(self, 'current_model_size') and 
            self.current_model_size == model_size):
            print(f"Whisper {model_size} 模型已載入，跳過")
            return True
        
        try:
            print(f"正在載入 Whisper {model_size} 模型...")
            self.whisper_model = whisper.load_model(model_size)
            self.current_model_size = model_size
            self.use_whisper = True
            print("Whisper 模型載入成功")
            return True
        
        except Exception as e:
            # 錯誤處理邏輯...
            print(f"Whisper 模型載入失敗: {e}")
            # 如果是 checksum 錯誤，自動清理並重試
            if "checksum" in str(e).lower() or "sha256" in str(e).lower():
                print("檢測到模型檔案損壞，正在清理快取...")
                if self.clear_whisper_cache():
                    try:
                        print(f"重新載入 Whisper {model_size} 模型...")
                        self.whisper_model = whisper.load_model(model_size)
                        self.use_whisper = True
                        print("重新載入成功")
                        return True
                    except Exception as e2:
                        print(f"重新載入也失敗: {e2}")
    
    def speech_to_text_whisper(self, audio_path: str, language: str = "zh") -> str:
        """使用 Whisper 進行語音識別 - 改善語言檢測"""
        if not self.use_whisper or not self.whisper_model:
            return ""
        
        try:
            # 第一次嘗試：自動檢測，但提供語言提示
            result = self.whisper_model.transcribe(
                audio_path, 
                language=None,  # 自動檢測
                fp16=False,
                temperature=0.0,
                condition_on_previous_text=False,
            )
            
            text = result["text"].strip()
            detected_lang = result.get("language", "unknown")
            
            print(f"      Whisper 檢測語言: {detected_lang}")
            
            # 如果自動檢測失敗或結果可疑，強制指定中文
            if detected_lang in ['nn', 'unknown', None] or not text or self.is_result_suspicious(text):
                print(f"      語言檢測失敗或結果可疑，強制指定中文...")
                
                # 嘗試多種中文設定
                for lang_code in ['zh', 'zh-cn', 'zh-tw']:
                    try:
                        result2 = self.whisper_model.transcribe(
                            audio_path, 
                            language=lang_code,
                            temperature=0.0,
                            condition_on_previous_text=False,
                        )
                        text2 = result2["text"].strip()
                        
                        if text2 and not self.is_result_suspicious(text2):
                            text = text2
                            print(f"      使用 {lang_code} 成功: {text}")
                            break
                    except:
                        continue
            
            text = self.clean_whisper_result(text)
            
            if text:
                print(f"      Whisper 最終結果: {text}")
                return text
            else:
                print(f"      Whisper 無有效結果")
                return ""
            
        except Exception as e:
            print(f"      Whisper 識別失敗: {e}")
            return ""

    def is_result_suspicious(self, text: str) -> bool:
        """檢查識別結果是否可疑"""
        if not text:
            return True
        
        words = text.split()
        
        # 檢查重複
        if len(words) > 6:
            unique_ratio = len(set(words)) / len(words)
            if unique_ratio < 0.5:  # 重複率超過50%
                return True
        
        # 檢查是否包含奇怪字符
        if any(char in text for char in ['♪', '♫', '[', ']', '(', ')', '*']):
            return True
        
        # 檢查長度異常
        if len(text) > 200:  # 超長結果通常有問題
            return True
        
        return False

    def clean_whisper_result(self, text: str) -> str:
        """清理 Whisper 識別結果"""
        if not text:
            return text
        
        # 移除音樂符號和標點
        import re
        text = re.sub(r'[♪♫\[\]\(\)\*]', '', text)
        
        # 移除重複片段
        text = self.remove_repetition(text)
        
        # 移除過短或過長的結果
        words = text.split()
        if len(words) < 2 or len(words) > 30:
            return ""
        
        return text.strip()
    
    def remove_repetition(self, text: str) -> str:
        """移除文字中的重複片段"""
        if not text:
            return text
        
        words = text.split()
        if len(words) < 6:
            return text
        
        # 檢測重複模式
        for pattern_len in range(2, len(words) // 3 + 1):
            for start in range(len(words) - pattern_len * 2 + 1):
                pattern = words[start:start + pattern_len]
                
                # 檢查是否有連續重複
                repeats = 1
                pos = start + pattern_len
                
                while pos + pattern_len <= len(words):
                    if words[pos:pos + pattern_len] == pattern:
                        repeats += 1
                        pos += pattern_len
                    else:
                        break
                
                # 如果重複超過2次，移除多餘部分
                if repeats >= 3:
                    # 保留一次，移除其他
                    clean_words = words[:start + pattern_len] + words[pos:]
                    return " ".join(clean_words)
        
        return text
    ###

    def speech_to_text(self, audio_chunk_path: str, language: str = 'chinese', 
                  use_multi_strategy: bool = False, prefer_whisper: bool = True) -> str:
        """語音轉文字 - 統一接口"""
        
        # 1. 先進行激進音頻增強
        enhanced_path = self.aggressive_audio_enhancement(audio_chunk_path)
        
        # 選擇語言代碼
        lang_code = self.language_codes.get(language, 'zh-TW')
        
        result = ""

        # 優先使用 Whisper (如果可用且啟用)
        if prefer_whisper and self.use_whisper:
            # 轉換語言代碼
            whisper_lang = "zh" if language in ['chinese', 'zh-TW', 'zh-CN'] else "en"
            result = self.speech_to_text_whisper(audio_chunk_path, whisper_lang)
            
            if result:
                return result
            else:
                print("      Whisper 失敗，嘗試 Google 識別...")
        
        if use_multi_strategy:
            # 2. 使用增強後的音頻進行多引擎識別
            result = self.multi_engine_recognition(enhanced_path)
            if not result:
                result = self.multi_recognition_strategy(enhanced_path, lang_code)
        else:
            # 3. 預設使用多引擎識別
            result = self.multi_engine_recognition(enhanced_path)
            if not result:
                result = self.speech_to_text_basic(enhanced_path, lang_code)
        
        # 4. 清理臨時文件
        try:
            if enhanced_path != audio_chunk_path:
                os.remove(enhanced_path)
        except:
            pass
        
        if result:
            print(f"      最終識別結果: {result}")
        else:
            print(f"      所有識別方法都失敗")
        
        return result
    