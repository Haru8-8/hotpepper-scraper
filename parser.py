from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

def parse_list_page(html, url):
    soup = BeautifulSoup(html, "html.parser")
    shops = []

    # 各店舗のコンテナを全取得
    containers = soup.select('div.shopDetailTop')

    for container in containers:
        try:
            # 店舗名の抽出
            a_tag = container.select_one("h3.shopDetailStoreName > a")

            # エリア、ジャンルなどの情報はここからさらに取得
            # 例: area = container.select_one('.area_class_name').text
            p_tag = container.select_one("p.parentGenreName")
            if p_tag:
                genre, area = parse_genre_area(p_tag.get_text())
            else:
                genre = ""
                area = ""

            shops.append({
                "name": a_tag.get_text(strip=True) if a_tag else "店舗名取得失敗",
                "detail_url": a_tag.get("href") if a_tag else "",
                "area": area,
                "genre": genre,
                "source_url": url,
            })
        except Exception as e:
            logging.error(f"店舗データの解析に失敗しました。スキップします: {e}")
            continue
    return shops

def parse_genre_area(text):
    # 区切り文字が複数パターンある場合は置換してから split する
    clean_text = text.replace('|', '｜') 
    parts = clean_text.split('｜')
    
    # ちゃんと2つに分かれたか確認してから返す
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    else:
        # 分割できなかった場合のフォールバック（例：ジャンルだけ返してエリアは空にする）
        return parts[0].strip(), ""