"""リッチメニュー設定・管理"""

import os
import json
import logging
from linebot.v3.messaging import (
    ApiClient,
    MessagingApi,
    Configuration,
    RichMenuRequest,
    RichMenuSize,
    RichMenuArea,
    RichMenuBounds,
    MessageAction,
    URIAction
)

from config import LINE_CHANNEL_ACCESS_TOKEN

logger = logging.getLogger(__name__)


def create_rich_menu(ngrok_url: str):
    """リッチメニューを作成
    
    Args:
        ngrok_url: ngrokの公開URL（例: https://xxxx.ngrok-free.app）
    
    Returns:
        リッチメニューID
    """
    configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
    
    with ApiClient(configuration) as api_client:
        messaging_api = MessagingApi(api_client)
        
        # リッチメニュー定義
        rich_menu = RichMenuRequest(
            size=RichMenuSize(width=2500, height=1686),
            selected=True,
            name="枚方市民ニーズ抽出メニュー",
            chatBarText="メニューを開く",
            areas=[
                # 左上: 対話で意見
                RichMenuArea(
                    bounds=RichMenuBounds(x=0, y=0, width=1250, height=843),
                    action=MessageAction(text="意見を送りたい")
                ),
                # 右上: アンケート（テキスト送信に変更）
                RichMenuArea(
                    bounds=RichMenuBounds(x=1250, y=0, width=1250, height=843),
                    action=MessageAction(text="アンケート")
                ),
                # 左下: ポイント確認
                RichMenuArea(
                    bounds=RichMenuBounds(x=0, y=843, width=1250, height=843),
                    action=MessageAction(text="/point")
                ),
                # 右下: ヘルプ
                RichMenuArea(
                    bounds=RichMenuBounds(x=1250, y=843, width=1250, height=843),
                    action=MessageAction(text="/help")
                ),
            ]
        )
        
        # リッチメニュー作成
        result = messaging_api.create_rich_menu(rich_menu_request=rich_menu)
        rich_menu_id = result.rich_menu_id
        
        logger.info(f"Rich menu created: {rich_menu_id}")
        return rich_menu_id


def upload_rich_menu_image(rich_menu_id: str, image_path: str):
    """リッチメニュー画像をアップロード
    
    Args:
        rich_menu_id: リッチメニューID
        image_path: 画像ファイルのパス
    """
    configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
    
    with ApiClient(configuration) as api_client:
        messaging_api = MessagingApi(api_client)
        
        with open(image_path, 'rb') as image:
            messaging_api.set_rich_menu_image(
                rich_menu_id=rich_menu_id,
                body=image.read(),
                _headers={'Content-Type': 'image/png'}
            )
        
        logger.info(f"Rich menu image uploaded: {rich_menu_id}")


def set_default_rich_menu(rich_menu_id: str):
    """デフォルトリッチメニューを設定
    
    Args:
        rich_menu_id: リッチメニューID
    """
    configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
    
    with ApiClient(configuration) as api_client:
        messaging_api = MessagingApi(api_client)
        messaging_api.set_default_rich_menu(rich_menu_id=rich_menu_id)
        
        logger.info(f"Default rich menu set: {rich_menu_id}")


def delete_rich_menu(rich_menu_id: str):
    """リッチメニューを削除
    
    Args:
        rich_menu_id: リッチメニューID
    """
    configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
    
    with ApiClient(configuration) as api_client:
        messaging_api = MessagingApi(api_client)
        messaging_api.delete_rich_menu(rich_menu_id=rich_menu_id)
        
        logger.info(f"Rich menu deleted: {rich_menu_id}")


if __name__ == "__main__":
    # 使用例
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python rich_menu.py <ngrok_url>")
        print("Example: python rich_menu.py https://xxxx.ngrok-free.app")
        sys.exit(1)
    
    ngrok_url = sys.argv[1].rstrip('/')
    
    # リッチメニュー作成
    menu_id = create_rich_menu(ngrok_url)
    print(f"✓ Rich menu created: {menu_id}")
    
    # 画像パスの指定
    image_path = input("リッチメニュー画像のパスを入力してください（Enter=スキップ）: ").strip()
    
    if image_path and os.path.exists(image_path):
        upload_rich_menu_image(menu_id, image_path)
        print(f"✓ Image uploaded")
    
    # デフォルトに設定
    set_default_rich_menu(menu_id)
    print(f"✓ Set as default menu")
    
    print(f"\nリッチメニューID: {menu_id}")
    print("設定が完了しました！")
