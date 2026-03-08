import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Set, Optional, Any, Generator

import pandas as pd
from bs4 import BeautifulSoup

from scraper import generate_url, fetch_html, fetch_tel_number
from parser import parse_list_page

# エリア階層の定義（マスターデータのキーに対応）
AREA_LEVELS = ["large_area", "middle_area", "detail_area"]

class HotPepperScraper:
    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.logger = self._setup_logger()
        self.csv_file = "shop_list.csv"
        self.seen_shop_ids: Set[str] = self._load_seen_ids()
        self.total_shops_count = len(self.seen_shop_ids)

    def _load_config(self, path: str) -> Dict:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("Scraper")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            # コンソール出力
            sh = logging.StreamHandler()
            sh.setFormatter(formatter)
            logger.addHandler(sh)
            # ファイル出力
            fh = logging.FileHandler('scraper.log', encoding='utf-8')
            fh.setFormatter(formatter)
            logger.addHandler(fh)
        return logger

    def _load_seen_ids(self) -> Set[str]:
        """既存CSVから取得済みURLを読み込む"""
        if not os.path.exists(self.csv_file):
            return set()
        try:
            df = pd.read_csv(self.csv_file)
            return set(df["detail_url"].dropna().unique()) if "detail_url" in df.columns else set()
        except Exception as e:
            self.logger.error(f"履歴読み込み失敗: {e}")
            return set()

    def find_path_to_key(self, current_struct: Any, target_key: str, current_path: List[str] = []) -> Optional[List[str]]:
        """ターゲットエリアまでの名前のリスト（パス）を再帰的に探す"""
        if isinstance(current_struct, dict):
            if target_key in current_struct:
                return current_path + [target_key]
            for key, value in current_struct.items():
                result = self.find_path_to_key(value, target_key, current_path + [key])
                if result: return result
        elif isinstance(current_struct, list):
            if target_key in current_struct:
                return current_path + [target_key]
        return None

    def get_leaf_paths(self, node: Any, base_path: List[str]) -> Generator[List[str], None, None]:
        """
        ノードから末端までのパスを生成。
        nodeが文字列（末端）なら現在のパスを返し、リストや辞書ならさらに潜る。
        """
        if isinstance(node, dict):
            for key, value in node.items():
                yield from self.get_leaf_paths(value, base_path + [key])
        elif isinstance(node, list):
            for leaf in node:
                yield base_path + [leaf]
        else:
            yield base_path

    def resolve_ids(self, path_names: List[str], genre_key: str) -> Optional[List[str]]:
        """エリア名のリストをIDのリストに変換する"""
        master = self.config.get("master", {})
        ids = []
        try:
            for i, name in enumerate(path_names):
                category = AREA_LEVELS[i] if i < len(AREA_LEVELS) else "detail_area"
                ids.append(master[category][name])
            
            # ジャンルIDの追加
            ids.append(master.get("genres", {})[genre_key])
            return ids
        except KeyError as e:
            self.logger.warning(f"ID変換に失敗しました（マスター未登録）: {e}")
            return None

    def save_to_csv(self, shops: List[Dict]):
        """データをCSVに追記保存する"""
        if not shops:
            return
        df = pd.DataFrame(shops)
        is_new = not os.path.exists(self.csv_file)
        df.to_csv(self.csv_file, mode='a', header=is_new, index=False, encoding="utf_8_sig")

    def scrape_area(self, path_ids: List[str]):
        """特定エリアの全ページを巡回する"""
        base_url = self.config["system"]["base_url"]
        headers = self.config["system"]["headers"]
        max_pages = self.config["constraints"]["max_pages"]
        max_shops = self.config["constraints"]["max_shops"]

        for page in range(1, max_pages + 1):
            if self.total_shops_count >= max_shops:
                self.logger.info("最大取得件数に達しました。")
                return

            url = generate_url(base_url, path_ids, page)
            self.logger.info(f"Page {page}: 取得開始 {url}")

            html = fetch_html(url, headers)
            if not html: break

            shops = parse_list_page(html, url)
            if not shops: break

            new_shops_this_page = []
            for shop in shops:
                shop_id = shop["detail_url"]
                if shop_id in self.seen_shop_ids:
                    continue

                # 個別情報の取得（電話番号など）
                self.logger.info(f"  - 店舗詳細取得中: {shop['name']}")
                shop['tel'] = fetch_tel_number(base_url + shop_id, headers)
                
                self.seen_shop_ids.add(shop_id)
                new_shops_this_page.append(shop)
                self.total_shops_count += 1
                time.sleep(1.5) # 負荷対策

            self.save_to_csv(new_shops_this_page)
            
            # 次ページ判定
            if f"bgn{page+1}/" not in html:
                self.logger.info("最終ページです。")
                break
            time.sleep(1.5)

    def run(self):
        """全体の実行フロー管理"""
        self.logger.info("=== スクレイピングプロセス開始 ===")
        
        target_root = self.config["search"]["target_area_key"]
        target_genre = self.config["search"]["target_genre_key"]

        # 1. ターゲットエリアのノードを特定
        root_path = self.find_path_to_key(self.config["hierarchy"], target_root)
        if not root_path:
            self.logger.error(f"エリア '{target_root}' が hierarchy に見つかりません")
            return

        # 2. 階層を下って対象の末端ノードを取得
        current_node = self.config["hierarchy"]
        for key in root_path:
            if isinstance(current_node, dict) and key in current_node:
                current_node = current_node[key]
            elif isinstance(current_node, list) and key in current_node:
                # リストの中にターゲット（小エリア名）がある場合
                current_node = key # 文字列そのものをセット
                break

        print(current_node)
        print(root_path)

        # 3. 末端パスを一つずつ処理
        for leaf_path in self.get_leaf_paths(current_node, root_path):
            path_ids = self.resolve_ids(leaf_path, target_genre)
            if path_ids:
                self.logger.info(f"巡回ルート確定: {' -> '.join(leaf_path)} (IDs: {path_ids})")
                self.scrape_area(path_ids)

        self.logger.info(f"完了。合計取得件数: {self.total_shops_count}件")

if __name__ == "__main__":
    scraper = HotPepperScraper("config.json")
    scraper.run()