# enhanced_profanity_detector.py - 整合訓練功能的特殊詞語檢測器
import os
import re
from typing import List, Dict, Tuple
from adaptive_training_module import AdaptiveTrainingModule

class EnhancedProfanityDetector:
    """增強的特殊詞語檢測器 - 整合自適應訓練"""
    
    def __init__(self):
        # 原有的規則檢測
        self.profanity_words = {
            "幹": ["beep"], 
            "甘": ["beep"],
            "干": ["beep"],
            "幹你": ["beep"],
            "操你": ["beep"],
            "靠北": ["beep"],
            "幹你娘": ["beep"],
            "操你媽": ["beep"],
            "衝三小": ["beep"],
            "甘霖娘": ["beep"],
            "幹哩娘": ["beep"],
            "幹你老師": ["beep"],
            "操你全家": ["beep"],
            "你好我是Google小姐": ["beep"],  # 測試用
        }
        
        # 新增：自適應訓練模組
        self.adaptive_trainer = AdaptiveTrainingModule()
        self.use_adaptive_detection = False
        self.adaptive_weight = 0.3  # 自適應檢測的權重
        
        # 模糊匹配模式
        self.profanity_patterns = {
            "幹你娘": [r"[幹干乾甘][你泥妳尼][娘涼良梁]"],
            "操你媽": [r"[操草曹][你泥妳尼][媽馬麻母嗎]"],
            "幹你老師": [r"[幹干乾甘][你泥妳尼][老][師]"],
            "靠北": [r"[靠考烤][北杯背悲]"],
        }
    
    def detect_profanity_basic(self, text: str) -> List[str]:
        """基本特殊詞語檢測（原有功能）"""
        found_profanity = []
        text_lower = text.lower()
        
        for profanity in self.profanity_words.keys():
            if profanity in text_lower:
                found_profanity.append(profanity)
        
        return found_profanity
    
    def detect_profanity_fuzzy(self, text: str) -> List[str]:
        """模糊匹配特殊詞語檢測（原有功能）"""
        found_profanity = []
        text_clean = re.sub(r'[^\w\s]', '', text.lower())
        
        for profanity, patterns in self.profanity_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_clean):
                    found_profanity.append(profanity)
                    break
        
        return found_profanity
    
    def detect_profanity_adaptive(self, audio_segment_path: str) -> Tuple[List[str], float]:
        """自適應音頻檢測"""
        if not self.use_adaptive_detection or not self.adaptive_trainer.is_trained:
            return [], 0.0
        
        try:
            probability = self.adaptive_trainer.predict_profanity_probability(audio_segment_path)
            
            # 根據概率判斷
            if probability > 0.7:
                confidence_level = 'high'
                detected = ['adaptive_detection']
            elif probability > 0.4:
                confidence_level = 'medium'
                detected = ['adaptive_detection']
            else:
                detected = []
                confidence_level = 'low'
            
            return detected, probability
            
        except Exception as e:
            print(f"自適應檢測失敗: {e}")
            return [], 0.0
    
    def detect_profanity(self, text: str = "", audio_segment_path: str = "", use_fuzzy: bool = True) -> Dict:
        """整合檢測方法"""
        detection_results = {
            'found_profanity': [],
            'confidence': 0.0,
            'methods_used': [],
            'adaptive_probability': 0.0
        }
        
        all_detections = []
        confidence_scores = []
        
        # 方法1：基本文字檢測
        if text:
            basic_results = self.detect_profanity_basic(text)
            if basic_results:
                all_detections.extend(basic_results)
                confidence_scores.append(0.8)
                detection_results['methods_used'].append('basic_text')
        
        # 方法2：模糊文字匹配
        if text and use_fuzzy:
            fuzzy_results = self.detect_profanity_fuzzy(text)
            if fuzzy_results:
                all_detections.extend(fuzzy_results)
                confidence_scores.append(0.6)
                detection_results['methods_used'].append('fuzzy_text')
        
        # 方法3：自適應音頻檢測
        if audio_segment_path and os.path.exists(audio_segment_path):
            adaptive_results, adaptive_prob = self.detect_profanity_adaptive(audio_segment_path)
            detection_results['adaptive_probability'] = adaptive_prob
            
            if adaptive_results:
                all_detections.extend(['訓練模型檢測'])
                
                # 根據訓練準確率調整信心度
                training_accuracy = self.adaptive_trainer.training_accuracy
                adjusted_confidence = adaptive_prob * training_accuracy
                confidence_scores.append(adjusted_confidence)
                detection_results['methods_used'].append('adaptive_audio')
        
        # 整合結果
        if all_detections:
            detection_results['found_profanity'] = list(set(all_detections))
            
            # 計算整體信心度
            if confidence_scores:
                # 使用加權平均，給自適應檢測更高權重
                weights = []
                for method in detection_results['methods_used']:
                    if 'adaptive' in method:
                        weights.append(self.adaptive_weight)
                    else:
                        weights.append(1 - self.adaptive_weight)
                
                if len(weights) == len(confidence_scores):
                    detection_results['confidence'] = sum(w * c for w, c in zip(weights, confidence_scores)) / sum(weights)
                else:
                    detection_results['confidence'] = max(confidence_scores)
            
            print(f"檢測結果: {detection_results}")
        
        return detection_results
    
    def enable_adaptive_detection(self, model_path: str = None):
        """啟用自適應檢測"""
        if model_path and os.path.exists(model_path):
            if self.adaptive_trainer.load_model(model_path):
                self.use_adaptive_detection = True
                print(f"自適應模型已載入，準確率: {self.adaptive_trainer.training_accuracy:.3f}")
                return True
        
        print("自適應檢測啟用失敗")
        return False
    
    def disable_adaptive_detection(self):
        """停用自適應檢測"""
        self.use_adaptive_detection = False
        print("自適應檢測已停用")
    
    def train_adaptive_model(self, annotations: List[Dict]) -> Dict:
        """訓練自適應模型"""
        result = self.adaptive_trainer.quick_train_from_annotations(annotations)
        
        if result.get('accuracy', 0) > 0.5:  # 準確率超過50%才啟用
            self.use_adaptive_detection = True
            print(f"自適應模型訓練完成，準確率: {result['accuracy']:.3f}")
        else:
            print("模型準確率過低，建議增加訓練樣本")
        
        return result
    
    def save_adaptive_model(self, model_path: str):
        """保存自適應模型"""
        if self.adaptive_trainer.is_trained:
            self.adaptive_trainer.save_model(model_path)
            print(f"模型已保存: {model_path}")
        else:
            print("沒有訓練好的模型可保存")
    
    def get_detection_status(self) -> Dict:
        """獲取檢測系統狀態"""
        return {
            'basic_detection': True,
            'fuzzy_detection': True,
            'adaptive_detection': self.use_adaptive_detection,
            'adaptive_trained': self.adaptive_trainer.is_trained,
            'adaptive_accuracy': self.adaptive_trainer.training_accuracy,
            'profanity_words_count': len(self.profanity_words)
        }
    
    # 保持向後兼容
    def add_custom_profanity(self, words: List[str]):
        """添加自定義特殊詞語詞庫"""
        for word in words:
            self.profanity_words[word.lower()] = ["beep"]
        print(f"已添加 {len(words)} 個自定義詞彙到過濾清單")