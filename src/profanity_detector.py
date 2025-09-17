# profanity_detector.py - 髒話檢測模組
import re
from typing import List, Dict


class ProfanityDetector:
    """髒話檢測器"""
    
    def __init__(self):
        # 髒話詞庫 (包含不同長度)
        self.profanity_words = {
            # 一字髒話
            "幹": ["beep"], 
            "甘": ["beep"],
            "干": ["beep"],

            # 二字髒話
            "幹你": ["beep"],
            "操你": ["beep"],
            "靠北": ["beep"],
            
            # 三字髒話
            "幹你娘": ["beep"],
            "操你媽": ["beep"],
            "衝三小": ["beep"],
            "甘霖娘": ["beep"],
            "幹哩娘": ["beep"],
            "幹哩涼": ["beep"],
            "幹尼娘": ["beep"],
            "幹你涼": ["beep"],

            # 四字髒話
            "幹你老師": ["beep"],
            "操你全家": ["beep"],
            "幹你老母": ["beep"],
            "白痴智障": ["beep"],
            
            # 五字髒話
            "幹你娘機掰": ["beep"],
            "操你媽的逼": ["beep"],

            # Test
            "你好我是Google小姐": ["beep"],
        }
        
        # 擴展的髒話模式 - 包含可能的變形
        self.profanity_patterns = {
            "幹你娘": [
                r"幹.*你.*娘",      # 幹-你-娘 (有停頓)
                r"幹.*娘",          # 幹-娘 (省略你)
                r"干.*你.*娘",      # 錯字識別
                r"乾.*你.*娘",      # 同音字
                r"幹.*泥.*娘",      # 口音變化
                r"幹.*妳.*娘",      # 注音輸入法
            ],
            "操你媽": [
                r"操.*你.*媽",
                r"操.*妳.*媽",
                r"草.*你.*媽",      # 同音字
                r"操.*你.*馬",      # 諧音
                r"操.*媽",
                r"操.*你.*母",
            ],
            "幹你老師": [
                r"幹.*你.*老.*師",
                r"幹.*老.*師",
                r"乾.*你.*老.*師",
                r"幹.*泥.*老.*師",
            ],
            "靠北": [
                r"靠.*北",
                r"考.*北",
                r"靠.*杯",
                r"cao.*bei",        # 英文輸入
            ]
        }
    
    def detect_profanity_basic(self, text: str) -> List[str]:
        """基本髒話檢測"""
        found_profanity = []
        text_lower = text.lower()
        
        for profanity in self.profanity_words.keys():
            if profanity in text_lower:
                found_profanity.append(profanity)
        
        return found_profanity
    
    def detect_profanity_fuzzy(self, text: str) -> List[str]:
        """模糊匹配髒話檢測 - 處理重音、延遲等問題"""
        found_profanity = []
        text_clean = re.sub(r'[^\w\s]', '', text.lower())  # 移除標點符號
        
        print(f"      模糊檢測文字: 「{text_clean}」")
        
        for profanity, patterns in self.profanity_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_clean):
                    found_profanity.append(profanity)
                    print(f"      🎯 模糊匹配到: {profanity} (模式: {pattern})")
                    break  # 找到一個就跳到下個髒話
        
        return found_profanity
    
    def detect_profanity(self, text: str, use_fuzzy: bool = True) -> List[str]:
        """檢測文字中的髒話"""
        # 基本檢測
        basic_results = self.detect_profanity_basic(text)
        
        if use_fuzzy:
            # 模糊檢測
            fuzzy_results = self.detect_profanity_fuzzy(text)
            # 合併結果並去重
            all_results = list(set(basic_results + fuzzy_results))
            return all_results
        
        return basic_results
    
    def add_custom_profanity(self, words: List[str]):
        """添加自定義髒話詞庫"""
        for word in words:
            self.profanity_words[word.lower()] = ["beep"]
        print(f"已添加 {len(words)} 個自定義詞彙到過濾清單")
    
    def estimate_word_duration(self, word: str) -> float:
        """根據髒話長度估算發音時間"""
        word_length = len(word)
        if word_length <= 2:
            return 0.6
        elif word_length <= 4:
            return 1.2
        else:
            return 1.8