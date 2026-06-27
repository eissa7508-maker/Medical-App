import os
import urllib.parse
import re
import json
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# رقم الواتساب الخاص بالطبيب الاستشاري (يمكنك تعديله لاحقاً)
DOCTOR_WHATSAPP = "249900000000" 

# دالة تنظيف وتوحيد النصوص (Text Normalization) لرفع دقة التعرف على الأعراض
def normalize_text(text):
    if not text:
        return ""
    text = text.strip()
    # إزالة التشكيل والزخارف الطبية
    text = re.sub(r"[\u064B-\u0652]", "", text)
    # توحيد أشكال الهمزات
    text = re.sub(r"[أإآٱ]", "أ", text)
    # توحيد الياء والألف المقصورة
    text = re.sub(r"ى", "ي", text)
    # إسقاط الروابط وعلامات التعريف لتبسيط الكلمة المفتاحية
    text = re.sub(r"\bال", " ", text)
    text = re.sub(r"\bو", " ", text)
    # إزالة الفراغات الزائدة
    text = re.sub(r"\s+", " ", text).strip()
    return text

# 1. صفحة تسجيل الدخول الأساسية
@app.route('/')
@app.route('/login')
def login():
    return render_template('login.html')

# 2. صفحة إنشاء حساب جديد
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        # حفظ الحسابات الجديدة تلقائياً في ملف نصي لمعرفتها لاحقاً
        with open('registered_users.txt', 'a', encoding='utf-8') as f:
            f.write(f"Username: {username}\n")
        return redirect(url_for('login'))
    return render_template('register.html')

# 3. لوحة التحكم الرئيسية للمنظومة
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# 4. صفحة واجهة استقبال وفحص الأعراض
@app.route('/analysis')
def analysis():
    return render_template('analysis.html')

# 5. الخطوة الأولى: دالة معالجة واستخراج التشخيص المبدئي فقط
@app.route('/results', methods=['POST'])
def results():
    if request.method == 'POST':
        symptoms = request.form.get('symptoms', '')
        normalized_input = normalize_text(symptoms)
        
        diagnoses_list = []
        recommended_tests = []
        detected = False
        
        # تحميل قاعدة المعرفة الطبية الثابتة من ملف JSON
        try:
            with open('diseases.json', 'r', encoding='utf-8') as f:
                diseases_data = json.load(f)
        except Exception:
            diseases_data = []

        # محرك الاستدلال: مطابقة الكلمات المفتاحية بالأعراض المدخلة
        for item in diseases_data:
            for key in item.get('keys', []):
                normalized_key = normalize_text(key)
                if normalized_key and normalized_key in normalized_input:
                    detected = True
                    if item.get('disease') not in diagnoses_list:
                        diagnoses_list.append(item.get('disease'))
                    
                    # تجميع الفحوصات المرتبطة تلقائياً
                    tests_info = item.get('tests', '')
                    if "+" in tests_info:
                        split_tests = tests_info.split("+")
                        for test in split_tests:
                            clean_test = test.strip().rstrip('.')
                            if clean_test and clean_test not in recommended_tests:
                                recommended_tests.append(clean_test)
                    else:
                        clean_test = tests_info.strip().rstrip('.')
                        if clean_test and clean_test not in recommended_tests:
                            recommended_tests.append(clean_test)

        final_diagnosis = " و ".join(diagnoses_list) if diagnoses_list else ""
        
        # عرض صفحة التشخيصات أولاً وتمرير قائمة الفحوصات معها كخطوة وسيطة
        return render_template('results.html', 
                               symptoms=symptoms, 
                               detected=detected, 
                               diagnosis=final_diagnosis, 
                               recommended_tests=recommended_tests)
    return redirect(url_for('dashboard'))

# 6. الخطوة الثانية: المسار الجديد المخصص لصفحة الفحوصات الطبية المستقلة والواتساب
@app.route('/tests-page')
def tests_page():
    symptoms = request.args.get('symptoms', '').strip()
    diagnosis = request.args.get('diagnosis', '').strip()
    recommended_tests_raw = request.args.get('tests', '').strip()
    
    recommended_tests = []
    if recommended_tests_raw:
        recommended_tests = [t.strip() for t in recommended_tests_raw.split(',') if t.strip()]
        
    detected = True if diagnosis or recommended_tests else False

    # صياغة وهيكلة نص الرسالة الأكاديمية النهائية لتصديرها للواتساب
    base_message = f"🏥 *تقرير منظومة تشخيص جامعة بخت الرضا*\n\n"
    base_message += f"📝 *الأعراض المدخلة:* {symptoms}\n\n"
    if diagnosis:
        base_message += f"🔍 *التشخيص المبدئي المحتمل:* {diagnosis}\n\n"
    if recommended_tests:
        base_message += f"🧪 *الفحوصات الطبية المطلوبة فوراً:*\n- " + "\n- ".join(recommended_tests)
    else:
        base_message += "⚠️ لم يتم التعرف على نمط الأعراض تلقائياً."
        
    whatsapp_url = f"https://wa.me/{DOCTOR_WHATSAPP}?text={urllib.parse.quote(base_message)}"

    return render_template('tests.html', 
                           symptoms=symptoms,
                           detected=detected,
                           diagnosis=diagnosis,
                           recommended_tests=recommended_tests,
                           whatsapp_url=whatsapp_url)

if __name__ == '__main__':
    app.run(debug=True)