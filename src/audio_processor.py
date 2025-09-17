# audio_processor.py - 音頻處理模組
import os
from moviepy.editor import VideoFileClip
from pydub import AudioSegment
from typing import List, Tuple


class AudioProcessor:
    """音頻處理器"""
    
    def __init__(self):
        self.chunk_duration = 10  # 預設分割時間
    
    def extract_audio_from_video(self, video_path: str, audio_path: str = None) -> str:
        """從影片中提取音頻"""
        if audio_path is None:
            audio_path = video_path.rsplit('.', 1)[0] + '_audio.wav'
        
        try:
            print("正在提取音頻...")
            video = VideoFileClip(video_path)
            audio = video.audio
            audio.write_audiofile(audio_path, verbose=False, logger=None)
            video.close()
            audio.close()
            print(f"音頻已提取到: {audio_path}")
            return audio_path
        except Exception as e:
            print(f"提取音頻失敗: {e}")
            return None
    
    def split_audio_chunks(self, audio_path: str, chunk_duration: int = None) -> List[Tuple[str, float, float]]:
        """將音頻分割成小段以便處理"""
        if chunk_duration is None:
            chunk_duration = self.chunk_duration
            
        try:
            audio = AudioSegment.from_wav(audio_path)
            chunk_length_ms = chunk_duration * 1000
            chunks = []
            
            for i, start_time in enumerate(range(0, len(audio), chunk_length_ms)):
                end_time = min(start_time + chunk_length_ms, len(audio))
                chunk = audio[start_time:end_time]
                
                chunk_path = f"temp_chunk_{i}.wav"
                chunk.export(chunk_path, format="wav")
                
                chunks.append((chunk_path, start_time / 1000.0, end_time / 1000.0))
            
            print(f"   音頻分割完成，共 {len(chunks)} 個片段")
            return chunks
        except Exception as e:
            print(f"分割音頻失敗: {e}")
            return []
    
    def split_audio_with_overlap(self, audio_path: str, segment_duration: int = 10, 
                                overlap_duration: int = 2) -> List[Tuple[str, float, float]]:
        """重疊分割音頻 - 避免髒話被切斷"""
        try:
            audio = AudioSegment.from_wav(audio_path)
            segment_length_ms = segment_duration * 1000
            overlap_length_ms = overlap_duration * 1000
            step_length_ms = segment_length_ms - overlap_length_ms
            
            segments = []
            
            for i, start_ms in enumerate(range(0, len(audio), step_length_ms)):
                end_ms = min(start_ms + segment_length_ms, len(audio))
                
                # 提取片段
                segment = audio[start_ms:end_ms]
                segment_path = f"temp_segment_{i}.wav"
                segment.export(segment_path, format="wav")
                
                start_sec = start_ms / 1000.0
                end_sec = end_ms / 1000.0
                
                segments.append((segment_path, start_sec, end_sec))
            
            print(f"   重疊分割完成，共 {len(segments)} 個片段（重疊 {overlap_duration} 秒）")
            return segments
            
        except Exception as e:
            print(f"重疊分割失敗: {e}")
            return []
    
    def find_word_timing_in_segment(self, audio_segment_path: str, text: str, 
                                   target_word: str, segment_start_time: float) -> List[Tuple[float, float]]:
        """在音頻片段中找到特定詞彙的精確時間位置"""
        try:
            # 估算詞彙在片段內的相對時間
            audio = AudioSegment.from_wav(audio_segment_path)
            segment_duration = len(audio) / 1000.0
            
            # 根據髒話長度估算發音時間
            word_length = len(target_word)
            if word_length <= 2:
                estimated_duration = 0.6
            elif word_length <= 4:
                estimated_duration = 1.2
            else:
                estimated_duration = 1.8
            
            # 在文字中找到髒話位置
            text_lower = text.lower()
            target_lower = target_word.lower()
            
            word_timings = []
            start_pos = 0
            
            while True:
                pos = text_lower.find(target_lower, start_pos)
                if pos == -1:
                    break
                
                # 計算在片段內的相對位置
                chars_before = pos
                total_chars = len(text_lower)
                
                # 片段內的相對時間
                relative_start = (chars_before / total_chars) * segment_duration
                relative_end = min(relative_start + estimated_duration, segment_duration)
                
                # 轉換為絕對時間
                absolute_start = segment_start_time + relative_start
                absolute_end = segment_start_time + relative_end
                
                word_timings.append((absolute_start, absolute_end))
                start_pos = pos + 1
            
            return word_timings
            
        except Exception as e:
            print(f"詞彙定位失敗: {e}")
            return []
    
    def cleanup_temp_files(self, pattern: str = "temp_"):
        """清理臨時文件"""
        try:
            for f in os.listdir('.'):
                if f.startswith(pattern) and (f.endswith('.wav') or f.endswith('.mp4')):
                    try:
                        os.remove(f)
                    except:
                        pass
            print("臨時文件清理完成")
        except Exception as e:
            print(f"清理臨時文件失敗: {e}")