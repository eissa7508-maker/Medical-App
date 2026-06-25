from flask import Flask, render_template, request, redirect, url_for
import urllib.parse
import json
import os
import re

app = Flask(__name__)
app.secret_key = "bakht_alrida_secret"

DOCTOR_WHATSAPP = "249123456789"

def normalize_text(text):
    if not text:
        return ""
    text = str(text).lower().strip()
    text = re.sub(r'[\u064B-\u0652]', '', text) 
    text = re.sub(r'[أإآٱ]', 'ا', text)         
    text = re.sub(r'[ىي]', 'ي', text)          
    text = re.sub(r'[ة]', 'ه', text)           
    text = re.sub(r'\b(ال|بال|وال|لل|فال|في)\b', '', text) 
    return " ".join(text.split())

def load_medical_database():
    json_path = os.path.join(app.root_path, 'diseases.json')
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error: {e}")
            return []
    return []

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        return redirect(url_for('dashboard'))
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/analysis')
def analysis():
    category = request.args.get('category', '')
    placeholder_text = "حمى داخلية مستمرة وقشعريرة بالجسد"
    
    if category == 'digestive':
        placeholder_text = "اكتب أعراض الجهاز الهضمي هنا... (مثال: ألم شديد في فم المعدة مع حموضة)"
    elif category == 'fevers':
        placeholder_text = "اكتب أعراض الحميات هنا... (مثال: قشعريرة، ارتفاع درجة الحرارة، صداع مستمر)"
    elif category == 'colon':
        placeholder_text = "اكتب أعراض القولون هنا... (مثال: انتفاخ، غازات، تقلصات أسفل البطن)"
        
    return render_template('analysis.html', placeholder_text=placeholder_text)

# تأمين دالة تغيير اللغة لتعود للوحة التحكم بشكل مستقر إذا تم استدعاؤها
@app.route('/change-lang')
def change_lang():
    return redirect(url_for('dashboard'))

@app.route('/results', methods=['GET', 'POST'])
def results():
    symptoms = request.form.get('symptoms', '').strip()
    if not symptoms:
        symptoms = request.args.get('symptoms', '').strip()

    clean_input = normalize_text(symptoms)
    medical_db = load_medical_database()
    
    detected = False
    diagnoses_list = []
    recommended_tests = []

    if clean_input:
        for item in medical_db:
            disease_name = item.get("disease", "")
            tests_info = item.get("tests", "")
            keywords = item.get("keys", [])
            
            match_found = False
            for key in keywords:
                clean_key = normalize_text(key)
                if not clean_key:
                    continue
                if (clean_key in clean_input) or (clean_input in clean_key):
                    match_found = True
                    break

            if match_found:
                detected = True
                if disease_name not in diagnoses_list:
                    diagnoses_list.append(disease_name)
                
                if "+" in tests_info:
                    split_tests = tests_info.split("+")
                    for test in split_tests:
                        clean_test = test.strip().rstrip('.')
                        if clean_test and clean_test not in recommended_tests:
                            recommended_tests.append(clean_test)
                else:
                    if tests_info and tests_info.strip().rstrip('.') not in recommended_tests:
                        recommended_tests.append(tests_info.strip().rstrip('.'))

    final_diagnosis = " + و ".join(diagnoses_list) if diagnoses_list else ""

    base_message = f"🏥 *تقرير منظومة تشخيص جامعة بخت الرضا*\n\n"
    base_message += f"📝 *الأعراض المدخلة:* {symptoms}\n\n"
    if detected:
        base_message += f"🔍 *التشخيص المبدئي المحتمل:*\n- " + "\n- ".join(diagnoses_list) + "\n\n"
        base_message += f"🧪 *الفحوصات الطبية المطلوبة فوراً:*\n- " + "\n- ".join(recommended_tests)
    else:
        base_message += "⚠️ لم يتم التعرف على نمط الأعراض تلقائياً."
        
    whatsapp_url = f"https://wa.me/{DOCTOR_WHATSAPP}?text={urllib.parse.quote(base_message)}"

    return render_template('results.html', 
                           symptoms=symptoms, 
                           detected=detected, 
                           diagnosis=final_diagnosis, 
                           recommended_tests=recommended_tests,
                           whatsapp_url=whatsapp_url)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)