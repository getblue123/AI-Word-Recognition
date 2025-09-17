# main.py - 主程序入口
"""
影片語音辨識髒話自動消音程式
功能：
1. 從影片中提取語音
2. 語音轉文字
3. 檢測髒話/不當用詞
4. 自動消音處理
5. 輸出處理後的影片
"""

import os
from video_processor import VideoProfanityFilter
from gui_interface import create_gui


def main():
    """命令行版本主程式"""
    # 創建過濾器實例
    filter = VideoProfanityFilter()
    
    # 添加自定義髒話詞庫（可選）
    custom_words = ["垃圾", "廢物"]  # 添加你想過濾的詞彙
    filter.add_custom_profanity(custom_words)
    
    # 處理影片
    input_video = "input_video.mp4"  # 替換為你的影片路徑
    output_video = "cleaned_video.mp4"  # 輸出路徑
    
    # 檢查輸入文件是否存在
    if not os.path.exists(input_video):
        print(f"錯誤: 找不到影片文件 {input_video}")
        print("請確保影片文件存在，或修改 input_video 變數為正確的路徑")
        return
    
    try:
        result = filter.process_video(input_video, output_video, language='chinese')
        
        if result:
            print(f"\n✅ 成功！處理後的影片保存在: {result}")
        else:
            print("\n❌ 處理失敗！")
            
    except Exception as e:
        print(f"執行錯誤: {e}")


if __name__ == "__main__":
    print("影片語音髒話過濾器")
    print("1. 命令行版本")
    print("2. GUI版本")
    
    choice = input("請選擇 (1 或 2): ").strip()
    
    if choice == "2":
        create_gui()
    else:
        main()