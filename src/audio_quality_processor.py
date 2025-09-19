# audio_quality_processor.py - 音質改善處理器
import os
import numpy as np
from pydub import AudioSegment
from pydub.effects import normalize, compress_dynamic_range, high_pass_filter, low_pass_filter
from pydub.silence import detect_nonsilent, detect_silence
from typing import Tuple, List
import librosa
import scipy.signal

class AudioQualityProcessor:
    """音質改善處理器"""
    
    def __init__(self):
        self.sample_rate = 16000  # 語音識別最佳採樣率
        self.target_dbfs = -20    # 目標音量級別
        self.noise_floor_threshold = -40  # 噪音底限
        
    def analyze_audio_quality(self, audio_path: str) -> dict:
        """分析音頻質量問題"""
        try:
            audio = AudioSegment.from_wav(audio_path)
            
            # 基本參數
            quality_report = {
                'file_path': audio_path,
                'duration_ms': len(audio),
                'channels': audio.channels,
                'frame_rate': audio.frame_rate,
                'sample_width': audio.sample_width,
                'max_dBFS': audio.max_dBFS,
                'dBFS': audio.dBFS,
                'issues': []
            }
            
            # 檢測問題
            # 1. 音量問題
            if audio.dBFS < -35:
                quality_report['issues'].append('音量過低')
            elif audio.dBFS > -5:
                quality_report['issues'].append('音量過高，可能失真')
            
            # 2. 採樣率問題
            if audio.frame_rate < 16000:
                quality_report['issues'].append('採樣率過低')
            elif audio.frame_rate > 48000:
                quality_report['issues'].append('採樣率過高，建議降採樣')
            
            # 3. 聲道問題
            if audio.channels > 1:
                quality_report['issues'].append('立體聲，建議轉換為單聲道')
            
            # 4. 動態範圍問題
            dynamic_range = audio.max_dBFS - audio.dBFS
            if dynamic_range > 30:
                quality_report['issues'].append('動態範圍過大')
            elif dynamic_range < 5:
                quality_report['issues'].append('動態範圍過小，可能過度壓縮')
            
            # 5. 靜音檢測
            silence_segments = detect_silence(audio, min_silence_len=500, silence_thresh=-50)
            if len(silence_segments) > len(audio) * 0.3:
                quality_report['issues'].append('包含過多靜音')
            
            return quality_report
            
        except Exception as e:
            return {'error': f'分析失敗: {str(e)}'}
    
    def noise_reduction(self, audio_path: str) -> str:
        """噪音抑制"""
        try:
            audio = AudioSegment.from_wav(audio_path)
            
            # 方法1: 頻率域濾波
            # 高通濾波器 - 去除低頻噪音（如空調、交流聲）
            audio = high_pass_filter(audio, 300)
            
            # 低通濾波器 - 去除高頻噪音
            audio = low_pass_filter(audio, 8000)
            
            # 方法2: 簡單的門限降噪
            # 找到靜音片段作為噪音參考
            silence_segments = detect_silence(audio, min_silence_len=200, silence_thresh=-50)
            
            if silence_segments:
                # 計算噪音級別
                noise_samples = []
                for start, end in silence_segments[:3]:  # 只取前3個靜音片段
                    noise_segment = audio[start:end]
                    noise_samples.append(noise_segment.dBFS)
                
                if noise_samples:
                    noise_floor = max(noise_samples) + 3  # 噪音底限
                    
                    # 簡單的噪音門限
                    chunks = []
                    chunk_size = 100  # 100ms 片段
                    
                    for i in range(0, len(audio), chunk_size):
                        chunk = audio[i:i + chunk_size]
                        if chunk.dBFS > noise_floor:
                            chunks.append(chunk)
                        else:
                            # 用低音量替代靜音
                            chunks.append(chunk - 20)
                    
                    if chunks:
                        audio = sum(chunks)
            
            # 保存處理後的音頻
            output_path = audio_path.replace('.wav', '_denoised.wav')
            audio.export(output_path, format="wav")
            
            return output_path
            
        except Exception as e:
            print(f"降噪處理失敗: {e}")
            return audio_path
    
    def enhance_speech_clarity(self, audio_path: str) -> str:
        """增強語音清晰度"""
        try:
            audio = AudioSegment.from_wav(audio_path)
            
            # 1. 頻率增強 - 提升人聲頻段
            # 人聲主要在 300-3400 Hz
            # 使用簡單的頻率強調
            
            # 2. 動態範圍處理
            # 壓縮動態範圍，讓小聲部分更清楚
            audio = compress_dynamic_range(
                audio,
                threshold=-25.0,  # 壓縮閾值
                ratio=3.0,        # 壓縮比例
                attack=5.0,       # 攻擊時間
                release=50.0      # 釋放時間
            )
            
            # 3. 音量正規化
            audio = normalize(audio, headroom=3.0)
            
            # 4. 輕微的高頻提升（模擬 presence boost）
            # 這需要更複雜的 EQ，這裡用簡化版本
            
            output_path = audio_path.replace('.wav', '_enhanced.wav')
            audio.export(output_path, format="wav")
            
            return output_path
            
        except Exception as e:
            print(f"清晰度增強失敗: {e}")
            return audio_path
    
    def format_optimization(self, audio_path: str) -> str:
        """格式優化"""
        try:
            audio = AudioSegment.from_wav(audio_path)
            
            # 1. 轉換為單聲道
            if audio.channels > 1:
                audio = audio.set_channels(1)
            
            # 2. 優化採樣率
            target_rate = 16000  # 語音識別最佳採樣率
            if audio.frame_rate != target_rate:
                audio = audio.set_frame_rate(target_rate)
            
            # 3. 確保16位深度
            audio = audio.set_sample_width(2)  # 2 bytes = 16 bits
            
            output_path = audio_path.replace('.wav', '_optimized.wav')
            audio.export(output_path, format="wav", 
                        parameters=["-ac", "1", "-ar", str(target_rate)])
            
            return output_path
            
        except Exception as e:
            print(f"格式優化失敗: {e}")
            return audio_path
    
    def remove_clicks_pops(self, audio_path: str) -> str:
        """去除爆音和咔嗒聲"""
        try:
            # 載入音頻數據
            audio = AudioSegment.from_wav(audio_path)
            raw_data = np.array(audio.get_array_of_samples())
            
            # 如果是立體聲，轉換為單聲道
            if audio.channels == 2:
                raw_data = raw_data.reshape((-1, 2))
                raw_data = raw_data.mean(axis=1)
            
            # 檢測和修復爆音
            # 爆音通常是突然的大幅度變化
            diff = np.abs(np.diff(raw_data))
            threshold = np.percentile(diff, 99)  # 99百分位作為閾值
            
            pop_indices = np.where(diff > threshold * 2)[0]
            
            # 修復檢測到的爆音
            for idx in pop_indices:
                if idx > 0 and idx < len(raw_data) - 1:
                    # 用前後平均值替代
                    raw_data[idx] = (raw_data[idx-1] + raw_data[idx+1]) / 2
            
            # 轉換回 AudioSegment
            processed_audio = audio._spawn(raw_data.astype(np.int16).tobytes())
            
            output_path = audio_path.replace('.wav', '_declick.wav')
            processed_audio.export(output_path, format="wav")
            
            return output_path
            
        except Exception as e:
            print(f"爆音去除失敗: {e}")
            return audio_path
    
    def comprehensive_quality_improvement(self, audio_path: str) -> str:
        """綜合音質改善"""
        try:
            print(f"開始處理音頻: {audio_path}")
            
            # 1. 分析音頻質量
            quality_report = self.analyze_audio_quality(audio_path)
            print(f"檢測到的問題: {quality_report.get('issues', [])}")
            
            current_path = audio_path
            processing_steps = []
            
            # 2. 根據檢測到的問題進行處理
            if '立體聲，建議轉換為單聲道' in quality_report.get('issues', []):
                current_path = self.format_optimization(current_path)
                processing_steps.append('格式優化')
            
            if any('噪音' in issue for issue in quality_report.get('issues', [])):
                current_path = self.noise_reduction(current_path)
                processing_steps.append('噪音抑制')
            
            if any('音量' in issue for issue in quality_report.get('issues', [])):
                current_path = self.enhance_speech_clarity(current_path)
                processing_steps.append('語音增強')
            
            # 3. 去除爆音（通用處理）
            current_path = self.remove_clicks_pops(current_path)
            processing_steps.append('爆音去除')
            
            # 4. 最終優化
            if current_path != audio_path:
                final_path = self.format_optimization(current_path)
                processing_steps.append('最終優化')
            else:
                final_path = current_path
            
            print(f"處理完成，執行步驟: {processing_steps}")
            
            # 清理中間文件
            intermediate_files = [
                audio_path.replace('.wav', '_denoised.wav'),
                audio_path.replace('.wav', '_enhanced.wav'),
                audio_path.replace('.wav', '_optimized.wav'),
                audio_path.replace('.wav', '_declick.wav')
            ]
            
            for file_path in intermediate_files:
                if file_path != final_path and os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except:
                        pass
            
            return final_path
            
        except Exception as e:
            print(f"綜合音質改善失敗: {e}")
            return audio_path
    
    def batch_quality_improvement(self, audio_files: List[str]) -> List[str]:
        """批量音質改善"""
        improved_files = []
        
        for i, audio_file in enumerate(audio_files):
            print(f"處理第 {i+1}/{len(audio_files)} 個文件")
            improved_file = self.comprehensive_quality_improvement(audio_file)
            improved_files.append(improved_file)
        
        return improved_files


# 與現有系統的整合適配器
class AudioQualityAdapter:
    """音質處理適配器"""
    
    def __init__(self):
        self.processor = AudioQualityProcessor()
        self.enable_quality_improvement = False
    
    def process_audio_for_recognition(self, audio_path: str) -> str:
        """為語音識別處理音頻質量"""
        if not self.enable_quality_improvement:
            return audio_path
        
        try:
            # 快速質量分析
            quality_report = self.processor.analyze_audio_quality(audio_path)
            
            # 如果沒有明顯問題，跳過處理以節省時間
            if not quality_report.get('issues'):
                return audio_path
            
            # 有問題則進行改善
            improved_path = self.processor.comprehensive_quality_improvement(audio_path)
            
            print(f"音質改善: {audio_path} -> {improved_path}")
            return improved_path
            
        except Exception as e:
            print(f"音質處理出錯: {e}")
            return audio_path  # 失敗時返回原文件


# 使用示例
if __name__ == "__main__":
    processor = AudioQualityProcessor()
    
    # 分析單個文件
    test_file = "test_audio.wav"
    if os.path.exists(test_file):
        quality_report = processor.analyze_audio_quality(test_file)
        print("音質分析結果:")
        for key, value in quality_report.items():
            print(f"  {key}: {value}")
        
        # 改善音質
        improved_file = processor.comprehensive_quality_improvement(test_file)
        print(f"改善後文件: {improved_file}")
    else:
        print("請提供測試音頻文件")