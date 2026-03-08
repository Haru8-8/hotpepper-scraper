import requests
from requests.exceptions import RequestException, HTTPError, Timeout
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

def generate_url(base_url, path_list, page=1):
    # ページネーションの制御
    # 1ページ目は通常のURL、2ページ目以降は bgn(ページ数)/ を付与する
    page_str = f"bgn{page}/" if page > 1 else ""
    path_str = "/".join(path_list)

    # URLの組み立て
    url = f"{base_url}/{path_str}/{page_str}"
    return url

def fetch_html(url, headers, timeout=10):
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        # ステータスコードが200以外なら例外を投げる
        response.raise_for_status()
        # サイト側の文字コードを自動判別
        response.encoding = response.apparent_encoding
        return response.text
    except Timeout:
        logging.error(f"タイムアウトしました: {url}")
    except HTTPError as e:
        logging.error(f"HTTPエラーが発生しました: {e}")
    except RequestException as e:
        logging.error(f"通信エラーが発生しました: {e}")
    return None # 失敗時は None を返すことで、呼び出し側で判定できるようにする
    
def fetch_tel_number(detail_url, headers):
    # /tel/ ページへアクセス
    tel_url = detail_url.rstrip('/') + '/tel/'
    html = fetch_html(tel_url, headers)

    if not html:
        return "取得失敗"
    
    # ここで電話番号を抽出（parserの役割だが、シンプルなのでここに含める）
    soup = BeautifulSoup(html, "html.parser")
    tel_element = soup.select_one("p.telephoneNumber")

    return tel_element.get_text(strip=True) if tel_element else "掲載なし"