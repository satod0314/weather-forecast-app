from flask import Flask, render_template, request, jsonify, send_file, url_for
import os
import json
import datetime
import tempfile
from src.weather_data_enhanced import WeatherDataCollector
from src.script_generator_improved import ScriptGenerator

app = Flask(__name__, static_url_path='/static', static_folder='static')

# 現在のスクリプトを保存するグローバル変数
current_script = None

@app.route('/')
def index():
    """メインページを表示"""
    return render_template('index.html')

@app.route('/api/generate_script', methods=['POST'])
def generate_script():
    """天気予報原稿を生成するAPI"""
    global current_script
    
    try:
        # 天気データを取得
        collector = WeatherDataCollector()
        weather_data = collector.get_complete_weather_data()
        
        # 原稿を生成
        generator = ScriptGenerator()
        script = generator.generate_complete_script(weather_data)
        
        # 現在のスクリプトを保存
        current_script = script
        
        return jsonify({"success": True, "script": script})
    except Exception as e:
        print(f"Error generating script: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/regenerate_script', methods=['POST'])
def regenerate_script():
    """天気予報原稿を再生成するAPI"""
    global current_script
    
    if not current_script:
        return jsonify({"success": False, "error": "No script to regenerate"}), 400
    
    try:
        data = request.json
        instruction = data.get('instruction', '')
        
        # 天気データを取得
        collector = WeatherDataCollector()
        weather_data = collector.get_complete_weather_data()
        
        # 原稿を生成
        generator = ScriptGenerator()
        script = generator.generate_complete_script(weather_data)
        
        # 指示に基づいて調整（簡易的な実装）
        if "簡潔" in instruction or "短く" in instruction:
            for key in script:
                if isinstance(script[key], str) and key not in ["date", "forecast_date", "total_chars", "reading_time"]:
                    script[key] = generator._adjust_text_length(script[key], len(script[key]) * 0.8)
        elif "詳しく" in instruction or "長く" in instruction:
            for key in script:
                if isinstance(script[key], str) and key not in ["date", "forecast_date", "total_chars", "reading_time"]:
                    script[key] = generator._adjust_text_length(script[key], len(script[key]) * 1.2)
        
        # 合計文字数を再計算
        total_chars = sum(len(text) for section, text in script.items() if section not in ["date", "forecast_date", "total_chars", "reading_time"])
        script["total_chars"] = total_chars
        
        # 読み上げ時間の目安を再計算
        reading_time = total_chars / 250
        script["reading_time"] = f"{reading_time:.1f}"
        
        # 現在のスクリプトを更新
        current_script = script
        
        return jsonify({"success": True, "script": script})
    except Exception as e:
        print(f"Error regenerating script: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/update_script', methods=['POST'])
def update_script():
    """編集された原稿を更新するAPI"""
    global current_script
    
    if not current_script:
        return jsonify({"success": False, "error": "No script to update"}), 400
    
    try:
        data = request.json
        edited_text = data.get('edited_text', '')
        
        # 編集されたテキストを解析
        lines = edited_text.split('\n')
        
        # 日付と予報対象日を更新
        if len(lines) >= 2:
            current_script["date"] = lines[0]
            current_script["forecast_date"] = lines[1]
        
        # セクションを更新
        current_section = None
        section_text = ""
        
        for line in lines[2:]:
            if line.startswith('【') and line.endswith('】'):
                # 前のセクションを保存
                if current_section and section_text:
                    current_script[current_section] = section_text.strip()
                
                # 新しいセクションを開始
                current_section = line[1:-1]
                section_text = ""
            elif current_section:
                section_text += line + "\n"
        
        # 最後のセクションを保存
        if current_section and section_text:
            current_script[current_section] = section_text.strip()
        
        # 合計文字数を再計算
        total_chars = sum(len(text) for section, text in current_script.items() if section not in ["date", "forecast_date", "total_chars", "reading_time"])
        current_script["total_chars"] = total_chars
        
        # 読み上げ時間の目安を再計算
        reading_time = total_chars / 250
        current_script["reading_time"] = f"{reading_time:.1f}"
        
        return jsonify({"success": True, "script": current_script})
    except Exception as e:
        print(f"Error updating script: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/export_text', methods=['POST'])
def export_text():
    """原稿をテキストファイルとして出力するAPI"""
    global current_script
    
    if not current_script:
        return jsonify({"success": False, "error": "No script to export"}), 400
    
    try:
        # テキストファイルを作成
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.txt', encoding='utf-8') as f:
            f.write(f"{current_script['date']}\n")
            f.write(f"{current_script['forecast_date']}\n\n")
            
            # セクションを順番に出力（現在の全国天気の概況→今後のポイント→全国天気→全国気温→週間予報）
            sections = [
                "現在の全国天気の概況",
                "今後のポイント",
                "全国天気",
                "全国気温",
                "週間予報"
            ]
            
            for section in sections:
                if section in current_script:
                    f.write(f"【{section}】\n")
                    f.write(f"{current_script[section]}\n\n")
            
            f.write(f"合計: {current_script['total_chars']}文字\n")
            f.write(f"読み上げ時間: 約{current_script['reading_time']}分\n")
            
            filename = f.name
        
        # ファイルを送信
        return send_file(filename, as_attachment=True, download_name='天気予報原稿.txt', mimetype='text/plain')
    except Exception as e:
        print(f"Error exporting text: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# デバッグ用ルート
@app.route('/debug')
def debug():
    """デバッグ情報を表示"""
    debug_info = {
        "static_url_path": app.static_url_path,
        "static_folder": app.static_folder,
        "static_files": os.listdir(app.static_folder) if os.path.exists(app.static_folder) else [],
        "image_files": os.listdir(os.path.join(app.static_folder, 'images')) if os.path.exists(os.path.join(app.static_folder, 'images')) else []
    }
    return jsonify(debug_info)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
