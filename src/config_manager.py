# config_manager.py - 配置管理模組
import json
import os
from typing import Dict, Any


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: str = "filter_config.json"):
        self.config_file = config_file
        self.default_config = {
            # 音頻處理設定
            "chunk_duration": 10,
            "use_overlap_segments": False,
            "overlap_duration": 2,
            
            # 語音識別設定
            "language": "chinese",
            "use_multi_recognition": False,
            "use_fuzzy_matching": True,
            
            # 消音設定
            "precise_muting": True,
            "mute_padding": 0.5,
            "use_ffmpeg": True,
            
            # 特殊詞語詞庫設定
            "custom_profanity_words": [],
            
            # 輸出設定
            "output_suffix": "_cleaned",
            "output_format": "mp4"
        }
        
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """載入配置文件"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # 合併預設配置，確保所有必要的鍵都存在
                merged_config = self.default_config.copy()
                merged_config.update(config)
                return merged_config
            except Exception as e:
                print(f"載入配置文件失敗: {e}，使用預設配置")
                return self.default_config.copy()
        else:
            return self.default_config.copy()
    
    def save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            print(f"配置已保存到: {self.config_file}")
        except Exception as e:
            print(f"保存配置文件失敗: {e}")
    
    def get(self, key: str, default=None):
        """獲取配置值"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """設定配置值"""
        self.config[key] = value
    
    def update(self, new_config: Dict[str, Any]):
        """批量更新配置"""
        self.config.update(new_config)
    
    def reset_to_default(self):
        """重置為預設配置"""
        self.config = self.default_config.copy()
    
    def export_config(self, export_path: str):
        """匯出配置到指定檔案"""
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            print(f"配置已匯出到: {export_path}")
        except Exception as e:
            print(f"匯出配置失敗: {e}")
    
    def import_config(self, import_path: str):
        """從指定檔案匯入配置"""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
            self.config.update(imported_config)
            print(f"配置已從 {import_path} 匯入")
        except Exception as e:
            print(f"匯入配置失敗: {e}")


# 使用範例
if __name__ == "__main__":
    # 創建配置管理器
    config = ConfigManager()
    
    # 修改一些設定
    config.set("chunk_duration", 15)
    config.set("precise_muting", False)
    
    # 批量更新
    config.update({
        "use_fuzzy_matching": False,
        "mute_padding": 1.0
    })
    
    # 保存配置
    config.save_config()
    
    # 重新載入測試
    config2 = ConfigManager()
    print("重新載入的配置:")
    print(json.dumps(config2.config, ensure_ascii=False, indent=2))