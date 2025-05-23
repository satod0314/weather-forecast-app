"""
天気予報データ収集モジュール
気象庁APIから最新の天気予報データを取得し、テレビ用天気予報原稿作成に必要な情報を提供します。
"""

import requests
import json
import datetime
from typing import Dict, List, Any, Optional

class WeatherDataCollector:
    """気象庁APIから天気予報データを収集するクラス"""
    
    def __init__(self):
        # 気象庁API URL
        self.jma_forecast_url = "https://www.jma.go.jp/bosai/forecast/data/forecast/{area_code}.json"
        # 全国天気用エリアコード（全国を網羅する主要都市）
        self.area_codes = {
            "北海道": "016000",  # 札幌管区
            "東北": "040000",    # 仙台管区
            "関東甲信": "130000", # 東京管区
            "北陸": "170000",    # 金沢地方
            "東海": "230000",    # 名古屋地方
            "近畿": "270000",    # 大阪管区
            "中国": "340000",    # 広島地方
            "四国": "390000",    # 高松地方
            "九州": "400000",    # 福岡管区
            "沖縄": "471000"     # 沖縄本島地方
        }
        
    def get_weather_data(self) -> Dict[str, Any]:
        """
        全国の天気予報データを取得する
        
        Returns:
            Dict[str, Any]: 全国の天気予報データ
        """
        all_weather_data = {}
        
        for region_name, area_code in self.area_codes.items():
            try:
                url = self.jma_forecast_url.format(area_code=area_code)
                response = requests.get(url)
                response.raise_for_status()  # エラーチェック
                data = response.json()
                all_weather_data[region_name] = data
            except Exception as e:
                print(f"Error fetching data for {region_name}: {e}")
                all_weather_data[region_name] = None
                
        return all_weather_data
    
    def extract_national_weather_overview(self, all_weather_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        全国の天気概況を抽出する
        
        Args:
            all_weather_data: 全国の天気予報データ
            
        Returns:
            Dict[str, Any]: 全国の天気概況
        """
        overview = {
            "today": {},
            "tomorrow": {},
            "week": {}
        }
        
        # 各地方の今日と明日の天気を抽出
        for region_name, data in all_weather_data.items():
            if data is None:
                continue
                
            try:
                # 今日の天気
                today_weather = data[0]["timeSeries"][0]["areas"][0]["weathers"][0]
                today_weather_code = data[0]["timeSeries"][0]["areas"][0]["weatherCodes"][0]
                
                # 明日の天気
                tomorrow_weather = data[0]["timeSeries"][0]["areas"][0]["weathers"][1]
                tomorrow_weather_code = data[0]["timeSeries"][0]["areas"][0]["weatherCodes"][1]
                
                # 週間天気（週間予報の最初の3日間）
                week_weathers = []
                week_weather_codes = []
                if len(data) > 1 and "timeSeries" in data[1]:
                    for i in range(min(3, len(data[1]["timeSeries"][0]["areas"][0]["weatherCodes"]))):
                        if i > 0:  # 最初の日は今日/明日と重複するので除外
                            code = data[1]["timeSeries"][0]["areas"][0]["weatherCodes"][i]
                            week_weather_codes.append(code)
                
                overview["today"][region_name] = {
                    "weather": today_weather,
                    "code": today_weather_code
                }
                
                overview["tomorrow"][region_name] = {
                    "weather": tomorrow_weather,
                    "code": tomorrow_weather_code
                }
                
                overview["week"][region_name] = {
                    "codes": week_weather_codes
                }
                
            except (KeyError, IndexError) as e:
                print(f"Error extracting data for {region_name}: {e}")
        
        return overview
    
    def extract_national_temperature(self, all_weather_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        全国の気温情報を抽出する
        
        Args:
            all_weather_data: 全国の天気予報データ
            
        Returns:
            Dict[str, Any]: 全国の気温情報
        """
        temperature = {
            "today": {},
            "tomorrow": {}
        }
        
        # 各地方の今日と明日の気温を抽出
        for region_name, data in all_weather_data.items():
            if data is None:
                continue
                
            try:
                # 気温データがある場合のみ処理
                if len(data[0]["timeSeries"]) > 2:
                    # 代表都市の気温を取得
                    city_temps = data[0]["timeSeries"][2]["areas"][0]["temps"]
                    
                    # 今日の最高気温
                    today_max = city_temps[0] if len(city_temps) > 0 else None
                    
                    # 明日の最高気温と最低気温
                    tomorrow_min = None
                    tomorrow_max = None
                    
                    if len(city_temps) > 2:
                        tomorrow_min = city_temps[2]
                        tomorrow_max = city_temps[3] if len(city_temps) > 3 else None
                    
                    temperature["today"][region_name] = {
                        "max": today_max
                    }
                    
                    temperature["tomorrow"][region_name] = {
                        "min": tomorrow_min,
                        "max": tomorrow_max
                    }
            
            except (KeyError, IndexError) as e:
                print(f"Error extracting temperature for {region_name}: {e}")
        
        return temperature
    
    def extract_weekly_forecast(self, all_weather_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        週間天気予報を抽出する
        
        Args:
            all_weather_data: 全国の天気予報データ
            
        Returns:
            Dict[str, Any]: 週間天気予報
        """
        weekly = {}
        
        # 代表的な地域（東京）の週間天気予報を抽出
        if "関東甲信" in all_weather_data and all_weather_data["関東甲信"] is not None:
            data = all_weather_data["関東甲信"]
            
            try:
                if len(data) > 1:
                    # 週間天気予報の日付、天気、降水確率、最高/最低気温を抽出
                    time_defines = data[1]["timeSeries"][0]["timeDefines"]
                    weather_codes = data[1]["timeSeries"][0]["areas"][0]["weatherCodes"]
                    pops = data[1]["timeSeries"][0]["areas"][0]["pops"]
                    
                    # 気温データ
                    if len(data[1]["timeSeries"]) > 1:
                        temps_min = data[1]["timeSeries"][1]["areas"][0]["tempsMin"]
                        temps_max = data[1]["timeSeries"][1]["areas"][0]["tempsMax"]
                    else:
                        temps_min = [None] * len(time_defines)
                        temps_max = [None] * len(time_defines)
                    
                    # 日付ごとにデータを整理
                    for i in range(len(time_defines)):
                        if i == 0:  # 最初の日は今日/明日と重複するので除外
                            continue
                            
                        date_str = time_defines[i]
                        date_obj = datetime.datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                        date_formatted = date_obj.strftime("%m/%d")
                        
                        weekly[date_formatted] = {
                            "weather_code": weather_codes[i] if i < len(weather_codes) else None,
                            "pop": pops[i] if i < len(pops) else None,
                            "temp_min": temps_min[i] if i < len(temps_min) else None,
                            "temp_max": temps_max[i] if i < len(temps_max) else None
                        }
            
            except (KeyError, IndexError) as e:
                print(f"Error extracting weekly forecast: {e}")
        
        return weekly
    
    def get_weather_warnings(self, all_weather_data: Dict[str, Any]) -> List[str]:
        """
        注意報・警報情報を抽出する
        
        Args:
            all_weather_data: 全国の天気予報データ
            
        Returns:
            List[str]: 注意報・警報情報のリスト
        """
        warnings = []
        
        # 各地方の注意報・警報情報を確認
        # 実際の気象庁APIでは別エンドポイントから取得する必要があるため、
        # ここでは天気予報データから推測される警報情報を生成
        for region_name, data in all_weather_data.items():
            if data is None:
                continue
                
            try:
                # 今日の天気から警報情報を推測
                today_weather = data[0]["timeSeries"][0]["areas"][0]["weathers"][0]
                today_weather_code = data[0]["timeSeries"][0]["areas"][0]["weatherCodes"][0]
                
                # 大雨・雷・強風などのキーワードがあれば警報として扱う
                keywords = ["大雨", "暴風", "雷", "警報", "注意報", "激しく", "非常に激しく"]
                for keyword in keywords:
                    if keyword in today_weather:
                        warnings.append(f"{region_name}地方では{keyword}に注意")
                        break
                
                # 天気コードから警報情報を推測
                warning_codes = ["203", "204", "205", "206", "207", "208", "209", "300", "301", "302", "303", "304", "306", "308", "309", "350"]
                if today_weather_code in warning_codes:
                    if not any(region_name in w for w in warnings):
                        warnings.append(f"{region_name}地方では天候の急変に注意")
            
            except (KeyError, IndexError) as e:
                print(f"Error extracting warnings for {region_name}: {e}")
        
        return warnings
    
    def get_complete_weather_data(self) -> Dict[str, Any]:
        """
        天気予報原稿作成に必要な全データを取得する
        
        Returns:
            Dict[str, Any]: 天気予報原稿作成に必要な全データ
        """
        # 全国の天気予報データを取得
        all_weather_data = self.get_weather_data()
        
        # 全国の天気概況を抽出
        overview = self.extract_national_weather_overview(all_weather_data)
        
        # 全国の気温情報を抽出
        temperature = self.extract_national_temperature(all_weather_data)
        
        # 週間天気予報を抽出
        weekly = self.extract_weekly_forecast(all_weather_data)
        
        # 注意報・警報情報を抽出
        warnings = self.get_weather_warnings(all_weather_data)
        
        # 現在の日時
        now = datetime.datetime.now()
        date_str = now.strftime("%Y年%m月%d日(%a)")
        
        # 全データをまとめる
        complete_data = {
            "date": date_str,
            "overview": overview,
            "temperature": temperature,
            "weekly": weekly,
            "warnings": warnings,
            "raw_data": all_weather_data
        }
        
        return complete_data

# 単体テスト用
if __name__ == "__main__":
    collector = WeatherDataCollector()
    data = collector.get_complete_weather_data()
    print(json.dumps(data, ensure_ascii=False, indent=2))
