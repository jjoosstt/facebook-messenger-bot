from flask import Flask, request
import requests
import json
import os  # لاستيراد مكتبة التعامل مع البيئة

app = Flask(__name__)

# إعدادات فيسبوك (يتم قراءتها من المتغيرات البيئية)
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")  
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")  

# إعدادات Gemini API (يتم قراءتها من المتغيرات البيئية)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# نقطة نهاية Webhook
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        token_sent = request.args.get("hub.verify_token")
        if token_sent == VERIFY_TOKEN:
            return request.args.get("hub.challenge")
        return "Token verification failed", 403

    elif request.method == "POST":
        data = request.get_json()
        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:
                if "message" in messaging_event:
                    sender_id = messaging_event["sender"]["id"]
                    message_text = messaging_event["message"]["text"]
                    reply_text = get_gemini_reply(message_text)
                    send_message(sender_id, reply_text)
        return "OK", 200

# استدعاء API جيمناي لإنشاء ردود ذكية
def get_gemini_reply(user_message):
    url = f"https://generativelanguage.googleapis.com/v1beta2/models/text-bison-001:generateText?key={GEMINI_API_KEY}"
    payload = {
        "prompt": {"text": f"قم بالرد على هذا الاستفسار كما لو كنت خدمة العملاء لشركة قافلة الرحاب:\n\n{user_message}"},
        "temperature": 0.7
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)
    return response.json().get("candidates", [{}])[0].get("output", "عذرًا، لم أفهم سؤالك.")

# إرسال الرسالة إلى فيسبوك ماسنجر
def send_message(recipient_id, message_text):
    url = f"https://graph.facebook.com/v17.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = json.dumps({"recipient": {"id": recipient_id}, "message": {"text": message_text}})
    headers = {"Content-Type": "application/json"}
    requests.post(url, data=payload, headers=headers)

if __name__ == "__main__":
    app.run(port=5000, debug=True)
