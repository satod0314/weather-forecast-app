from flask import Flask, render_template, request, jsonify
import os
import json
import datetime
import traceback
from src.weather_data_enhanced import WeatherDataCollector
from src.script_generator_improved import ScriptGenerator

app = Flask(__name__)

# キャッシュ用のグローバル変数
cached_weather_data = None
cached_script = None
last_update_time = None

@app.route('/')
def index():
    """メインページを表示"""
    return render_template('index.html')

@app.route('/api/generate_script', methods=['POST'])
def generate_script():
    """天気予報原稿を生成するAPI"""
    global cached_weather_data, cached_script, last_update_time
    
    try:
        # 現在時刻を取得
        now = datetime.datetime.now()
        
        # キャッシュが存在し、1時間以内に更新されている場合はキャッシュを使用
        if cached_weather_data and last_update_time and (now - last_update_time).total_seconds() < 3600:
            weather_data = cached_weather_data
        else:
            # 天気データを取得
            collector = WeatherDataCollector()
            weather_data = collector.get_complete_weather_data()
            
            # キャッシュを更新
            cached_weather_data = weather_data
            last_update_time = now
        
        # 原稿を生成
        generator = ScriptGenerator()
        script = generator.generate_complete_script(weather_data)
        
        # 生成した原稿をキャッシュ
        cached_script = script
        
        return jsonify({
            'status': 'success',
            'script': script
        })
    
    except Exception as e:
        print(f"Error generating script: {e}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/regenerate_script', methods=['POST'])
def regenerate_script():
    """天気予報原稿を再生成するAPI"""
    global cached_weather_data, cached_script, last_update_time
    
    try:
        # リクエストからデータを取得
        data = request.get_json()
        instructions = data.get('instructions', '')
        current_script = data.get('current_script', {})
        
        # 現在時刻を取得
        now = datetime.datetime.now()
        
        # キャッシュが存在し、1時間以内に更新されている場合はキャッシュを使用
        if cached_weather_data and last_update_time and (now - last_update_time).total_seconds() < 3600:
            weather_data = cached_weather_data
        else:
            # 天気データを取得
            collector = WeatherDataCollector()
            weather_data = collector.get_complete_weather_data()
            
            # キャッシュを更新
            cached_weather_data = weather_data
            last_update_time = now
        
        # 原稿を生成
        generator = ScriptGenerator()
        
        # 指示に基づいて原稿を調整
        # ここでは簡易的な実装として、指示内容に応じて文字数を調整
        if "簡潔" in instructions or "短く" in instructions:
            generator.target_char_count = 400
        elif "詳しく" in instructions or "長く" in instructions:
            generator.target_char_count = 600
        
        script = generator.generate_complete_script(weather_data)
        
        # 生成した原稿をキャッシュ
        cached_script = script
        
        return jsonify({
            'status': 'success',
            'script': script
        })
    
    except Exception as e:
        print(f"Error regenerating script: {e}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/edit_script', methods=['POST'])
def edit_script():
    """編集された天気予報原稿を保存するAPI"""
    global cached_script
    
    try:
        # リクエストからデータを取得
        data = request.get_json()
        edited_script = data.get('edited_script', {})
        
        # 全体テキストを各セクションに分割
        if "全体" in edited_script:
            full_text = edited_script["全体"]
            sections = full_text.split("\n\n")
            
            # 各セクションを解析
            for section in sections:
                lines = section.strip().split("\n")
                if len(lines) >= 2:
                    section_name = lines[0].strip()
                    section_content = "\n".join(lines[1:]).strip()
                    
                    # 既存のスクリプトに反映
                    if section_name in cached_script:
                        cached_script[section_name] = section_content
        
        # 文字数を再計算
        total_chars = sum(len(text) for section, text in cached_script.items() if section not in ["date", "total_chars", "reading_time"])
        cached_script["total_chars"] = total_chars
        
        # 読み上げ時間の目安（1分あたり250文字と仮定）
        reading_time = total_chars / 250
        cached_script["reading_time"] = f"{reading_time:.1f}"
        
        return jsonify({
            'status': 'success',
            'script': cached_script
        })
    
    except Exception as e:
        print(f"Error editing script: {e}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
