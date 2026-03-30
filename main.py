from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pythainlp
from pythainlp.tag import pos_tag

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=False, 
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mockup Database เริ่มต้น
database_reviews = [
    {
        "id": 1,
        "text": "ตัดผมสวยถูกใจมากครับ ช่างเก็บงานละเอียดดีมาก",
        "original_text": "ตัดผมสวยถูกใจมากครับ ช่างเก็บงานละเอียดดีมาก",
        "tokens": ["ตัดผม", "สวย", "ถูกใจ", "มาก", "ครับ", "ช่าง", "เก็บงาน", "ละเอียด", "ดีมาก"],
        "pos_tags": [["ตัดผม", "VACT"], ["สวย", "VATT"], ["ถูกใจ", "VATT"], ["มาก", "ADVN"]],
        "sentiment": "Positive",
        "category": "คุณภาพงานช่าง",
        "keywords": ["ตัดผม", "ช่าง", "สวย"]
    }
]

class ReviewModel(BaseModel):
    message: str

@app.get("/")
def read_root():
    return {"status": "online", "total_reviews": len(database_reviews)}

@app.post("/api/submit-review")
def submit_review(data: ReviewModel):
    msg = data.message
    words = pythainlp.word_tokenize(msg, engine="newmm", keep_whitespace=False)
    
    pos = pos_tag(words, engine="perceptron", corpus="orchid")
    pos_tags_list = [[word, tag] for word, tag in pos]
    
    # --- [ปรับปรุง: ส่วนจัดหมวดหมู่ Sentiment ให้แม่นยำขึ้น] ---
    sentiment = "Positive" # Default เป็นบวก
    
    # 1. คีย์เวิร์ดที่เป็นลบโดยตรง
    negative_keywords = [
        "ช้า", "นาน", "ร้อน", "แย่", "คิวยาว", "แพง", "ปรับปรุง", "ไม่สวย", 
        "สกปรก", "เหม็น", "เจ็บ", "สั้นไป", "แหว่ง", "ไม่ชอบ", "ห่วย", "หนวกหู",
        "ตัดไม่ตรง", "หน้าบึ้ง", "ไม่ต้อนรับ", "โกง", "เลอะ"
    ]
    
    # 2. คีย์เวิร์ดเชิงปฏิเสธ (ถ้านำหน้าคำดีๆ จะกลายเป็นลบทันที)
    negation_words = ["ไม่", "ห่วย", "เลิก"]
    positive_vibes = ["ดี", "ชอบ", "โอเค", "สะอาด", "สวย", "คุ้ม", "ประทับใจ"]
    
    # เช็กคำลบตรงๆ ก่อน
    if any(neg_kw in msg for neg_kw in negative_keywords):
        sentiment = "Negative"
    
    # เช็กการกลับคำ (เช่น ไม่+ดี, ไม่+ชอบ)
    for neg in negation_words:
        for pos_vibe in positive_vibes:
            if f"{neg}{pos_vibe}" in msg:
                sentiment = "Negative"
                break
                
    # ประโยคพิเศษที่มักจะสลับกัน
    if "ไม่ดี" in msg or "ไม่ค่อย" in msg or "รอนาน" in msg:
        sentiment = "Negative"

    # --- [ส่วนจัดหมวดหมู่ Category] ---
    category = "ทั่วไป"
    if any(word in msg for word in ["ช่าง", "ตัด", "สระ", "ไดร์", "ซอย", "ทรง", "ตัดผม"]):
        category = "คุณภาพงานช่าง"
    elif any(word in msg for word in ["สะอาด", "แอร์", "ร้าน", "ร้อน", "ที่จอดรถ", "เหม็น", "เจ้าของ"]):
        category = "สถานที่และสิ่งอำนวยความสะดวก"
    elif any(word in msg for word in ["คิว", "รอ", "จอง", "นัด", "ชั่วโมง"]):
        category = "ระบบการจอง"
    elif any(word in msg for word in ["คุ้ม", "ราคา", "บาท", "ถูก", "แพง", "เงิน"]):
        category = "ราคาและความคุ้มค่า"
        
    keywords = []
    for word, tag in pos:
        if tag in ["NCMN", "VACT", "VATT"] and len(word) > 1:
            if word not in keywords:
                keywords.append(word)
                
    if not keywords and len(words) > 0:
        keywords = words[:2]

    review_result = {
        "id": len(database_reviews) + 1, 
        "text": msg, 
        "original_text": msg,
        "tokens": words,
        "pos_tags": pos_tags_list,
        "sentiment": sentiment,
        "category": category,
        "keywords": keywords[:3]
    }
    
    database_reviews.insert(0, review_result)
    return review_result

@app.get("/api/get-reviews")
def get_reviews():
    return database_reviews