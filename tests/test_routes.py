def test_health_check(client):
    """ヘルスチェックエンドポイントのテスト"""
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'ok'

def test_index_route(client):
    """ルートエンドポイントのテスト"""
    response = client.get('/')
    assert response.status_code == 200
    data = response.get_json()
    assert data['service'] == '枚方市民ニーズ抽出ハイブリッドシステム'

def test_survey_form_display(client):
    """アンケートフォーム表示テスト"""
    # web/survey_form.pyのルート
    response = client.get('/web/survey?user_id=test_user')
    assert response.status_code == 200
    assert b'Survey' in response.data or 'アンケート'.encode('utf-8') in response.data
