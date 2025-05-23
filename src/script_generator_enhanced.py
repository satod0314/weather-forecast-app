"""
拡張版天気予報原稿生成モジュール
複数情報源から収集した天気データから、テレビ用の天気予報原稿を生成します。
ナレーション調の自然な話し言葉で、2分程度の適切な長さに調整します。
丁寧で親しみやすい口調を維持しつつ、全国の天気情報を簡潔に要約します。
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
        
        # 天気コードと天気表現のマッピング
        self.weather_expressions = {
            # 晴れ系
            "100": ["青空が広がる", "晴れ渡った空", "日差しが降り注ぐ", "澄み切った青空の下"],
            "101": ["晴れ間が広がる", "時々雲が現れる", "おおむね晴れ", "晴れ時々曇り"],
            "110": ["晴れの天気", "日差しが感じられる", "晴れ模様", "日が差す天気"],
            "111": ["晴れ間が見える", "時々雲が広がる", "晴れ時々曇り", "晴れたり曇ったり"],
            "112": ["晴れ間が見える", "雨の合間に晴れ間", "晴れ間が出る", "雨上がりの晴れ間"],
            "115": ["晴れ間が見える", "雪の合間に晴れ間", "晴れ間が出る", "雪の晴れ間"],
            
            # 曇り系
            "200": ["雲が広がる", "曇り空", "雲に覆われた空", "グレーの雲に包まれた"],
            "201": ["雲が多く見られる", "やや曇った空", "曇り時々晴れ", "雲の多い天気"],
            "202": ["雲が広がり", "曇り一時雨", "雨の降る可能性", "雨雲が近づく"],
            "203": ["雪雲が広がり", "曇り一時雪", "雪の降る可能性", "雪雲が近づく"],
            "204": ["曇り時々雨", "雨の降る時間帯も", "雨雲が通過", "雨の降ったり止んだり"],
            "205": ["曇り時々雪", "雪の降る時間帯も", "雪雲が通過", "雪の降ったり止んだり"],
            "206": ["曇り一時雨か雪", "雨や雪の可能性", "天気が不安定", "雨や雪が混じる"],
            "207": ["曇り一時雨か雷雨", "雷を伴う雨の可能性", "雷雨の恐れ", "激しい雨の可能性"],
            "208": ["曇り一時雪か雷雪", "雷を伴う雪の可能性", "雷雪の恐れ", "激しい雪の可能性"],
            "209": ["霧が発生", "視界不良", "霧に包まれた", "霧で見通しが悪い"],
            "210": ["曇りがち", "雲の多い天気", "どんよりとした空", "薄暗い雲に覆われた"],
            "211": ["曇り時々晴れ", "晴れ間も見られる", "雲の切れ間から青空", "雲の多い中でも晴れ間"],
            "212": ["曇り後雨", "次第に雨の降る天気", "雨雲が近づく", "雨の予報"],
            "213": ["曇り後雪", "次第に雪の降る天気", "雪雲が近づく", "雪の予報"],
            "214": ["曇り後雨か雪", "雨や雪に変わる", "天気が崩れる", "雨や雪の予報"],
            "215": ["曇り後雨か雷雨", "雷雨に変わる可能性", "激しい雨に変わる", "雷を伴う雨の予報"],
            "216": ["曇り後雪か雷雪", "雷雪に変わる可能性", "激しい雪に変わる", "雷を伴う雪の予報"],
            "217": ["曇り後霧", "霧が発生する見込み", "視界不良になる", "霧に包まれる予報"],
            "218": ["曇り後晴れ", "次第に晴れる", "雲が晴れてくる", "晴れ間が広がる"],
            "219": ["曇り昼頃から雨", "昼頃から雨の降る天気", "午後は雨模様", "昼過ぎから雨"],
            "220": ["曇り夕方から雨", "夕方から雨の降る天気", "夜は雨模様", "夕刻から雨"],
            "221": ["曇り夜は雨", "夜になると雨", "夜間は雨の予報", "夜から雨模様"],
            
            # 雨系
            "300": ["雨が降る", "雨模様", "傘が必要", "雨の一日"],
            "301": ["雨時々晴れ", "雨の合間に晴れ間", "にわか雨", "晴れ間もある雨"],
            "302": ["雨時々止む", "断続的な雨", "雨が降ったり止んだり", "雨脚が強まったり弱まったり"],
            "303": ["雨時々雪", "雨と雪が混じる", "雨や雪が降る", "雨と雪が入り混じる"],
            "304": ["雨か雪", "雨または雪", "雨や雪の可能性", "雨と雪の境界"],
            "306": ["大雨", "激しい雨", "土砂災害に警戒", "河川の増水に注意"],
            "308": ["雷を伴う雨", "雷雨", "激しい雨と雷", "雷鳴の響く雨"],
            "309": ["雨で暴風を伴う", "暴風雨", "強風と雨", "風雨が強まる"],
            "311": ["雨後晴れ", "雨上がりの晴天", "雨の後は晴れる", "雨が止んで晴れる"],
            "313": ["雨後曇り", "雨が止んで曇る", "雨上がりの曇天", "雨の後は曇り空"],
            "314": ["雨後雪", "雨から雪に変わる", "雨が雪に変わる", "雨の後は雪"],
            "315": ["雨か雷雨後晴れ", "雷雨の後は晴れる", "激しい雨の後は晴天", "雷雨が過ぎ去り晴れる"],
            "316": ["雨か雷雨後曇り", "雷雨の後は曇る", "激しい雨の後は曇天", "雷雨が過ぎ去り曇る"],
            "317": ["雨か雷雨後雪", "雷雨の後は雪", "激しい雨の後は雪", "雷雨が過ぎ去り雪に変わる"],
            "320": ["朝の内雨後晴れ", "朝は雨、その後晴れる", "午前中は雨、午後は晴れ", "朝の雨は上がり晴れる"],
            "321": ["朝の内雨後曇り", "朝は雨、その後曇る", "午前中は雨、午後は曇り", "朝の雨は上がり曇る"],
            
            # 雪系
            "400": ["雪が降る", "雪模様", "雪の舞う", "雪の一日"],
            "401": ["雪時々晴れ", "雪の合間に晴れ間", "にわか雪", "晴れ間もある雪"],
            "402": ["雪時々止む", "断続的な雪", "雪が降ったり止んだり", "雪の強さが変わる"],
            "403": ["雪時々雨", "雪と雨が混じる", "みぞれ", "雪と雨が入り混じる"],
            "405": ["大雪", "激しい雪", "積雪に警戒", "交通障害に注意"],
            "406": ["風雪強い", "吹雪", "地吹雪", "視界不良に注意"],
            "407": ["暴風雪", "猛吹雪", "外出危険", "厳重な警戒が必要"],
            "409": ["雪で雷を伴う", "雷雪", "雷を伴う雪", "雷鳴の響く雪"],
            "411": ["雪後晴れ", "雪上がりの晴天", "雪の後は晴れる", "雪が止んで晴れる"],
            "413": ["雪後曇り", "雪が止んで曇る", "雪上がりの曇天", "雪の後は曇り空"],
            "414": ["雪後雨", "雪から雨に変わる", "雪が雨に変わる", "雪の後は雨"],
            "420": ["朝の内雪後晴れ", "朝は雪、その後晴れる", "午前中は雪、午後は晴れ", "朝の雪は上がり晴れる"],
            "421": ["朝の内雪後曇り", "朝は雪、その後曇る", "午前中は雪、午後は曇り", "朝の雪は上がり曇る"],
            "422": ["朝の内雪後雨", "朝は雪、その後雨", "午前中は雪、午後は雨", "朝の雪は上がり雨に変わる"],
        }
        
        # 天気の傾向を表す表現
        self.weather_trend_expressions = {
            "sunny_to_cloudy": ["次第に雲が広がり", "晴れから曇りに変わり", "晴れの後曇りに転じ", "晴れ間が少なくなり"],
            "cloudy_to_sunny": ["雲が晴れて", "曇りから晴れに変わり", "次第に晴れ間が広がり", "雲が少なくなり"],
            "cloudy_to_rainy": ["雨雲が近づき", "次第に雨の降る所が多くなり", "天気が下り坂となり", "雨の降る地域が広がり"],
            "rainy_to_cloudy": ["雨は次第に上がり", "雨雲が遠ざかり", "雨は止んで", "雨の降る地域が減り"],
            "getting_colder": ["気温が下がり", "寒気が入り", "冷え込みが強まり", "気温が低下し"],
            "getting_warmer": ["気温が上がり", "暖かい空気に覆われ", "気温が上昇し", "暖かさが増し"]
        }
        
        # 季節感を表す表現
        self.seasonal_expressions = {
            "spring": ["春らしい陽気", "春の訪れを感じる", "春めいた天気", "春風が心地よい"],
            "summer": ["夏らしい暑さ", "夏空が広がる", "真夏日となる所も", "熱中症に注意が必要な暑さ"],
            "autumn": ["秋らしい爽やかさ", "秋の気配を感じる", "秋晴れの空", "秋の深まりを感じる"],
            "winter": ["冬らしい冷え込み", "冬の厳しさが増す", "冬本番の寒さ", "冬の冷たい空気"]
        }
        
        # 時間帯を表す表現
        self.time_expressions = {
            "morning": ["朝は", "朝方は", "早朝は", "午前中は"],
            "afternoon": ["昼頃は", "午後は", "日中は", "昼間は"],
            "evening": ["夕方は", "夕刻は", "夕暮れ時は", "日没頃は"],
            "night": ["夜は", "夜間は", "夜遅くは", "深夜は"]
        }
        
        # 丁寧で親しみやすい文末表現
        self.polite_endings = [
            "でしょう。",
            "となるでしょう。",
            "見込みです。",
            "予想されます。",
            "になりそうです。",
            "でしょう。",
            "となりそうです。",
            "のようです。",
            "ようです。",
            "見通しです。"
        ]
        
        # 接続詞・接続表現
        self.conjunctions = [
            "また、",
            "そして、",
            "一方、",
            "さらに、",
            "なお、",
            "ところで、",
            "続いて、",
            "次に、"
        ]
        
        # 注意喚起表現
        self.caution_expressions = [
            "お出かけの際は{item}にご注意ください。",
            "{item}にはくれぐれもご注意ください。",
            "{item}には十分お気をつけください。",
            "{item}に対する備えをお願いします。"
        ]
        
        # 注意項目
        self.caution_items = {
            "rain": ["傘の準備", "足元の濡れ", "路面の滑りやすさ", "雨の強まり"],
            "snow": ["路面の凍結", "積雪", "視界不良", "転倒"],
            "wind": ["強風", "飛ばされやすいもの", "突風", "風の強まり"],
            "heat": ["熱中症", "水分補給", "直射日光", "体調管理"],
            "cold": ["防寒対策", "凍結", "体温管理", "乾燥"]
        }
        
        # 親しみやすい挨拶表現
        self.greeting_expressions = [
            "皆さん、こんにちは。",
            "お天気の時間です。",
            "それでは天気予報をお伝えします。",
            "今日の天気をお伝えします。"
        ]
        
        # 締めくくり表現
        self.closing_expressions = [
            "以上、天気予報でした。",
            "今日もお天気に気をつけてお過ごしください。",
            "最新の気象情報にご注意ください。",
            "お出かけの際は天気の変化にご注意ください。"
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
        return "天気が変わる"
    
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
            
            additional_text = f"。{self._get_conjunction()}{seasonal_expr}の一日に{self._get_polite_ending()}"
            return text + additional_text
        
        return text
    
    def generate_national_weather_overview(self, weather_data):
        """
        全国の天気概況を生成
        
        Args:
            weather_data: 天気データ
            
        Returns:
            str: 全国の天気概況
        """
        try:
            # 挨拶から始める
            greeting = self._get_random_expression(self.greeting_expressions)
            
            overview = weather_data["overview"]["today"]
            
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
                overview_text = f"{greeting} 今日の天気は、" + "、".join(pattern_texts) + f"となっています{self._get_polite_ending()[:-1]}。"
                
                # 季節感を追加
                seasonal_expr = self._get_random_expression(self.seasonal_expressions[self.current_season])
                overview_text += f"{seasonal_expr}が感じられる一日です。"
                
                return overview_text
            else:
                return f"{greeting} 今日の天気は地域によって変化があります。お出かけの際は最新の天気予報をご確認ください。"
                
        except Exception as e:
            print(f"Error generating national weather overview: {e}")
            return f"{self._get_random_expression(self.greeting_expressions)} 今日の天気は地域によって様々です。お出かけの際は最新の天気予報をご確認ください。"
    
    def generate_weather_points(self, weather_data):
        """
        今後の天気のポイントを生成
        
        Args:
            weather_data: 天気データ
            
        Returns:
            str: 今後の天気のポイント
        """
        try:
            # 警報・注意報情報を取得
            warnings = weather_data.get("warnings", [])
            
            # 明日の天気概況を取得
            tomorrow_overview = weather_data["overview"]["tomorrow"]
            
            points_text = ""
            
            # 警報・注意報がある場合
            if warnings:
                warnings_text = "、".join(warnings[:2])
                if len(warnings) > 2:
                    warnings_text += "など"
                
                points_text += f"{warnings_text}が発表されています。十分ご注意ください。"
            
            # 明日の天気の特徴を抽出
            tomorrow_patterns = {}
            for region, data in tomorrow_overview.items():
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
                
                if pattern not in tomorrow_patterns:
                    tomorrow_patterns[pattern] = []
                tomorrow_patterns[pattern].append(region)
            
            # 明日の天気の傾向
            if tomorrow_patterns:
                if points_text:
                    points_text += f" {self._get_conjunction()}"
                
                # 最も多い天気パターンを特定
                max_pattern = max(tomorrow_patterns.items(), key=lambda x: len(x[1]))
                pattern, regions = max_pattern
                
                if len(regions) >= 7:  # ほぼ全国的
                    points_text += f"明日は全国的に{pattern}の天気となる見込み{self._get_polite_ending()}"
                else:
                    regions_text = "、".join(regions[:2])
                    if len(regions) > 2:
                        regions_text += "など"
                    points_text += f"明日は{regions_text}を中心に{pattern}の天気となる見込み{self._get_polite_ending()}"
            
            # 注意事項を追加
            if "雨" in str(tomorrow_patterns.keys()):
                points_text += f" {self._get_caution_expression('rain')}"
            elif "雪" in str(tomorrow_patterns.keys()):
                points_text += f" {self._get_caution_expression('snow')}"
            elif self.current_season == "summer":
                points_text += f" {self._get_caution_expression('heat')}"
            elif self.current_season == "winter":
                points_text += f" {self._get_caution_expression('cold')}"
            
            return points_text
            
        except Exception as e:
            print(f"Error generating weather points: {e}")
            return "今後の天気の変化にご注意ください。最新の気象情報をこまめに確認することをおすすめします。"
    
    def generate_national_weather(self, weather_data):
        """
        全国の天気を生成
        
        Args:
            weather_data: 天気データ
            
        Returns:
            str: 全国の天気
        """
        try:
            # 今日の天気概況
            today_overview = weather_data["overview"]["today"]
            
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
                    if region in today_overview:
                        weather_codes.append(today_overview[region]["code"])
                
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
                weather_texts.append(f"{group_name}は{weather_expr}")
            
            # 全国の天気文を生成
            if weather_texts:
                national_text = "全国の天気は、" + "、".join(weather_texts) + f"となっています{self._get_polite_ending()[:-1]}。"
                
                # 気温の傾向を追加
                if self.current_season in ["spring", "summer"]:
                    national_text += f"気温は平年並みから高めで推移する見込み{self._get_polite_ending()}"
                else:
                    national_text += f"気温は平年並みから低めで推移する見込み{self._get_polite_ending()}"
                
                return national_text
            else:
                return "全国的に天気は変化しています。各地の最新の気象情報にご注意ください。"
                
        except Exception as e:
            print(f"Error generating national weather: {e}")
            return "全国的に天気は変化しています。各地の最新の気象情報にご注意ください。"
    
    def generate_national_temperature(self, weather_data):
        """
        全国の気温情報を生成
        
        Args:
            weather_data: 天気データ
            
        Returns:
            str: 全国の気温情報
        """
        try:
            # 今日の気温データ
            today_temp = weather_data["temperature"]["today"]
            tomorrow_temp = weather_data["temperature"]["tomorrow"]
            
            # 代表的な地域の気温を抽出
            key_regions = ["関東甲信", "北海道", "沖縄"]
            temp_texts = []
            
            for region in key_regions:
                if region in today_temp and region in tomorrow_temp:
                    today_max = today_temp[region].get("max")
                    tomorrow_max = tomorrow_temp[region].get("max")
                    tomorrow_min = tomorrow_temp[region].get("min")
                    
                    if today_max and tomorrow_max:
                        # 気温の変化を表現
                        if int(tomorrow_max) > int(today_max):
                            temp_texts.append(f"{region}地方は明日の最高気温が{tomorrow_max}度まで上昇")
                        elif int(tomorrow_max) < int(today_max):
                            temp_texts.append(f"{region}地方は明日の最高気温が{tomorrow_max}度まで下降")
                        else:
                            temp_texts.append(f"{region}地方は明日も最高気温が{tomorrow_max}度")
            
            # 全国の気温傾向
            if self.current_season == "summer":
                general_trend = "全国的に気温が高く、熱中症対策が必要な一日となりそうです。"
            elif self.current_season == "winter":
                general_trend = "全国的に気温が低く、防寒対策をしっかりと行ってください。"
            else:
                general_trend = "全国的に気温は平年並みからやや高めで推移する見込みです。"
            
            # 気温情報を文章化
            if temp_texts:
                temp_text = "気温については、" + "、".join(temp_texts) + f"する見込み{self._get_polite_ending()[:-1]}。"
                temp_text += f" {general_trend}"
                return temp_text
            else:
                return general_trend
                
        except Exception as e:
            print(f"Error generating national temperature: {e}")
            return "全国的に気温は平年並みで推移する見込みです。急な気温変化にはご注意ください。"
    
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
                return "週間予報については、明日以降も天気の変化にご注意ください。最新の気象情報をこまめに確認することをおすすめします。"
            
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
                    trend_text += "週間を通して晴れの天気が続く見込みです。"
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
                trend_text += f" {self._get_caution_expression('rain')}"
            elif self.current_season == "summer":
                trend_text += f" {self._get_caution_expression('heat')}"
            elif self.current_season == "winter":
                trend_text += f" {self._get_caution_expression('cold')}"
            
            # 締めくくり
            trend_text += f" {self._get_random_expression(self.closing_expressions)}"
            
            return trend_text
            
        except Exception as e:
            print(f"Error generating weekly forecast: {e}")
            return "週間予報については、明日以降も天気の変化にご注意ください。最新の気象情報をこまめに確認することをおすすめします。"
    
    def generate_complete_script(self, weather_data):
        """
        完全な天気予報原稿を生成
        
        Args:
            weather_data: 天気データ
            
        Returns:
            Dict[str, str]: 各セクションの原稿
        """
        # 各セクションの原稿を生成
        national_overview = self.generate_national_weather_overview(weather_data)
        weather_points = self.generate_weather_points(weather_data)
        national_weather = self.generate_national_weather(weather_data)
        national_temperature = self.generate_national_temperature(weather_data)
        weekly_forecast = self.generate_weekly_forecast(weather_data)
        
        # 各セクションの文字数を計算
        char_counts = {
            "現在の全国天気の概況": len(national_overview),
            "今後のポイント": len(weather_points),
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
                    national_overview = self._adjust_text_length(national_overview, int(self.target_char_count * 0.2))
                elif section == "今後のポイント":
                    weather_points = self._adjust_text_length(weather_points, int(self.target_char_count * 0.2))
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
                    national_overview = self._adjust_text_length(national_overview, int(self.target_char_count * 0.2))
                elif section == "今後のポイント":
                    weather_points = self._adjust_text_length(weather_points, int(self.target_char_count * 0.2))
                elif section == "全国天気":
                    national_weather = self._adjust_text_length(national_weather, int(self.target_char_count * 0.2))
                elif section == "全国気温":
                    national_temperature = self._adjust_text_length(national_temperature, int(self.target_char_count * 0.2))
                elif section == "週間予報":
                    weekly_forecast = self._adjust_text_length(weekly_forecast, int(self.target_char_count * 0.2))
        
        # 日付情報
        now = datetime.datetime.now()
        date_str = now.strftime("%Y年%m月%d日(%a)")
        
        # 完成した原稿を辞書形式で返す
        script = {
            "date": date_str,
            "現在の全国天気の概況": national_overview,
            "今後のポイント": weather_points,
            "全国天気": national_weather,
            "全国気温": national_temperature,
            "週間予報": weekly_forecast
        }
        
        # 合計文字数を計算
        total_chars = sum(len(text) for section, text in script.items() if section != "date")
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
