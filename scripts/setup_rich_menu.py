#!/usr/bin/env python3
"""リッチメニューを設定するスクリプト"""

import sys
import os
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, '/home/hirakata_bot1')

from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    RichMenuRequest,
    RichMenuArea,
    RichMenuBounds,
    RichMenuSize,
    PostbackAction,
    MessagingApiBlob
)
from config import LINE_CHANNEL_ACCESS_TOKEN

def create_rich_menu_image(output_path):
    """リッチメニュー用の画像を生成"""
    # 2500x1686 (Large) or 2500x843 (Small)
    width = 2500
    height = 843
    
    img = Image.new('RGB', (width, height), color='#FFFFFF')
    draw = ImageDraw.Draw(img)
    
    # 背景色 (左側: メニュー, 右側: 登録)
    # 左側 (メインエリア)
    draw.rectangle([(0, 0), (1250, height)], fill='#F0F0F0')
    # 右側 (登録ボタン)
    draw.rectangle([(1250, 0), (width, height)], fill='#667eea')
    
    # テキストを描画 (フォントがない場合はデフォルト)
    try:
        # 日本語フォントを探す
        font_paths = [
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        ]
        font = None
        for path in font_paths:
            if os.path.exists(path):
                font = ImageFont.truetype(path, 100)
                break
        if not font:
            font = ImageFont.load_default()
    except:
        font = ImageFont.load_default()
        
    # 左側のテキスト
    draw.text((625, height//2), "メニュー", fill='#333333', anchor="mm", font=font)
    
    # 右側のテキスト
    draw.text((1875, height//2), "🔔 通知を受け取る\n(登録する)", fill='#FFFFFF', anchor="mm", font=font)
    
    img.save(output_path)
    print(f"画像生成完了: {output_path}")

def setup_rich_menu():
    """リッチメニューを作成・設定"""
    print("=== リッチメニュー設定 ===\n")
    
    configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
    
    with ApiClient(configuration) as api_client:
        messaging_api = MessagingApi(api_client)
        messaging_api_blob = MessagingApiBlob(api_client)
        
        # 1. リッチメニューを作成
        rich_menu_to_create = RichMenuRequest(
            size=RichMenuSize(width=2500, height=843),
            selected=True,
            name="Main Menu",
            chat_bar_text="メニューを開く",
            areas=[
                # 左側: メニュー (今のところ何もしない、またはヘルプ)
                RichMenuArea(
                    bounds=RichMenuBounds(x=0, y=0, width=1250, height=843),
                    action=PostbackAction(data="action=help", label="ヘルプ")
                ),
                # 右側: 登録ボタン
                RichMenuArea(
                    bounds=RichMenuBounds(x=1250, y=0, width=1250, height=843),
                    action=PostbackAction(data="action=register", label="登録する")
                )
            ]
        )
        
        rich_menu_id = messaging_api.create_rich_menu(rich_menu_to_create).rich_menu_id
        print(f"リッチメニュー作成成功: {rich_menu_id}")
        
        # 2. 画像をアップロード
        image_path = "rich_menu.png"
        create_rich_menu_image(image_path)
        
        with open(image_path, 'rb') as f:
            image_data = f.read()
            messaging_api_blob.set_rich_menu_image(
                rich_menu_id=rich_menu_id,
                body=image_data,
                _content_type='image/png'
            )
        print("画像アップロード成功")
        
        # 3. デフォルトのリッチメニューとして設定
        messaging_api.set_default_rich_menu(rich_menu_id)
        print("デフォルトリッチメニューに設定完了")
        
        print("\n✅ 全て完了しました。LINEアプリで確認してください。")

if __name__ == "__main__":
    setup_rich_menu()
