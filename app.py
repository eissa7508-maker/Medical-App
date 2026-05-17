from flask import Flask, render_template, request, jsonify
import json
import os

app = Flask(__name__)

# تحميل ملف الأمراض الباطنية
def load_diseases():
    # نستخدم utf-8 لضمان قراءة اللغة العربية بدون مشاكل رموز
    with open('diseases.json', 'r', encoding='utf-8') as f:
        return json.load(f)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/check', methods=['POST'])
def check_symptoms():
    try:
        data = request.get_json()
        if not data:
            return jsonify([])
            
        user_symptoms = data.get('symptoms', '').lower()
        # استقبال متغير اللغة حتى لو لم نستخدمه في الفلترة لمنع تعارض الـ Fetch
        user_lang = data.get('lang', 'ar') 
        
        if not user_symptoms.strip():
            return jsonify([])
            
        all_diseases = load_diseases()
        matched_results = []
        
        # الفحص والمقاطعة بناءً على الكلمات المفتاحية
        for item in all_diseases:
            for key in item.get('keys', []):
                if key in user_symptoms:
                    matched_results.append({
                        "disease": item['disease'],
                        "tests": item['tests']
                    })
                    break  # الانتقال للمرض التالي بمجرد المطابقة
                    
        return jsonify(matched_results)
        
    except Exception as e:
        # في حال حدوث أي خطأ غير متوقع يرجع مصفوفة فارغة بدل أن ينهار السيرفر
        print(f"Error: {e}")
        return jsonify([])

if __name__ == '__main__':
    app.run(debug=True)