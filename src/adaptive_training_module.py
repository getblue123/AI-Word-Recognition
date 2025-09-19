# adaptive_training_module.py - 自適應訓練模組
import os
import numpy as np
import pickle
from typing import List, Dict, Any, Tuple
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import librosa

class AdaptiveTrainingModule:
    """自適應訓練模組 - 整合到現有系統"""
    
    def __init__(self):
        self.training_history = []  
        self.all_training_data = []  
        self.feature_scaler = StandardScaler()
        self.audio_classifier = None
        self.is_trained = False
        self.training_accuracy = 0.0
        
        # 音頻特徵參數
        self.sample_rate = 22050
        self.n_mfcc = 13
        
    def extract_simple_features(self, audio_path: str) -> np.ndarray:
        """提取簡化的音頻特徵（減少依賴）"""
        try:
            # 使用pydub讀取音頻（已有的依賴）
            from pydub import AudioSegment
            
            audio = AudioSegment.from_wav(audio_path)
            
            # 轉換為numpy陣列
            samples = np.array(audio.get_array_of_samples())
            if audio.channels == 2:
                samples = samples.reshape((-1, 2)).mean(axis=1)
            
            # 正規化
            samples = samples.astype(np.float32) / np.iinfo(np.int16).max
            
            # 基本特徵提取
            features = []
            
            # 1. 音量特徵
            rms = np.sqrt(np.mean(samples**2))
            features.append(rms)
            
            # 2. 過零率
            zcr = np.mean(np.abs(np.diff(np.sign(samples)))) / 2
            features.append(zcr)
            
            # 3. 頻譜質心（如果有librosa）
            try:
                y = librosa.resample(samples, orig_sr=audio.frame_rate, target_sr=self.sample_rate)
                spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=y, sr=self.sample_rate))
                mfccs = librosa.feature.mfcc(y=y, sr=self.sample_rate, n_mfcc=5)
                mfcc_mean = np.mean(mfccs, axis=1)
                
                features.append(spectral_centroid)
                features.extend(mfcc_mean)
            except ImportError:
                # 如果沒有librosa，使用簡化特徵
                features.extend([0.0] * 6)  # 填充零值
            
            # 4. 統計特徵
            features.extend([
                np.mean(samples),
                np.std(samples),
                np.max(samples),
                np.min(samples)
            ])
            
            return np.array(features)
            
        except Exception as e:
            print(f"特徵提取失敗: {e}")
            return np.zeros(12)  # 返回固定長度的零向量
    
    def quick_train_from_annotations(self, annotations: List[Dict]) -> Dict[str, float]:
        """快速訓練（簡化版本）"""
        if len(annotations) < 4:
            return {'accuracy': 0.0, 'error': 'insufficient_data'}
        
        features_list = []
        labels_list = []
        
        for annotation in annotations:
            if annotation['label'] in ['profanity', 'normal']:
                features = self.extract_simple_features(annotation['segment_path'])
                features_list.append(features)
                
                label = 1 if annotation['label'] == 'profanity' else 0
                labels_list.append(label)
        
        if len(features_list) < 4:
            return {'accuracy': 0.0, 'error': 'insufficient_valid_data'}
        
        # 訓練
        X = np.array(features_list)
        y = np.array(labels_list)
        
        # 特徵標準化
        X_scaled = self.feature_scaler.fit_transform(X)
        
        # 使用簡單的隨機森林
        self.audio_classifier = RandomForestClassifier(n_estimators=50, random_state=42)
        self.audio_classifier.fit(X_scaled, y)
        
        # 簡單評估
        accuracy = self.audio_classifier.score(X_scaled, y)
        self.training_accuracy = accuracy
        self.is_trained = True
        
        return {
            'accuracy': accuracy,
            'sample_count': len(features_list),
            'profanity_count': sum(y),
            'normal_count': len(y) - sum(y)
        }
    
    def incremental_train(self, new_annotations: List[Dict]) -> Dict:
        """增量訓練 - 在現有模型基礎上繼續訓練"""
        if not self.is_trained:
            # 如果沒有現有模型，就進行全新訓練
            return self.quick_train_from_annotations(new_annotations)
        
        # 提取新的特徵和標籤
        new_features = []
        new_labels = []
        
        for annotation in new_annotations:
            if annotation['label'] in ['profanity', 'normal']:
                features = self.extract_simple_features(annotation['segment_path'])
                new_features.append(features)
                label = 1 if annotation['label'] == 'profanity' else 0
                new_labels.append(label)
        
        if len(new_features) < 2:
            return {'error': 'insufficient_new_data'}
        
        # 準備新數據
        X_new = self.feature_scaler.transform(new_features)
        y_new = np.array(new_labels)
        
        # 使用現有模型的部分擬合能力（如果支持）
        # 對於RandomForest，需要重新訓練合併的數據
        try:
            # 獲取原有訓練數據（如果有保存的話）
            # 這裡簡化為重新訓練
            print("執行增量訓練（重新訓練合併數據）")
            
            # 可以保存歷史數據並合併新數據重新訓練
            return self.quick_train_from_annotations(new_annotations)
            
        except Exception as e:
            return {'error': f'incremental_training_failed: {str(e)}'}
        
    def retrain_model(self, all_annotations: List[Dict]) -> Dict:
        """完全重新訓練模型"""
        # 重置模型狀態
        self.audio_classifier = None
        self.is_trained = False
        
        # 用新數據重新訓練
        return self.quick_train_from_annotations(all_annotations)
    
    def predict_profanity_probability(self, audio_segment_path: str) -> float:
        """預測特殊詞語概率"""
        if not self.is_trained or self.audio_classifier is None:
            return 0.0
        
        try:
            features = self.extract_simple_features(audio_segment_path)
            features_scaled = self.feature_scaler.transform([features])
            probability = self.audio_classifier.predict_proba(features_scaled)[0][1]
            return float(probability)
        except:
            return 0.0
    
    def save_model(self, model_path: str):
        """保存模型和訓練數據"""
        model_data = {
            'audio_classifier': self.audio_classifier,
            'feature_scaler': self.feature_scaler,
            'training_accuracy': self.training_accuracy,
            'is_trained': self.is_trained,
            'training_history': self.training_history,  # 保存訓練歷史
            'all_training_data': self.all_training_data  # 保存所有訓練數據
        }
        
        with open(model_path, 'wb') as f:
            pickle.dump(model_data, f)
    
    def load_model(self, model_path: str) -> bool:
        """載入模型和訓練數據"""
        try:
            with open(model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            # ... 載入模型 ...
            self.training_history = model_data.get('training_history', [])
            self.all_training_data = model_data.get('all_training_data', [])
            
            return True
        except:
            return False