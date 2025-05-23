"""
テレビ用天気予報ナレーション原稿生成モジュール
複数情報源から収集した天気データから、テレビ用の天気予報原稿を生成します。
アナウンサーが読みやすい自然な話し言葉で、2分程度の適切な長さに調整します。
文章の流れ、リズム、間を意識し、聞き手に伝わりやすい原稿を生成します。
"""

import json
import datetime
import random
import re
from typing import Dict, List, Any, Optional

class ScriptGenerator:
    """天気予報原稿を生成するクラス"""
    
    def __init__(self):
        # 2分間の読み上げに適した文字数（目安）
        self.target_char_count = 500
        
        # 天気表現のマッピング（簡潔で読みやすい表現に厳選）
        self.weather_expressions = {
            # 晴れ系
            "100": ["青空が広がり", "晴れ渡った空の下", "日差しが降り注ぎ", "澄み切った青空に"],
            "101": ["晴れ間が広がり", "時おり雲が現れ", "おおむね晴れて", "晴れ時々曇りで"],
            "110": ["晴れの天気で", "日差しが感じられ", "晴れ模様で", "日が差す天気に"],
            "111": ["晴れ間が見え", "時おり雲が広がり", "晴れたり曇ったりの天気で", "晴れ時々曇りで"],
            "112": ["晴れ間が見え", "雨の合間に晴れ間が広がり", "晴れ間も出て", "雨上がりの晴れ間が"],
            "115": ["晴れ間が見え", "雪の合間に晴れ間が広がり", "晴れ間も出て", "雪の晴れ間が"],
            
            # 曇り系
            "200": ["雲が広がり", "曇り空で", "雲に覆われ", "グレーの雲に包まれ"],
            "201": ["雲が多く", "やや曇り気味で", "曇り時々晴れで", "雲の多い天気に"],
            "202": ["雲が広がり", "曇り一時雨で", "雨の降る可能性があり", "雨雲が近づいて"],
            "203": ["雪雲が広がり", "曇り一時雪で", "雪の降る可能性があり", "雪雲が近づいて"],
            "204": ["曇り時々雨で", "雨の降る時間帯もあり", "雨雲が通過し", "雨の降ったり止んだりで"],
            "205": ["曇り時々雪で", "雪の降る時間帯もあり", "雪雲が通過し", "雪の降ったり止んだりで"],
            "206": ["曇り一時雨か雪で", "雨や雪の可能性があり", "天気が不安定で", "雨や雪が混じり"],
            "207": ["曇り一時雨や雷雨で", "雷を伴う雨の可能性があり", "雷雨の恐れがあり", "激しい雨の可能性も"],
            "208": ["曇り一時雪や雷雪で", "雷を伴う雪の可能性があり", "雷雪の恐れがあり", "激しい雪の可能性も"],
            "209": ["霧が発生し", "視界不良となり", "霧に包まれ", "霧で見通しが悪く"],
            "210": ["曇りがちで", "雲の多い天気で", "どんよりとした空で", "薄暗い雲に覆われ"],
            "211": ["曇り時々晴れで", "晴れ間も見られ", "雲の切れ間から青空が顔を出し", "雲の多い中でも晴れ間が"],
            "212": ["曇り後雨となり", "次第に雨の降る天気に変わり", "雨雲が近づき", "雨の予報となって"],
            "213": ["曇り後雪となり", "次第に雪の降る天気に変わり", "雪雲が近づき", "雪の予報となって"],
            "214": ["曇り後雨か雪となり", "雨や雪に変わり", "天気が崩れ", "雨や雪の予報となって"],
            "215": ["曇り後雨や雷雨となり", "雷雨に変わる可能性があり", "激しい雨に変わり", "雷を伴う雨の予報となって"],
            "216": ["曇り後雪や雷雪となり", "雷雪に変わる可能性があり", "激しい雪に変わり", "雷を伴う雪の予報となって"],
            "217": ["曇り後霧が発生し", "霧が発生する見込みで", "視界不良になり", "霧に包まれる予報となって"],
            "218": ["曇り後晴れて", "次第に晴れ", "雲が晴れて", "晴れ間が広がり"],
            "219": ["曇り昼頃から雨となり", "昼頃から雨の降る天気に変わり", "午後は雨模様となり", "昼過ぎから雨が降り出し"],
            "220": ["曇り夕方から雨となり", "夕方から雨の降る天気に変わり", "夜は雨模様となり", "夕刻から雨が降り出し"],
            "221": ["曇り夜は雨となり", "夜になると雨が降り出し", "夜間は雨の予報となり", "夜から雨模様となり"],
            
            # 雨系
            "300": ["雨が降り", "雨模様となり", "傘が必要で", "雨の一日となり"],
            "301": ["雨時々晴れで", "雨の合間に晴れ間が見え", "にわか雨となり", "晴れ間もある雨で"],
            "302": ["雨時々止み", "断続的な雨となり", "雨が降ったり止んだりで", "雨脚が強まったり弱まったりし"],
            "303": ["雨時々雪が混じり", "雨と雪が入り混じり", "雨や雪が降り", "雨と雪が混ざり"],
            "304": ["雨か雪が降り", "雨または雪となり", "雨や雪の可能性があり", "雨と雪の境界となり"],
            "306": ["大雨となり", "激しい雨が降り", "土砂災害に警戒が必要で", "河川の増水に注意が必要で"],
            "308": ["雷を伴う雨が降り", "雷雨となり", "激しい雨と雷が発生し", "雷鳴の響く雨となり"],
            "309": ["暴風を伴う雨が降り", "暴風雨となり", "強風と雨が吹き付け", "風雨が強まり"],
            "311": ["雨後晴れて", "雨上がりの晴天となり", "雨の後は晴れ", "雨が止んで晴れ"],
            "313": ["雨後曇りとなり", "雨が止んで曇り", "雨上がりの曇天となり", "雨の後は曇り空となり"],
            "314": ["雨後雪に変わり", "雨から雪に変わり", "雨が雪に変わり", "雨の後は雪となり"],
            "315": ["雨や雷雨の後晴れて", "雷雨の後は晴れ", "激しい雨の後は晴天となり", "雷雨が過ぎ去り晴れ"],
            "316": ["雨や雷雨の後曇りとなり", "雷雨の後は曇り", "激しい雨の後は曇天となり", "雷雨が過ぎ去り曇り"],
            "317": ["雨や雷雨の後雪となり", "雷雨の後は雪", "激しい雨の後は雪となり", "雷雨が過ぎ去り雪に変わり"],
            "320": ["朝の内雨の後晴れて", "朝は雨、その後晴れ", "午前中は雨、午後は晴れて", "朝の雨は上がり晴れ"],
            "321": ["朝の内雨の後曇りとなり", "朝は雨、その後曇り", "午前中は雨、午後は曇りとなり", "朝の雨は上がり曇り"],
            
            # 雪系
            "400": ["雪が降り", "雪模様となり", "雪が舞い", "雪の一日となり"],
            "401": ["雪時々晴れで", "雪の合間に晴れ間が見え", "にわか雪となり", "晴れ間もある雪で"],
            "402": ["雪時々止み", "断続的な雪となり", "雪が降ったり止んだりで", "雪の強さが変わり"],
            "403": ["雪時々雨が混じり", "雪と雨が入り混じり", "みぞれとなり", "雪と雨が混ざり"],
            "405": ["大雪となり", "激しい雪が降り", "積雪に警戒が必要で", "交通障害に注意が必要で"],
            "406": ["風雪が強まり", "吹雪となり", "地吹雪となり", "視界不良に注意が必要で"],
            "407": ["暴風雪となり", "猛吹雪となり", "外出危険な状況となり", "厳重な警戒が必要で"],
            "409": ["雷を伴う雪が降り", "雷雪となり", "雷を伴う雪となり", "雷鳴の響く雪となり"],
            "411": ["雪後晴れて", "雪上がりの晴天となり", "雪の後は晴れ", "雪が止んで晴れ"],
            "413": ["雪後曇りとなり", "雪が止んで曇り", "雪上がりの曇天となり", "雪の後は曇り空となり"],
            "414": ["雪後雨に変わり", "雪から雨に変わり", "雪が雨に変わり", "雪の後は雨となり"],
            "420": ["朝の内雪の後晴れて", "朝は雪、その後晴れ", "午前中は雪、午後は晴れて", "朝の雪は上がり晴れ"],
            "421": ["朝の内雪の後曇りとなり", "朝は雪、その後曇り", "午前中は雪、午後は曇りとなり", "朝の雪は上がり曇り"],
            "422": ["朝の内雪の後雨となり", "朝は雪、その後雨", "午前中は雪、午後は雨となり", "朝の雪は上がり雨に変わり"],
        }
        
        # 天気の傾向を表す表現（読みやすく自然な表現に厳選）
        self.weather_trend_expressions = {
            "sunny_to_cloudy": ["次第に雲が広がり", "晴れから曇りに変わり", "晴れの後曇りに転じ", "晴れ間が少なくなり"],
            "cloudy_to_sunny": ["雲が晴れて", "曇りから晴れに変わり", "次第に晴れ間が広がり", "雲が少なくなり"],
            "cloudy_to_rainy": ["雨雲が近づき", "次第に雨の降る所が多くなり", "天気が下り坂となり", "雨の降る地域が広がり"],
            "rainy_to_cloudy": ["雨は次第に上がり", "雨雲が遠ざかり", "雨は止んで", "雨の降る地域が減り"],
            "getting_colder": ["気温が下がり", "寒気が入り", "冷え込みが強まり", "気温が低下し"],
            "getting_warmer": ["気温が上がり", "暖かい空気に覆われ", "気温が上昇し", "暖かさが増し"]
        }
        
        # 季節感を表す表現（簡潔で読みやすい表現に厳選）
        self.seasonal_expressions = {
            "spring": ["春らしい陽気", "春の訪れ", "春めいた天気", "春風が心地よい季節"],
            "summer": ["夏らしい暑さ", "夏空", "真夏日となる所も", "熱中症に注意が必要な暑さ"],
            "autumn": ["秋らしい爽やかさ", "秋の気配", "秋晴れ", "秋の深まり"],
            "winter": ["冬らしい冷え込み", "冬の厳しさ", "冬本番の寒さ", "冬の冷たい空気"]
        }
        
        # 時間帯を表す表現（簡潔で読みやすい表現に厳選）
        self.time_expressions = {
            "morning": ["朝は", "朝方は", "早朝は", "午前中は"],
            "afternoon": ["昼頃は", "午後は", "日中は", "昼間は"],
            "evening": ["夕方は", "夕刻は", "夕暮れ時は", "日没頃は"],
            "night": ["夜は", "夜間は", "夜遅くは", "深夜は"]
        }
        
        # 文末表現（読みやすく自然な表現に厳選）
        self.polite_endings = [
            "でしょう",
            "となるでしょう",
            "見込みです",
            "予想されます",
            "になりそうです",
            "となりそうです",
            "のようです",
            "ようです",
            "見通しです"
        ]
        
        # 接続詞・接続表現（読みやすく自然な表現に厳選）
        self.conjunctions = [
            "また、",
            "そして、",
            "一方、",
            "さらに、",
            "なお、",
            "続いて、",
            "次に、"
        ]
        
        # 注意喚起表現（簡潔で読みやすい表現に厳選）
        self.caution_expressions = [
            "お出かけの際は{item}にご注意ください",
            "{item}にはくれぐれもご注意ください",
            "{item}には十分お気をつけください",
            "{item}に対する備えをお願いします"
        ]
        
        # 注意項目（簡潔で読みやすい表現に厳選）
        self.caution_items = {
            "rain": ["傘の準備", "足元の濡れ", "路面の滑りやすさ", "雨の強まり"],
            "snow": ["路面の凍結", "積雪", "視界不良", "転倒"],
            "wind": ["強風", "飛ばされやすいもの", "突風", "風の強まり"],
            "heat": ["熱中症", "水分補給", "直射日光", "体調管理"],
            "cold": ["防寒対策", "凍結", "体温管理", "乾燥"]
        }
        
        # 挨拶表現（簡潔で読みやすい表現に厳選）
        self.greeting_expressions = [
            "皆さん、こんにちは",
            "お天気の時間です",
            "それでは天気予報をお伝えします",
            "今日の天気をお伝えします"
        ]
        
        # 締めくくり表現（簡潔で読みやすい表現に厳選）
        self.closing_expressions = [
            "以上、天気予報でした",
            "今日もお天気に気をつけてお過ごしください",
            "最新の気象情報にご注意ください",
            "お出かけの際は天気の変化にご注意ください"
        ]
        
        # 現在の季節を判定
        now = datetime.datetime.now()
        month = now.month
        
        if 3 <= month <= 5:
            self.current_season = "spring"
        elif 6 <= month <= 8:
            self.current_season = "summer"
        elif 9 <= month <= 11:
            self.current_season = "autumn"
        else:
            self.current_season = "winter"
    
    def _get_random_expression(self, expressions_list):
        """リストからランダムに表現を選択"""
        return random.choice(expressions_list)
    
    def _get_weather_expression(self, weather_code):
        """天気コードに対応する表現を取得"""
        if weather_code in self.weather_expressions:
            return self._get_random_expression(self.weather_expressions[weather_code])
        return "天気が変わり"
    
    def _get_polite_ending(self):
        """丁寧な文末表現を取得"""
        return self._get_random_expression(self.polite_endings)
    
    def _get_conjunction(self):
        """接続詞を取得"""
        return self._get_random_expression(self.conjunctions)
    
    def _get_caution_expression(self, caution_type):
        """注意喚起表現を取得"""
        if caution_type in self.caution_items:
            item = self._get_random_expression(self.caution_items[caution_type])
            template = self._get_random_expression(self.caution_expressions)
            return template.format(item=item)
        return ""
    
    def _format_sentence(self, text):
        """
        文章を読みやすく整形する
        - 長すぎる文は分割
        - 適切な間を挿入
        - 読点の位置を調整
        """
        # 文末に「。」がない場合は追加
        if not text.endswith("。"):
            text += "。"
        
        # 長すぎる文を分割（30文字以上で読点がない場合）
        sentences = []
        for sentence in text.split("。"):
            if not sentence:  # 空文字列はスキップ
                continue
                
            # 長い文で読点がない場合は適切な位置に読点を追加
            if len(sentence) > 30 and "、" not in sentence:
                # 助詞や接続詞の後に読点を追加
                for pos in range(15, len(sentence) - 5):
                    if sentence[pos-1:pos+1] in ["は", "が", "を", "に", "で", "と", "も", "や"]:
                        sentence = sentence[:pos+1] + "、" + sentence[pos+1:]
                        break
            
            sentences.append(sentence + "。")
        
        return "".join(sentences)
    
    def _adjust_text_length(self, text, target_length):
        """テキストの長さを調整する"""
        current_length = len(text)
        
        # 長すぎる場合は短くする
        if current_length > target_length * 1.2:
            sentences = text.split("。")
            # 最後の空文字列を削除
            if sentences and not sentences[-1]:
                sentences.pop()
                
            # 文章数を減らして調整
            while len("。".join(sentences) + "。") > target_length and len(sentences) > 1:
                # 重要度の低い文を削除（ここでは単純に真ん中あたりの文を削除）
                middle_index = len(sentences) // 2
                sentences.pop(middle_index)
            
            return "。".join(sentences) + "。"
        
        # 短すぎる場合は補足情報を追加
        elif current_length < target_length * 0.8:
            # 季節に応じた表現を追加
            seasonal_expr = self._get_random_expression(self.seasonal_expressions[self.current_season])
            
            # 文末の「。」を除去して追加文を連結
            if text.endswith("。"):
                text = text[:-1]
            
            additional_text = f"。{self._get_conjunction()}{seasonal_expr}を感じる一日となりそうです。"
            return text + additional_text
        
        return text
    
    def _determine_forecast_day(self):
        """
        現在時刻に基づいて予報対象日を決定する
        0-12時は当日、12時以降は翌日を対象とする
        
        Returns:
            tuple: (当日キー, 翌日キー, 予報対象日の表現)
        """
        now = datetime.datetime.now()
        hour = now.hour
        
        if hour < 12:
            # 0-12時は当日を対象
            return "today", "tomorrow", "今日"
        else:
            # 12時以降は翌日を対象
            return "tomorrow", "day_after_tomorrow", "明日"
    
    def generate_current_national_overview(self, weather_data):
        """
        現在の全国天気の概況を生成
        
        Args:
            weather_data: 天気データ
            
        Returns:
            str: 全国の天気概況
        """
        try:
            # 予報対象日を決定
            target_day, next_day, day_expression = self._determine_forecast_day()
            
            # 挨拶から始める
            greeting = self._get_random_expression(self.greeting_expressions)
            
            overview = weather_data["overview"][target_day]
            
            # 地域ごとの天気パターンをカウント
            weather_patterns = {}
            for region, data in overview.items():
                weather = data["weather"]
                weather_code = data["code"]
                
                # 主要な天気パターンを抽出（晴れ、曇り、雨、雪など）
                pattern = "その他"
                if "晴" in weather:
                    pattern = "晴れ"
                elif "曇" in weather:
                    pattern = "曇り"
                elif "雨" in weather:
                    pattern = "雨"
                elif "雪" in weather:
                    pattern = "雪"
                
                if pattern not in weather_patterns:
                    weather_patterns[pattern] = []
                weather_patterns[pattern].append(region)
            
            # 天気パターンごとの地域をまとめる
            pattern_texts = []
            for pattern, regions in weather_patterns.items():
                if len(regions) > 0:
                    if len(regions) >= 3:  # 多くの地域で同じ天気の場合
                        if len(regions) >= 7:  # ほぼ全国的な天気の場合
                            pattern_texts.append(f"全国的に{pattern}の天気")
                        else:
                            regions_text = "、".join(regions[:2]) + "など"
                            pattern_texts.append(f"{regions_text}では{pattern}")
                    else:
                        regions_text = "、".join(regions)
                        pattern_texts.append(f"{regions_text}では{pattern}")
            
            # 天気概況文を生成
            if pattern_texts:
                overview_text = f"{greeting}。{day_expression}の天気は、" + "、".join(pattern_texts) + f"となっています。"
                
                # 季節感を追加（自然な流れになるよう接続詞を使用）
                seasonal_expr = self._get_random_expression(self.seasonal_expressions[self.current_season])
                overview_text += f"{self._get_conjunction()}{seasonal_expr}を感じる一日となりそうです。"
                
                return self._format_sentence(overview_text)
            else:
                return self._format_sentence(f"{greeting}。{day_expression}の天気は地域によって変化があります。お出かけの際は最新の天気予報をご確認ください。")
                
        except Exception as e:
            print(f"Error generating current_national_overview: {e}")
            return self._format_sentence(f"{self._get_random_expression(self.greeting_expressions)}。今日の天気は地域によって様々です。お出かけの際は最新の天気予報をご確認ください。")
    
    def generate_future_points(self, weather_data):
        """
        今後の天気のポイントを生成
        
        Args:
            weather_data: 天気データ
            
        Returns:
            str: 今後の天気のポイント
        """
        try:
            # 予報対象日を決定
            target_day, next_day, day_expression = self._determine_forecast_day()
            
            # 警報・注意報情報を取得
            warnings = weather_data.get("warnings", [])
            
            # 翌日の天気概況を取得
            next_day_overview = weather_data["overview"][next_day]
            
            points_text = "今後の天気のポイントをお伝えします。"
            
            # 警報・注意報がある場合
            if warnings:
                warnings_text = "、".join(warnings[:2])
                if len(warnings) > 2:
                    warnings_text += "など"
                
                points_text += f" {warnings_text}が発表されています。十分ご注意ください。"
            
            # 翌日の天気の特徴を抽出
            next_day_patterns = {}
            for region, data in next_day_overview.items():
                weather = data["weather"]
                
                pattern = "その他"
                if "晴" in weather:
                    pattern = "晴れ"
                elif "曇" in weather:
                    pattern = "曇り"
                elif "雨" in weather:
                    pattern = "雨"
                elif "雪" in weather:
                    pattern = "雪"
                
                if pattern not in next_day_patterns:
                    next_day_patterns[pattern] = []
                next_day_patterns[pattern].append(region)
            
            # 翌日の天気の傾向
            if next_day_patterns:
                if "今後の天気のポイントをお伝えします。" != points_text:
                    points_text += f" {self._get_conjunction()}"
                
                # 最も多い天気パターンを特定
                max_pattern = max(next_day_patterns.items(), key=lambda x: len(x[1]))
                pattern, regions = max_pattern
                
                next_day_expression = "明日" if target_day == "today" else "明後日"
                
                if len(regions) >= 7:  # ほぼ全国的
                    points_text += f"{next_day_expression}は全国的に{pattern}の天気となる見込みです。"
                else:
                    regions_text = "、".join(regions[:2])
                    if len(regions) > 2:
                        regions_text += "など"
                    points_text += f"{next_day_expression}は{regions_text}を中心に{pattern}の天気となる見込みです。"
            
            # 注意事項を追加
            if "雨" in str(next_day_patterns.keys()):
                points_text += f" {self._get_caution_expression('rain')}。"
            elif "雪" in str(next_day_patterns.keys()):
                points_text += f" {self._get_caution_expression('snow')}。"
            elif self.current_season == "summer":
                points_text += f" {self._get_caution_expression('heat')}。"
            elif self.current_season == "winter":
                points_text += f" {self._get_caution_expression('cold')}。"
            
            return self._format_sentence(points_text)
            
        except Exception as e:
            print(f"Error generating future_points: {e}")
            return self._format_sentence("今後の天気の変化にご注意ください。最新の気象情報をこまめに確認することをおすすめします。")
    
    def generate_national_weather(self, weather_data):
        """
        全国の天気を生成
        
        Args:
            weather_data: 天気データ
            
        Returns:
            str: 全国の天気
        """
        try:
            # 予報対象日を決定
            target_day, next_day, day_expression = self._determine_forecast_day()
            
            # 対象日の天気概況
            target_overview = weather_data["overview"][target_day]
            
            # 地域ごとの天気をまとめる
            region_groups = {
                "北日本": ["北海道", "東北"],
                "東日本": ["関東甲信", "北陸", "東海"],
                "西日本": ["近畿", "中国", "四国", "九州"],
                "沖縄": ["沖縄"]
            }
            
            region_weather = {}
            for group_name, regions in region_groups.items():
                weather_codes = []
                for region in regions:
                    if region in target_overview:
                        weather_codes.append(target_overview[region]["code"])
                
                if weather_codes:
                    # 最も多い天気コードを代表として使用
                    code_counts = {}
                    for code in weather_codes:
                        if code not in code_counts:
                            code_counts[code] = 0
                        code_counts[code] += 1
                    
                    most_common_code = max(code_counts.items(), key=lambda x: x[1])[0]
                    region_weather[group_name] = most_common_code
            
            # 地域ごとの天気を文章化
            weather_texts = []
            for group_name, weather_code in region_weather.items():
                weather_expr = self._get_weather_expression(weather_code)
                weather_texts.append(f"{group_name}は{weather_expr}ます")
            
            # 全国の天気文を生成
            if weather_texts:
                national_text = f"全国の天気をお伝えします。{day_expression}は" + "。".join(weather_texts) + "。"
                
                # 気温の傾向を追加
                if self.current_season in ["spring", "summer"]:
                    national_text += f"気温は平年並みから高めで推移する見込みです。"
                else:
                    national_text += f"気温は平年並みから低めで推移する見込みです。"
                
                return self._format_sentence(national_text)
            else:
                return self._format_sentence("全国的に天気は変化しています。各地の最新の気象情報にご注意ください。")
                
        except Exception as e:
            print(f"Error generating national weather: {e}")
            return self._format_sentence("全国的に天気は変化しています。各地の最新の気象情報にご注意ください。")
    
    def generate_national_temperature(self, weather_data):
        """
        全国の気温情報を生成
        
        Args:
            weather_data: 天気データ
            
        Returns:
            str: 全国の気温情報
        """
        try:
            # 予報対象日を決定
            target_day, next_day, day_expression = self._determine_forecast_day()
            
            # 気温データ
            target_temp = weather_data["temperature"][target_day]
            next_day_temp = weather_data["temperature"][next_day]
            
            # 代表的な地域の気温を抽出
            key_regions = ["関東甲信", "北海道", "沖縄"]
            temp_texts = []
            
            for region in key_regions:
                if region in target_temp and region in next_day_temp:
                    target_max = target_temp[region].get("max")
                    next_day_max = next_day_temp[region].get("max")
                    next_day_min = next_day_temp[region].get("min")
                    
                    next_day_expression = "明日" if target_day == "today" else "明後日"
                    
                    if target_max and next_day_max:
                        # 気温の変化を表現
                        if int(next_day_max) > int(target_max):
                            temp_texts.append(f"{region}地方は{next_day_expression}の最高気温が{next_day_max}度まで上昇")
                        elif int(next_day_max) < int(target_max):
                            temp_texts.append(f"{region}地方は{next_day_expression}の最高気温が{next_day_max}度まで下降")
                        else:
                            temp_texts.append(f"{region}地方は{next_day_expression}も最高気温が{next_day_max}度")
            
            # 全国の気温傾向
            if self.current_season == "summer":
                general_trend = "全国的に気温が高く、熱中症対策が必要な一日となりそうです。"
            elif self.current_season == "winter":
                general_trend = "全国的に気温が低く、防寒対策をしっかりと行ってください。"
            else:
                general_trend = "全国的に気温は平年並みからやや高めで推移する見込みです。"
            
            # 気温情報を文章化
            if temp_texts:
                temp_text = "気温についてお伝えします。" + "。".join(temp_texts) + "する見込みです。"
                temp_text += f" {general_trend}"
                return self._format_sentence(temp_text)
            else:
                return self._format_sentence(general_trend)
                
        except Exception as e:
            print(f"Error generating national temperature: {e}")
            return self._format_sentence("全国的に気温は平年並みで推移する見込みです。急な気温変化にはご注意ください。")
    
    def generate_weekly_forecast(self, weather_data):
        """
        週間天気予報を生成
        
        Args:
            weather_data: 天気データ
            
        Returns:
            str: 週間天気予報
        """
        try:
            weekly = weather_data.get("weekly", {})
            
            if not weekly:
                return self._format_sentence("週間予報については、明日以降も天気の変化にご注意ください。最新の気象情報をこまめに確認することをおすすめします。")
            
            # 週間天気の傾向を分析
            sunny_days = 0
            rainy_days = 0
            cloudy_days = 0
            
            for date, data in weekly.items():
                weather_code = data.get("weather_code", "")
                if weather_code.startswith("1"):  # 晴れ系
                    sunny_days += 1
                elif weather_code.startswith("2"):  # 曇り系
                    cloudy_days += 1
                elif weather_code.startswith("3") or weather_code.startswith("4"):  # 雨系または雪系
                    rainy_days += 1
            
            # 週間天気の傾向を文章化
            trend_text = "週間予報をお伝えします。"
            
            # 天気の傾向
            total_days = sunny_days + rainy_days + cloudy_days
            if total_days > 0:
                if sunny_days > total_days / 2:
                    trend_text += "週間を通して晴れの天気が多くなりそうです。"
                elif rainy_days > total_days / 2:
                    trend_text += "週間を通して雨や雪の天気が多くなりそうです。"
                elif cloudy_days > total_days / 2:
                    trend_text += "週間を通して曇りの天気が多くなりそうです。"
                else:
                    trend_text += "週間を通して天気は変わりやすく、晴れや曇り、雨の天気が入れ替わる見込みです。"
            
            # 気温の傾向
            if self.current_season in ["spring", "summer"]:
                trend_text += "気温は平年並みからやや高めで推移する見込みです。"
            else:
                trend_text += "気温は平年並みからやや低めで推移する見込みです。"
            
            # 注意事項
            if rainy_days > 0:
                trend_text += f" {self._get_caution_expression('rain')}。"
            elif self.current_season == "summer":
                trend_text += f" {self._get_caution_expression('heat')}。"
            elif self.current_season == "winter":
                trend_text += f" {self._get_caution_expression('cold')}。"
            
            # 締めくくり
            trend_text += f" {self._get_random_expression(self.closing_expressions)}。"
            
            return self._format_sentence(trend_text)
            
        except Exception as e:
            print(f"Error generating weekly forecast: {e}")
            return self._format_sentence("週間予報については、明日以降も天気の変化にご注意ください。最新の気象情報をこまめに確認することをおすすめします。")
    
    def generate_complete_script(self, weather_data):
        """
        完全な天気予報原稿を生成
        
        Args:
            weather_data: 天気データ
            
        Returns:
            Dict[str, str]: 各セクションの原稿
        """
        # 予報対象日を決定
        target_day, next_day, day_expression = self._determine_forecast_day()
        
        # 各セクションの原稿を生成（メニュー順序：現在の全国天気の概況→今後のポイント→全国天気→全国気温→週間予報）
        current_national_overview = self.generate_current_national_overview(weather_data)
        future_points = self.generate_future_points(weather_data)
        national_weather = self.generate_national_weather(weather_data)
        national_temperature = self.generate_national_temperature(weather_data)
        weekly_forecast = self.generate_weekly_forecast(weather_data)
        
        # 各セクションの文字数を計算
        char_counts = {
            "現在の全国天気の概況": len(current_national_overview),
            "今後のポイント": len(future_points),
            "全国天気": len(national_weather),
            "全国気温": len(national_temperature),
            "週間予報": len(weekly_forecast)
        }
        
        # 合計文字数
        total_chars = sum(char_counts.values())
        
        # 目標文字数に調整
        if total_chars > self.target_char_count * 1.2:
            # 長すぎる場合は各セクションを短くする
            for section in char_counts.keys():
                if section == "現在の全国天気の概況":
                    current_national_overview = self._adjust_text_length(current_national_overview, int(self.target_char_count * 0.2))
                elif section == "今後のポイント":
                    future_points = self._adjust_text_length(future_points, int(self.target_char_count * 0.2))
                elif section == "全国天気":
                    national_weather = self._adjust_text_length(national_weather, int(self.target_char_count * 0.2))
                elif section == "全国気温":
                    national_temperature = self._adjust_text_length(national_temperature, int(self.target_char_count * 0.2))
                elif section == "週間予報":
                    weekly_forecast = self._adjust_text_length(weekly_forecast, int(self.target_char_count * 0.2))
        elif total_chars < self.target_char_count * 0.8:
            # 短すぎる場合は各セクションを長くする
            for section in char_counts.keys():
                if section == "現在の全国天気の概況":
                    current_national_overview = self._adjust_text_length(current_national_overview, int(self.target_char_count * 0.2))
                elif section == "今後のポイント":
                    future_points = self._adjust_text_length(future_points, int(self.target_char_count * 0.2))
                elif section == "全国天気":
                    national_weather = self._adjust_text_length(national_weather, int(self.target_char_count * 0.2))
                elif section == "全国気温":
                    national_temperature = self._adjust_text_length(national_temperature, int(self.target_char_count * 0.2))
                elif section == "週間予報":
                    weekly_forecast = self._adjust_text_length(weekly_forecast, int(self.target_char_count * 0.2))
        
        # 日付情報
        now = datetime.datetime.now()
        date_str = now.strftime("%Y年%m月%d日(%a)")
        
        # 予報対象日の表示
        forecast_date = f"{day_expression}の天気予報"
        
        # 完成した原稿を辞書形式で返す（メニュー順序を維持）
        script = {
            "date": date_str,
            "forecast_date": forecast_date,
            "現在の全国天気の概況": current_national_overview,
            "今後のポイント": future_points,
            "全国天気": national_weather,
            "全国気温": national_temperature,
            "週間予報": weekly_forecast
        }
        
        # 合計文字数を計算
        total_chars = sum(len(text) for section, text in script.items() if section not in ["date", "forecast_date"])
        script["total_chars"] = total_chars
        
        # 読み上げ時間の目安（1分あたり250文字と仮定）
        reading_time = total_chars / 250
        script["reading_time"] = f"{reading_time:.1f}"
        
        return script

# 単体テスト用
if __name__ == "__main__":
    import sys
    import os
    
    # 現在のディレクトリをsrcに変更
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if os.path.basename(current_dir) == "src":
        sys.path.append(os.path.dirname(current_dir))
    else:
        sys.path.append(current_dir)
    
    from weather_data_enhanced import WeatherDataCollector
    
    # 天気データを取得
    collector = WeatherDataCollector()
    data = collector.get_complete_weather_data()
    
    # 原稿を生成
    generator = ScriptGenerator()
    script = generator.generate_complete_script(data)
    
    # 結果を表示
    print(f"日付: {script['date']}")
    print(f"予報対象: {script['forecast_date']}")
    print(f"合計文字数: {script['total_chars']}文字")
    print(f"読み上げ時間: {script['reading_time']}分")
    print("\n=== 現在の全国天気の概況 ===")
    print(script["現在の全国天気の概況"])
    print("\n=== 今後のポイント ===")
    print(script["今後のポイント"])
    print("\n=== 全国天気 ===")
    print(script["全国天気"])
    print("\n=== 全国気温 ===")
    print(script["全国気温"])
    print("\n=== 週間予報 ===")
    print(script["週間予報"])
