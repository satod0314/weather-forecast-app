"""
拡張版天気予報データ収集モジュール
気象庁API、ウェザーマップ、その他信頼できる情報源から最新の天気予報データを取得し、
テレビ用天気予報原稿作成に必要な情報を提供します。
複数情報源からのデータ統合とエラー時のフォールバック機能を備えています。
"""

import requests
import json
import datetime
import time
import re
from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional

class WeatherDataCollector:
    """複数の情報源から天気予報データを収集するクラス"""
    
    def __init__(self):
        # 気象庁API URL
        self.jma_forecast_url = "https://www.jma.go.jp/bosai/forecast/data/forecast/{area_code}.json"
        self.jma_overview_url = "https://www.jma.go.jp/bosai/forecast/data/overview_forecast/{area_code}.json"
        
        # ウェザーマップURL
        self.weathermap_url = "https://weathermap.jp/s/0/{area_name}/"
        
        # Yahoo!天気URL
        self.yahoo_weather_url = "https://weather.yahoo.co.jp/weather/jp/{region_id}/{prefecture_id}/{city_id}.html"
        
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
        
        # 地域名とウェザーマップ検索キーワードのマッピング
        self.weathermap_area_names = {
            "北海道": "北海道",
            "東北": "宮城県",
            "関東甲信": "東京都",
            "北陸": "石川県",
            "東海": "愛知県",
            "近畿": "大阪府",
            "中国": "広島県",
            "四国": "香川県",
            "九州": "福岡県",
            "沖縄": "沖縄県"
        }
        
        # Yahoo!天気の地域ID
        self.yahoo_weather_ids = {
            "北海道": {"region_id": "1", "prefecture_id": "1", "city_id": "2128"},  # 札幌
            "東北": {"region_id": "2", "prefecture_id": "4", "city_id": "3410"},    # 仙台
            "関東甲信": {"region_id": "3", "prefecture_id": "13", "city_id": "4410"}, # 東京
            "北陸": {"region_id": "4", "prefecture_id": "17", "city_id": "5610"},   # 金沢
            "東海": {"region_id": "5", "prefecture_id": "23", "city_id": "6710"},   # 名古屋
            "近畿": {"region_id": "6", "prefecture_id": "27", "city_id": "6200"},   # 大阪
            "中国": {"region_id": "7", "prefecture_id": "34", "city_id": "6710"},   # 広島
            "四国": {"region_id": "8", "prefecture_id": "37", "city_id": "7110"},   # 高松
            "九州": {"region_id": "9", "prefecture_id": "40", "city_id": "8210"},   # 福岡
            "沖縄": {"region_id": "10", "prefecture_id": "47", "city_id": "9110"}   # 那覇
        }
        
        # ユーザーエージェント（Webスクレイピング用）
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        
        # 天気コードと天気のマッピング（気象庁コード）
        self.weather_code_mapping = {
            "100": "晴れ",
            "101": "晴れ時々曇り",
            "102": "晴れ一時雨",
            "103": "晴れ時々雨",
            "104": "晴れ一時雪",
            "105": "晴れ時々雪",
            "106": "晴れ一時雨か雪",
            "107": "晴れ時々雨か雪",
            "108": "晴れ一時雨か雷雨",
            "110": "晴れ後時々曇り",
            "111": "晴れ後曇り",
            "112": "晴れ後一時雨",
            "113": "晴れ後時々雨",
            "114": "晴れ後雨",
            "115": "晴れ後一時雪",
            "116": "晴れ後時々雪",
            "117": "晴れ後雪",
            "118": "晴れ後雨か雪",
            "119": "晴れ後雨か雷雨",
            "120": "晴れ朝夕一時雨",
            "121": "晴れ朝の内一時雨",
            "122": "晴れ夕方一時雨",
            "123": "晴れ山沿い雷雨",
            "124": "晴れ山沿い雪",
            "125": "晴れ午後は雷雨",
            "126": "晴れ昼頃から雨",
            "127": "晴れ夕方から雨",
            "128": "晴れ夜は雨",
            "130": "朝の内霧後晴れ",
            "131": "晴れ明け方霧",
            "132": "晴れ朝夕曇り",
            "140": "晴れ時々雨で雷を伴う",
            "160": "晴れ一時雪か雨",
            "170": "晴れ時々雪か雨",
            "181": "晴れ後雪か雨",
            "200": "曇り",
            "201": "曇り時々晴れ",
            "202": "曇り一時雨",
            "203": "曇り時々雨",
            "204": "曇り一時雪",
            "205": "曇り時々雪",
            "206": "曇り一時雨か雪",
            "207": "曇り時々雨か雪",
            "208": "曇り一時雨か雷雨",
            "209": "霧",
            "210": "曇り後時々晴れ",
            "211": "曇り後晴れ",
            "212": "曇り後一時雨",
            "213": "曇り後時々雨",
            "214": "曇り後雨",
            "215": "曇り後一時雪",
            "216": "曇り後時々雪",
            "217": "曇り後雪",
            "218": "曇り後雨か雪",
            "219": "曇り後雨か雷雨",
            "220": "曇り朝夕一時雨",
            "221": "曇り朝の内一時雨",
            "222": "曇り夕方一時雨",
            "223": "曇り日中時々晴れ",
            "224": "曇り昼頃から雨",
            "225": "曇り夕方から雨",
            "226": "曇り夜は雨",
            "228": "曇り昼頃から雪",
            "229": "曇り夕方から雪",
            "230": "曇り夜は雪",
            "231": "曇り海上海岸は霧か霧雨",
            "240": "曇り時々雨で雷を伴う",
            "250": "曇り時々雪で雷を伴う",
            "260": "曇り一時雪か雨",
            "270": "曇り時々雪か雨",
            "281": "曇り後雪か雨",
            "300": "雨",
            "301": "雨時々晴れ",
            "302": "雨時々止む",
            "303": "雨時々雪",
            "304": "雨か雪",
            "306": "大雨",
            "308": "雨で暴風を伴う",
            "309": "雨一時雪",
            "311": "雨後晴れ",
            "313": "雨後曇り",
            "314": "雨後時々雪",
            "315": "雨後雪",
            "316": "雨か雪後晴れ",
            "317": "雨か雪後曇り",
            "320": "朝の内雨後晴れ",
            "321": "朝の内雨後曇り",
            "322": "雨朝晩一時雪",
            "323": "雨昼頃から晴れ",
            "324": "雨夕方から晴れ",
            "325": "雨夜は晴れ",
            "326": "雨昼頃から曇り",
            "327": "雨夕方から曇り",
            "328": "雨夜は曇り",
            "329": "雨一時強く降る",
            "340": "雪か雨",
            "350": "雨で雷を伴う",
            "361": "雪か雨後晴れ",
            "371": "雪か雨後曇り",
            "400": "雪",
            "401": "雪時々晴れ",
            "402": "雪時々止む",
            "403": "雪時々雨",
            "405": "大雪",
            "406": "風雪強い",
            "407": "暴風雪",
            "409": "雪一時雨",
            "411": "雪後晴れ",
            "413": "雪後曇り",
            "414": "雪後雨",
            "420": "朝の内雪後晴れ",
            "421": "朝の内雪後曇り",
            "422": "雪昼頃から雨",
            "423": "雪夕方から雨",
            "425": "雪一時強く降る",
            "426": "雪後みぞれ",
            "427": "みぞれ後雪",
            "450": "雪で雷を伴う"
        }
        
    def get_jma_weather_data(self) -> Dict[str, Any]:
        """
        気象庁APIから全国の天気予報データを取得する
        
        Returns:
            Dict[str, Any]: 全国の天気予報データ
        """
        all_weather_data = {}
        
        for region_name, area_code in self.area_codes.items():
            try:
                # 予報データを取得
                forecast_url = self.jma_forecast_url.format(area_code=area_code)
                forecast_response = requests.get(forecast_url, timeout=10)
                forecast_response.raise_for_status()
                forecast_data = forecast_response.json()
                
                # 概況データを取得
                overview_url = self.jma_overview_url.format(area_code=area_code)
                overview_response = requests.get(overview_url, timeout=10)
                overview_response.raise_for_status()
                overview_data = overview_response.json()
                
                # データを統合
                all_weather_data[region_name] = {
                    "forecast": forecast_data,
                    "overview": overview_data
                }
                
                # APIリクエスト間隔を空ける（サーバー負荷軽減）
                time.sleep(0.5)
                
            except Exception as e:
                print(f"Error fetching JMA data for {region_name}: {e}")
                all_weather_data[region_name] = None
                
        return all_weather_data
    
    def get_weathermap_data(self) -> Dict[str, Any]:
        """
        ウェザーマップから全国の天気予報データを取得する
        
        Returns:
            Dict[str, Any]: 全国の天気予報データ
        """
        all_weather_data = {}
        
        headers = {
            "User-Agent": self.user_agent
        }
        
        for region_name, area_name in self.weathermap_area_names.items():
            try:
                url = self.weathermap_url.format(area_name=area_name)
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                
                # BeautifulSoupでHTMLを解析
                soup = BeautifulSoup(response.text, "html.parser")
                
                # 今日の天気
                today_weather = None
                today_element = soup.select_one(".today-weather")
                if today_element:
                    today_weather = today_element.text.strip()
                
                # 明日の天気
                tomorrow_weather = None
                tomorrow_element = soup.select_one(".tomorrow-weather")
                if tomorrow_element:
                    tomorrow_weather = tomorrow_element.text.strip()
                
                # 気温データ
                temps = {}
                temp_elements = soup.select(".temperature")
                if temp_elements and len(temp_elements) >= 2:
                    today_temp = temp_elements[0].text.strip()
                    tomorrow_temp = temp_elements[1].text.strip()
                    
                    # 気温から最高・最低を抽出
                    today_match = re.search(r"(\d+)[^\d]+(\d+)", today_temp)
                    if today_match:
                        temps["today_max"] = today_match.group(1)
                        temps["today_min"] = today_match.group(2)
                    
                    tomorrow_match = re.search(r"(\d+)[^\d]+(\d+)", tomorrow_temp)
                    if tomorrow_match:
                        temps["tomorrow_max"] = tomorrow_match.group(1)
                        temps["tomorrow_min"] = tomorrow_match.group(2)
                
                # 週間天気
                weekly = {}
                weekly_elements = soup.select(".weekly-forecast .day")
                for i, element in enumerate(weekly_elements):
                    if i < 7:  # 7日分まで取得
                        date_elem = element.select_one(".date")
                        weather_elem = element.select_one(".weather")
                        temp_elem = element.select_one(".temp")
                        
                        if date_elem and weather_elem and temp_elem:
                            date = date_elem.text.strip()
                            weather = weather_elem.text.strip()
                            temp = temp_elem.text.strip()
                            
                            # 気温から最高・最低を抽出
                            temp_match = re.search(r"(\d+)[^\d]+(\d+)", temp)
                            if temp_match:
                                max_temp = temp_match.group(1)
                                min_temp = temp_match.group(2)
                            else:
                                max_temp = None
                                min_temp = None
                            
                            weekly[date] = {
                                "weather": weather,
                                "max_temp": max_temp,
                                "min_temp": min_temp
                            }
                
                all_weather_data[region_name] = {
                    "today_weather": today_weather,
                    "tomorrow_weather": tomorrow_weather,
                    "temperatures": temps,
                    "weekly": weekly
                }
                
                # APIリクエスト間隔を空ける（サーバー負荷軽減）
                time.sleep(0.5)
                
            except Exception as e:
                print(f"Error fetching Weathermap data for {region_name}: {e}")
                all_weather_data[region_name] = None
                
        return all_weather_data
    
    def get_yahoo_weather_data(self) -> Dict[str, Any]:
        """
        Yahoo!天気から全国の天気予報データを取得する
        
        Returns:
            Dict[str, Any]: 全国の天気予報データ
        """
        all_weather_data = {}
        
        headers = {
            "User-Agent": self.user_agent
        }
        
        for region_name, ids in self.yahoo_weather_ids.items():
            try:
                url = self.yahoo_weather_url.format(
                    region_id=ids["region_id"],
                    prefecture_id=ids["prefecture_id"],
                    city_id=ids["city_id"]
                )
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                
                # BeautifulSoupでHTMLを解析
                soup = BeautifulSoup(response.text, "html.parser")
                
                # 今日の天気
                today_weather = None
                today_element = soup.select_one(".forecastCity > table td.pict")
                if today_element:
                    img = today_element.select_one("img")
                    if img and img.get("alt"):
                        today_weather = img.get("alt")
                
                # 明日の天気
                tomorrow_weather = None
                tomorrow_element = soup.select_one(".forecastCity > table td.pict + td.pict")
                if tomorrow_element:
                    img = tomorrow_element.select_one("img")
                    if img and img.get("alt"):
                        tomorrow_weather = img.get("alt")
                
                # 気温データ
                temps = {}
                high_elements = soup.select(".forecastCity > table td.temp .high em")
                low_elements = soup.select(".forecastCity > table td.temp .low em")
                
                if high_elements and len(high_elements) >= 2:
                    temps["today_max"] = high_elements[0].text.strip()
                    temps["tomorrow_max"] = high_elements[1].text.strip()
                
                if low_elements and len(low_elements) >= 2:
                    temps["today_min"] = low_elements[0].text.strip()
                    temps["tomorrow_min"] = low_elements[1].text.strip()
                
                # 週間天気
                weekly = {}
                weekly_elements = soup.select(".forecastTable table tr")
                for element in weekly_elements[1:8]:  # ヘッダー行を除いて7日分
                    cells = element.select("td")
                    if len(cells) >= 5:
                        date_elem = cells[0]
                        weather_elem = cells[1]
                        high_elem = cells[3].select_one(".high em")
                        low_elem = cells[3].select_one(".low em")
                        
                        if date_elem and weather_elem:
                            date = date_elem.text.strip()
                            
                            img = weather_elem.select_one("img")
                            weather = img.get("alt") if img and img.get("alt") else None
                            
                            max_temp = high_elem.text.strip() if high_elem else None
                            min_temp = low_elem.text.strip() if low_elem else None
                            
                            weekly[date] = {
                                "weather": weather,
                                "max_temp": max_temp,
                                "min_temp": min_temp
                            }
                
                all_weather_data[region_name] = {
                    "today_weather": today_weather,
                    "tomorrow_weather": tomorrow_weather,
                    "temperatures": temps,
                    "weekly": weekly
                }
                
                # APIリクエスト間隔を空ける（サーバー負荷軽減）
                time.sleep(0.5)
                
            except Exception as e:
                print(f"Error fetching Yahoo Weather data for {region_name}: {e}")
                all_weather_data[region_name] = None
                
        return all_weather_data
    
    def extract_national_weather_overview(self, jma_data, weathermap_data=None, yahoo_data=None) -> Dict[str, Any]:
        """
        全国の天気概況を抽出する
        
        Args:
            jma_data: 気象庁の天気予報データ
            weathermap_data: ウェザーマップの天気予報データ（オプション）
            yahoo_data: Yahoo!天気の天気予報データ（オプション）
            
        Returns:
            Dict[str, Any]: 全国の天気概況
        """
        overview = {
            "today": {},
            "tomorrow": {},
            "week": {}
        }
        
        # 気象庁データから抽出
        if jma_data:
            for region_name, data in jma_data.items():
                if data is None:
                    continue
                    
                try:
                    forecast_data = data.get("forecast", [])
                    if not forecast_data:
                        continue
                    
                    # 今日の天気
                    today_weather = forecast_data[0]["timeSeries"][0]["areas"][0]["weathers"][0]
                    today_weather_code = forecast_data[0]["timeSeries"][0]["areas"][0]["weatherCodes"][0]
                    
                    # 明日の天気
                    tomorrow_weather = forecast_data[0]["timeSeries"][0]["areas"][0]["weathers"][1]
                    tomorrow_weather_code = forecast_data[0]["timeSeries"][0]["areas"][0]["weatherCodes"][1]
                    
                    # 週間天気（週間予報の最初の3日間）
                    week_weathers = []
                    week_weather_codes = []
                    if len(forecast_data) > 1 and "timeSeries" in forecast_data[1]:
                        for i in range(min(3, len(forecast_data[1]["timeSeries"][0]["areas"][0]["weatherCodes"]))):
                            if i > 0:  # 最初の日は今日/明日と重複するので除外
                                code = forecast_data[1]["timeSeries"][0]["areas"][0]["weatherCodes"][i]
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
                    print(f"Error extracting JMA data for {region_name}: {e}")
        
        # ウェザーマップデータで補完
        if weathermap_data:
            for region_name, data in weathermap_data.items():
                if data is None or region_name in overview["today"]:
                    continue
                
                try:
                    today_weather = data.get("today_weather")
                    tomorrow_weather = data.get("tomorrow_weather")
                    
                    if today_weather:
                        overview["today"][region_name] = {
                            "weather": today_weather,
                            "code": self._weather_text_to_code(today_weather)
                        }
                    
                    if tomorrow_weather:
                        overview["tomorrow"][region_name] = {
                            "weather": tomorrow_weather,
                            "code": self._weather_text_to_code(tomorrow_weather)
                        }
                    
                except Exception as e:
                    print(f"Error extracting Weathermap data for {region_name}: {e}")
        
        # Yahoo!天気データで補完
        if yahoo_data:
            for region_name, data in yahoo_data.items():
                if data is None or (region_name in overview["today"] and region_name in overview["tomorrow"]):
                    continue
                
                try:
                    today_weather = data.get("today_weather")
                    tomorrow_weather = data.get("tomorrow_weather")
                    
                    if today_weather and region_name not in overview["today"]:
                        overview["today"][region_name] = {
                            "weather": today_weather,
                            "code": self._weather_text_to_code(today_weather)
                        }
                    
                    if tomorrow_weather and region_name not in overview["tomorrow"]:
                        overview["tomorrow"][region_name] = {
                            "weather": tomorrow_weather,
                            "code": self._weather_text_to_code(tomorrow_weather)
                        }
                    
                except Exception as e:
                    print(f"Error extracting Yahoo Weather data for {region_name}: {e}")
        
        return overview
    
    def extract_national_temperature(self, jma_data, weathermap_data=None, yahoo_data=None) -> Dict[str, Any]:
        """
        全国の気温情報を抽出する
        
        Args:
            jma_data: 気象庁の天気予報データ
            weathermap_data: ウェザーマップの天気予報データ（オプション）
            yahoo_data: Yahoo!天気の天気予報データ（オプション）
            
        Returns:
            Dict[str, Any]: 全国の気温情報
        """
        temperature = {
            "today": {},
            "tomorrow": {}
        }
        
        # 気象庁データから抽出
        if jma_data:
            for region_name, data in jma_data.items():
                if data is None:
                    continue
                    
                try:
                    forecast_data = data.get("forecast", [])
                    if not forecast_data:
                        continue
                    
                    # 気温データがある場合のみ処理
                    if len(forecast_data[0]["timeSeries"]) > 2:
                        # 代表都市の気温を取得
                        city_temps = forecast_data[0]["timeSeries"][2]["areas"][0]["temps"]
                        
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
                    print(f"Error extracting JMA temperature for {region_name}: {e}")
        
        # ウェザーマップデータで補完
        if weathermap_data:
            for region_name, data in weathermap_data.items():
                if data is None:
                    continue
                
                try:
                    temps = data.get("temperatures", {})
                    
                    # 今日の気温がない場合のみ補完
                    if region_name not in temperature["today"] and "today_max" in temps:
                        temperature["today"][region_name] = {
                            "max": temps["today_max"]
                        }
                    
                    # 明日の気温がない場合のみ補完
                    if region_name not in temperature["tomorrow"] and "tomorrow_max" in temps:
                        temperature["tomorrow"][region_name] = {
                            "min": temps.get("tomorrow_min"),
                            "max": temps.get("tomorrow_max")
                        }
                    
                except Exception as e:
                    print(f"Error extracting Weathermap temperature for {region_name}: {e}")
        
        # Yahoo!天気データで補完
        if yahoo_data:
            for region_name, data in yahoo_data.items():
                if data is None:
                    continue
                
                try:
                    temps = data.get("temperatures", {})
                    
                    # 今日の気温がない場合のみ補完
                    if region_name not in temperature["today"] and "today_max" in temps:
                        temperature["today"][region_name] = {
                            "max": temps["today_max"]
                        }
                    
                    # 明日の気温がない場合のみ補完
                    if region_name not in temperature["tomorrow"] and "tomorrow_max" in temps:
                        temperature["tomorrow"][region_name] = {
                            "min": temps.get("tomorrow_min"),
                            "max": temps.get("tomorrow_max")
                        }
                    
                except Exception as e:
                    print(f"Error extracting Yahoo Weather temperature for {region_name}: {e}")
        
        return temperature
    
    def extract_weekly_forecast(self, jma_data, weathermap_data=None, yahoo_data=None) -> Dict[str, Any]:
        """
        週間天気予報を抽出する
        
        Args:
            jma_data: 気象庁の天気予報データ
            weathermap_data: ウェザーマップの天気予報データ（オプション）
            yahoo_data: Yahoo!天気の天気予報データ（オプション）
            
        Returns:
            Dict[str, Any]: 週間天気予報
        """
        weekly = {}
        
        # 気象庁データから抽出（東京を代表として使用）
        if jma_data and "関東甲信" in jma_data and jma_data["関東甲信"] is not None:
            data = jma_data["関東甲信"]
            
            try:
                forecast_data = data.get("forecast", [])
                if len(forecast_data) > 1:
                    # 週間天気予報の日付、天気、降水確率、最高/最低気温を抽出
                    time_defines = forecast_data[1]["timeSeries"][0]["timeDefines"]
                    weather_codes = forecast_data[1]["timeSeries"][0]["areas"][0]["weatherCodes"]
                    pops = forecast_data[1]["timeSeries"][0]["areas"][0]["pops"]
                    
                    # 気温データ
                    if len(forecast_data[1]["timeSeries"]) > 1:
                        temps_min = forecast_data[1]["timeSeries"][1]["areas"][0]["tempsMin"]
                        temps_max = forecast_data[1]["timeSeries"][1]["areas"][0]["tempsMax"]
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
                            "weather": self._code_to_weather_text(weather_codes[i]) if i < len(weather_codes) else None,
                            "pop": pops[i] if i < len(pops) else None,
                            "temp_min": temps_min[i] if i < len(temps_min) else None,
                            "temp_max": temps_max[i] if i < len(temps_max) else None
                        }
            
            except (KeyError, IndexError) as e:
                print(f"Error extracting JMA weekly forecast: {e}")
        
        # ウェザーマップデータで補完
        if not weekly and weathermap_data and "関東甲信" in weathermap_data and weathermap_data["関東甲信"] is not None:
            data = weathermap_data["関東甲信"]
            
            try:
                weekly_data = data.get("weekly", {})
                
                for date, day_data in weekly_data.items():
                    # 日付を整形
                    date_match = re.search(r"(\d+)[^\d]+(\d+)", date)
                    if date_match:
                        month = date_match.group(1)
                        day = date_match.group(2)
                        date_formatted = f"{month}/{day}"
                        
                        weekly[date_formatted] = {
                            "weather": day_data.get("weather"),
                            "weather_code": self._weather_text_to_code(day_data.get("weather")),
                            "temp_min": day_data.get("min_temp"),
                            "temp_max": day_data.get("max_temp"),
                            "pop": None  # 降水確率はウェザーマップでは取得できない
                        }
            
            except Exception as e:
                print(f"Error extracting Weathermap weekly forecast: {e}")
        
        # Yahoo!天気データで補完
        if not weekly and yahoo_data and "関東甲信" in yahoo_data and yahoo_data["関東甲信"] is not None:
            data = yahoo_data["関東甲信"]
            
            try:
                weekly_data = data.get("weekly", {})
                
                for date, day_data in weekly_data.items():
                    # 日付を整形
                    date_match = re.search(r"(\d+)[^\d]+(\d+)", date)
                    if date_match:
                        month = date_match.group(1)
                        day = date_match.group(2)
                        date_formatted = f"{month}/{day}"
                        
                        weekly[date_formatted] = {
                            "weather": day_data.get("weather"),
                            "weather_code": self._weather_text_to_code(day_data.get("weather")),
                            "temp_min": day_data.get("min_temp"),
                            "temp_max": day_data.get("max_temp"),
                            "pop": None  # 降水確率はYahoo!天気でも取得が難しい
                        }
            
            except Exception as e:
                print(f"Error extracting Yahoo Weather weekly forecast: {e}")
        
        return weekly
    
    def get_weather_warnings(self, jma_data) -> List[str]:
        """
        注意報・警報情報を抽出する
        
        Args:
            jma_data: 気象庁の天気予報データ
            
        Returns:
            List[str]: 注意報・警報情報のリスト
        """
        warnings = []
        
        # 各地方の概況から警報・注意報情報を抽出
        for region_name, data in jma_data.items():
            if data is None:
                continue
                
            try:
                overview_data = data.get("overview", {})
                if not overview_data:
                    continue
                
                # 概況テキストから警報・注意報を抽出
                text = overview_data.get("text", "")
                
                # 警報・注意報のキーワードを検索
                keywords = ["警報", "注意報", "特別警報", "警戒", "注意"]
                for keyword in keywords:
                    if keyword in text:
                        # 警報・注意報を含む文を抽出
                        sentences = text.split("。")
                        for sentence in sentences:
                            if keyword in sentence:
                                warning = f"{region_name}地方では{sentence.strip()}"
                                if warning not in warnings:
                                    warnings.append(warning)
                
                # 天気予報データからも警報情報を推測
                forecast_data = data.get("forecast", [])
                if forecast_data:
                    try:
                        today_weather = forecast_data[0]["timeSeries"][0]["areas"][0]["weathers"][0]
                        today_weather_code = forecast_data[0]["timeSeries"][0]["areas"][0]["weatherCodes"][0]
                        
                        # 大雨・雷・強風などのキーワードがあれば警報として扱う
                        alert_keywords = ["大雨", "暴風", "雷", "激しく", "非常に激しく"]
                        for keyword in alert_keywords:
                            if keyword in today_weather:
                                warning = f"{region_name}地方では{keyword}に注意"
                                if warning not in warnings:
                                    warnings.append(warning)
                        
                        # 天気コードから警報情報を推測
                        warning_codes = ["203", "204", "205", "206", "207", "208", "209", "300", "301", "302", "303", "304", "306", "308", "309", "350"]
                        if today_weather_code in warning_codes:
                            if not any(region_name in w for w in warnings):
                                warnings.append(f"{region_name}地方では天候の急変に注意")
                    except (KeyError, IndexError):
                        pass
            
            except Exception as e:
                print(f"Error extracting warnings for {region_name}: {e}")
        
        return warnings
    
    def _weather_text_to_code(self, weather_text):
        """
        天気テキストから気象庁の天気コードを推測する
        
        Args:
            weather_text: 天気テキスト
            
        Returns:
            str: 気象庁の天気コード
        """
        if not weather_text:
            return "200"  # デフォルトは曇り
        
        # 天気コードと天気のマッピングを逆引き
        for code, text in self.weather_code_mapping.items():
            if text in weather_text:
                return code
        
        # キーワードベースでコードを推測
        if "晴" in weather_text and "曇" in weather_text:
            return "101"  # 晴れ時々曇り
        elif "晴" in weather_text:
            return "100"  # 晴れ
        elif "雨" in weather_text and "雪" in weather_text:
            return "304"  # 雨か雪
        elif "雨" in weather_text:
            return "300"  # 雨
        elif "雪" in weather_text:
            return "400"  # 雪
        elif "曇" in weather_text:
            return "200"  # 曇り
        else:
            return "200"  # デフォルトは曇り
    
    def _code_to_weather_text(self, weather_code):
        """
        気象庁の天気コードから天気テキストを取得する
        
        Args:
            weather_code: 気象庁の天気コード
            
        Returns:
            str: 天気テキスト
        """
        if weather_code in self.weather_code_mapping:
            return self.weather_code_mapping[weather_code]
        return "不明"
    
    def get_complete_weather_data(self) -> Dict[str, Any]:
        """
        天気予報原稿作成に必要な全データを取得する
        複数の情報源からデータを取得し、統合する
        
        Returns:
            Dict[str, Any]: 天気予報原稿作成に必要な全データ
        """
        # 気象庁APIからデータ取得
        jma_data = self.get_jma_weather_data()
        
        # ウェザーマップからデータ取得（気象庁データが不完全な場合のバックアップ）
        weathermap_data = None
        if not jma_data or any(data is None for region, data in jma_data.items()):
            print("JMA data incomplete, fetching from Weathermap...")
            weathermap_data = self.get_weathermap_data()
        
        # Yahoo!天気からデータ取得（気象庁・ウェザーマップデータが不完全な場合のバックアップ）
        yahoo_data = None
        if (not jma_data or any(data is None for region, data in jma_data.items())) and \
           (not weathermap_data or any(data is None for region, data in weathermap_data.items())):
            print("JMA and Weathermap data incomplete, fetching from Yahoo Weather...")
            yahoo_data = self.get_yahoo_weather_data()
        
        # 全国の天気概況を抽出
        overview = self.extract_national_weather_overview(jma_data, weathermap_data, yahoo_data)
        
        # 全国の気温情報を抽出
        temperature = self.extract_national_temperature(jma_data, weathermap_data, yahoo_data)
        
        # 週間天気予報を抽出
        weekly = self.extract_weekly_forecast(jma_data, weathermap_data, yahoo_data)
        
        # 注意報・警報情報を抽出
        warnings = self.get_weather_warnings(jma_data)
        
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
            "raw_data": {
                "jma": jma_data,
                "weathermap": weathermap_data,
                "yahoo": yahoo_data
            }
        }
        
        return complete_data

# 単体テスト用
if __name__ == "__main__":
    collector = WeatherDataCollector()
    data = collector.get_complete_weather_data()
    print(json.dumps(data, ensure_ascii=False, indent=2))
