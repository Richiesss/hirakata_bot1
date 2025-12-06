
import sys
import os
import pandas as pd
import uuid
from datetime import datetime
import re

# パスを通す
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import get_db, User, Opinion, hash_line_user_id

def parse_date(date_str):
    """日付文字列を解析してdatetimeオブジェクトを返す"""
    if pd.isna(date_str):
        return datetime.utcnow()
    
    # 2021.８月 -> 2021-08-01
    try:
        # 全角数字を半角に
        date_str = str(date_str).translate(str.maketrans('０１２３４５６７８９', '0123456789'))
        
        match = re.search(r'(\d{4})[\.\-/年](\d{1,2})', date_str)
        if match:
            year = int(match.group(1))
            month = int(match.group(2))
            return datetime(year, month, 1)
    except Exception:
        pass
        
    return datetime.utcnow()

def import_data(file_path):
    print(f"Reading {file_path}...")
    try:
        df = pd.read_excel(file_path, header=2)
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return

    print(f"Found {len(df)} rows.")
    
    with get_db() as db:
        count = 0
        for index, row in df.iterrows():
            content = row['アンケート内容（テキスト）']
            if pd.isna(content):
                continue
                
            # ユーザー作成 (各行を別々のユーザーとする)
            age_range = row['年代'] if not pd.isna(row['年代']) else None
            gender = row['性別'] if not pd.isna(row['性別']) else None
            
            # ダミーのLINE IDハッシュ生成
            dummy_id = f"excel_import_{uuid.uuid4()}"
            user_hash = hash_line_user_id(dummy_id)
            
            user = User(
                line_user_id_hash=user_hash,
                line_user_id=None, # インポートデータなのでプッシュ不可
                display_name=f"Imported User {index}",
                age_range=str(age_range) if age_range else None,
                district=None # "東部地域"などソースから推測可能だが一旦None
            )
            db.add(user)
            db.flush() # ID取得
            
            # 意見作成
            source = row['Unnamed: 1'] if not pd.isna(row['Unnamed: 1']) else "excel_import"
            date_str = row['Unnamed: 2']
            created_at = parse_date(date_str)
            
            opinion = Opinion(
                user_id=user.id,
                source_type="excel_import",
                content=str(content),
                category=None, # AI分析で後埋め
                created_at=created_at,
                updated_at=created_at
            )
            db.add(opinion)
            
            count += 1
            if count % 100 == 0:
                print(f"Processed {count} rows...")
                
        db.commit()
        print(f"Successfully imported {count} opinions.")

if __name__ == "__main__":
    file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'interview.xlsx')
    if os.path.exists(file_path):
        import_data(file_path)
    else:
        print(f"File not found: {file_path}")
