from flask import Flask, request, abort
from linebot.v3.messaging import MessagingApi
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageMessage, ImageSendMessage
from tempfile import NamedTemporaryFile
import os
import cv2

from keras.models import load_model
from keras.preprocessing.image import load_img, img_to_array
import numpy as np
# Replace with your actual channel access token and secret
line_bot_api = LineBotApi('ELerOTczqsgDjtK7550HOKMoRN0rlXMDA00Hox0HnbFMKLMAlj0BbJqKbKZ1uPve0A/43R7G8KujRkicjukFOPfcgthBYm3oz44T0HEyEvHWMGDPN5GkhWUQ+NAfgxHygwfU+cjH6SYX5dYjo4SCTAdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('03b3ea683acc3e11ff122f432f64d9ff')

app = Flask(__name__)

# Webhook route for LINE Messaging API
@app.route('/webhook', methods=['GET','POST'])
def webhook():
    # Get X-Line-Signature header and request body
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # Handle webhook events
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)  

    return 'Connection'  

# Event handler for text messages
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # Extract message text from the event
    message_text = event.message.text

    # Reply to the user with the same message
    reply_message = TextSendMessage(text=message_text)
    line_bot_api.reply_message(event.reply_token, reply_message)

# Event handler for images messages
    
model = load_model("model.h5")

@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    # รับข้อมูลรูปภาพ
    message_content = line_bot_api.get_message_content(event.message.id)

    # ตั้งชื่อไฟล์
    filename = f"image_{event.message.id}.jpg"

    # บันทึกไฟล์
    with open(filename, "wb") as f:
        for chunk in message_content.iter_content():
            f.write(chunk)

    # อ่านรูปภาพ
    img1 = cv2.imread(filename)

    # แปลงสี
    img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2RGB)

    # ปรับขนาด
    img1 = cv2.resize(img1, (224, 224))

    # แปลงเป็น array
    img1 = np.array(img1) / 255.0

    # เปลี่ยนมิติ
    img1 = np.reshape(img1, (1, 224, 224, 3))

    # ทำนาย
    prediction = model.predict(img1)

    # ดึงคลาสและความน่าจะเป็น
    label = ['Anthracnose', 'Healthy']
    result = label[np.argmax(prediction)]
    percen = prediction[0][np.argmax(prediction)]*100

    # แสดงผลลัพธ์
    # print(prediction)
    # print(f"ความน่าจะเป็น:{prediction[0][np.argmax(prediction)]}")
    # print(f"คลาสที่ทำนาย: {result}")

    # ส่งผลลัพธ์กลับไปยังผู้ใช้
    line_bot_api.reply_message(
        event.reply_token,
        [
            TextSendMessage(text=f"เป็นใบ {result}"),
            TextSendMessage(text=f"โอกาศ {round(percen,2)}%"),
            TextSendMessage(text=f"{prediction}")

        ],
    )
if __name__ == '__main__':
    app.run(port=8000,debug=True)
    
