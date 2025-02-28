import os
from flask import Flask, request, jsonify
import requests
import json

app = Flask(__name__)

# استخدام المتغيرات البيئية لتخزين التوكنات بشكل آمن
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

@app.route("/", methods=["GET"])
def home():
    return "البوت يعمل بنجاح على Railway!", 200

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"}), 200

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        token_sent = request.args.get("hub.verify_token")
        if token_sent == VERIFY_TOKEN:
            return request.args.get("hub.challenge")
        return "Token verification failed", 403

    elif request.method == "POST":
        data = request.get_json()
        for entry in data.get("entry", []):
            for messaging_event in entry.get("messaging", []):
                if "message" in messaging_event:
                    sender_id = messaging_event["sender"]["id"]
                    message_text = messaging_event["message"].get("text", "")
                    if message_text:
                        reply_text = get_gemini_reply(message_text)
                        send_message(sender_id, reply_text)
        return "OK", 200

def get_gemini_reply(user_message):
    url = f"https://generativelanguage.googleapis.com/v1beta2/models/text-bison-001:generateText?key={GEMINI_API_KEY}"
    prompt_text = f"""
    أنت الآن تعمل كخدمة عملاء لقافلة الرحاب، وهي شركة تقدم رحلات عمرة مميزة خلال شهر رمضان بأسعار تنافسية. إليك بعض المعلومات المهمة حول العروض التي نقدمها:
    
    🔊 استعد لتجربة عمرة رمضانية لا تُضاهى!
    🚍 مع قافلة الرحاب، تبدأ رحلتك من الرياض إلى مكة والمدينة بأحدث الباصات المكيفة لعامي 2023 و2024، لضمان راحتك وأمانك.
    
    🏨 استمتع بإقامة فاخرة في فنادق 5، 4، أو 3 نجوم، على بُعد خطوات من الحرم.
    
    💥 تخفيضات خاصة للعائلات والمجموعات – لأن راحتكم أولويتنا!
    
    📅 برامجنا متنوعة لتناسب كل احتياجاتكم:
    - رحلات VIP إلى مكة فقط – كل يوم إثنين وخميس.
    - باقات 3 أيام في مكة فقط أو مع زيارة المدينة المنورة.
    - باقات 5 أيام في مكة فقط أو مع زيارة المدينة المنورة.
    
    💰 سعر الفرد فقط 100 ريال سعودي.
    
    📞 لا تضيع الفرصة! احجز الآن واستمتع بعمرة رمضان كأنها حجة مع الرسول ﷺ.
    للحجز والاستفسار: 0502857299 – اتصال وواتساب.
    
    الآن، قم بالرد على هذا الاستفسار من العميل كما لو كنت ممثل خدمة العملاء:
    {user_message}
    """
    
    payload = {
        "prompt": {"text": prompt_text},
        "temperature": 0.7
    }
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response_data = response.json()
        return response_data.get("candidates", [{}])[0].get("output", "عذرًا، لم أفهم سؤالك. يُرجى التواصل معنا عبر واتساب: 0502857299.")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching response from Gemini API: {e}")
        return "عذرًا، حدث خطأ أثناء جلب الرد. يُرجى المحاولة لاحقًا."

def send_message(recipient_id, message_text):
    url = f"https://graph.facebook.com/v17.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = json.dumps({"recipient": {"id": recipient_id}, "message": {"text": message_text}})
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, data=payload, headers=headers, timeout=10)
        response_data = response.json()
        if "error" in response_data:
            print(f"Facebook API error: {response_data['error']}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending message to Facebook API: {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
