# video_muting_processor.py - 影片消音處理模組
import os
import subprocess
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_audioclips
from pydub import AudioSegment
from typing import List, Dict


class VideoMutingProcessor:
    """影片消音處理器"""
    
    def create_muted_video_with_ffmpeg(self, video_path: str, profanity_segments: List[Dict], 
                                      output_path: str = None) -> str:
        """使用FFmpeg創建消音影片，保持同步"""
        if output_path is None:
            output_path = video_path.rsplit('.', 1)[0] + '_cleaned.mp4'
        
        try:
            if not profanity_segments:
                print("沒有檢測到髒話，複製原影片")
                # 直接複製
                cmd = ['ffmpeg', '-i', video_path, '-c', 'copy', '-y', output_path]
            else:
                print(f"正在對 {len(profanity_segments)} 個片段進行消音...")
                
                # 創建音量過濾器
                volume_filters = []
                for segment in profanity_segments:
                    start_time = segment['start_time']
                    end_time = segment['end_time']
                    # 在指定時間段將音量設為0
                    volume_filters.append(f"volume=0:enable='between(t,{start_time},{end_time})'")
                
                # 組合所有過濾器
                filter_string = ",".join(volume_filters)
                
                cmd = [
                    'ffmpeg',
                    '-i', video_path,
                    '-filter:a', filter_string,  # 音頻過濾器
                    '-c:v', 'copy',              # 複製影片流（不重新編碼）
                    '-c:a', 'aac',               # 音頻編碼
                    '-y', output_path
                ]
            
            # 執行FFmpeg命令
            result = subprocess.run(cmd, capture_output=True, text=True, 
                                encoding='utf-8', errors='ignore')
            
            if result.returncode == 0:
                print(f"✅ 消音影片已保存到: {output_path}")
                return output_path
            else:
                print(f"❌ FFmpeg處理失敗: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"創建消音影片失敗: {e}")
            return None
    
    def create_muted_video_with_moviepy(self, video_path: str, profanity_segments: List[Dict], 
                                       output_path: str = None) -> str:
        """使用MoviePy創建消音後的影片"""
        if output_path is None:
            output_path = video_path.rsplit('.', 1)[0] + '_cleaned.mp4'
        
        try:
            print("正在創建消音影片...")
            
            # 載入原始影片
            video = VideoFileClip(video_path)
            audio = video.audio
            
            # 創建消音片段
            if profanity_segments:
                print(f"需要消音 {len(profanity_segments)} 個片段")
                
                # 使用 moviepy 進行消音處理
                audio_clips = []
                last_end = 0
                
                for segment in profanity_segments:
                    start_time = segment['start_time']
                    end_time = segment['end_time']
                    
                    # 添加正常音頻片段
                    if start_time > last_end:
                        normal_clip = audio.subclip(last_end, start_time)
                        audio_clips.append(normal_clip)
                    
                    # 添加靜音片段
                    duration = end_time - start_time
                    silence = AudioSegment.silent(duration=int(duration * 1000))
                    silence_path = f"temp_silence_{len(audio_clips)}.wav"
                    silence.export(silence_path, format="wav")
                    
                    silence_clip = AudioFileClip(silence_path)
                    audio_clips.append(silence_clip)
                    
                    last_end = end_time
                
                # 添加剩餘的正常音頻
                if last_end < video.duration:
                    final_clip = audio.subclip(last_end, video.duration)
                    audio_clips.append(final_clip)
                
                # 合併音頻片段
                if audio_clips:
                    new_audio = concatenate_audioclips(audio_clips)
                    
                    # 創建新影片
                    final_video = video.set_audio(new_audio)
                    final_video.write_videofile(output_path, verbose=False, logger=None)
                    
                    # 清理
                    for clip in audio_clips:
                        clip.close()
                    new_audio.close()
                    final_video.close()
                else:
                    # 如果沒有音頻片段，直接複製原影片
                    video.write_videofile(output_path, verbose=False, logger=None)
            else:
                print("沒有檢測到髒話，複製原影片")
                video.write_videofile(output_path, verbose=False, logger=None)
            
            video.close()
            audio.close()
            
            # 清理臨時文件
            self._cleanup_silence_files()
            
            print(f"消音影片已保存到: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"創建消音影片失敗: {e}")
            return None
    
    def _cleanup_silence_files(self):
        """清理靜音臨時文件"""
        for f in os.listdir('.'):
            if f.startswith('temp_silence_') and f.endswith('.wav'):
                try:
                    os.remove(f)
                except:
                    pass
    
    def create_muted_video(self, video_path: str, profanity_segments: List[Dict], 
                          output_path: str = None, use_ffmpeg: bool = True) -> str:
        """創建消音影片 - 統一接口"""
        if use_ffmpeg:
            return self.create_muted_video_with_ffmpeg(video_path, profanity_segments, output_path)
        else:
            return self.create_muted_video_with_moviepy(video_path, profanity_segments, output_path)