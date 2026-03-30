from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pythainlp
from pythainlp.tag import pos_tag

app = FastAPI()

# --- ปรับปรุงเรื่อง CORS ให้รองรับการเชื่อมต่อข้ามโดเมน ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=False, 
    allow_methods=["*"],
    allow_headers=["*"],
)

database_reviews = [
    {
        "original_text": "ตัดผมสวยถูกใจมากครับ ช่างเก็บงานละเอียดดีมาก",
        "tokens": ["ตัดผม", "สวย", "ถูกใจ", "มาก", "ครับ", "ช่าง", "เก็บงาน", "ละเอียด", "ดีมาก"],
        "pos_tags": [["ตัดผม", "VACT"], ["สวย", "VATT"], ["ถูกใจ", "VATT"], ["มาก", "ADVN"], ["ครับ", "NCMN"], ["ช่าง", "NCMN"], ["เก็บงาน", "VACT"], ["ละเอียด", "VATT"], ["ดีมาก", "ADVN"]],
        "sentiment": "Positive",
        "category": "คุณภาพงานช่าง",
        "keywords": ["ตัดผม", "ช่าง", "สวย"]
    },
    {
        "original_text": "แอร์ไม่ค่อยเย็น แถมรอนานเกือบชั่วโมง",
        "tokens": ["แอร์", "ไม่ค่อย", "เย็น", "แถม", "รอ", "นาน", "เกือบ", "ชั่วโมง"],
        "pos_tags": [["แอร์", "NCMN"], ["ไม่ค่อย", "ADVN"], ["เย็น", "VATT"], ["แถม", "CONJ"], ["รอ", "VACT"], ["นาน", "VATT"], ["เกือบ", "ADVN"], ["ชั่วโมง", "CNTM"]],
        "sentiment": "Negative",
        "category": "สถานที่และสิ่งอำนวยความสะดวก",
        "keywords": ["แอร์", "รอ", "นาน"]
    }
]

class ReviewModel(BaseModel):
    message: str

@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "BarberEase API is running successfully!",
        "total_reviews": len(database_reviews)
    }

@app.post("/api/submit-review")
def submit_review(data: ReviewModel):
    words = pythainlp.word_tokenize(data.message, engine="newmm", keep_whitespace=False)
    
    # ดึง tuple POS Tag
    pos = pos_tag(words, engine="perceptron", corpus="orchid")
    pos_tags_list = [[word, tag] for word, tag in pos]
    
    # --- [ส่วนจัดหมวดหมู่ Sentiment] ---
    sentiment = "Positive"
    
    negation_keywords = ["ไม่มี", "ไม่ค่อย", "ไม่ค่อยดี", "ไม่ค่อยสวย", "ไม่ประทับใจ", "แย่"]
    negative_keywords = ["ช้า", "นาน", "ร้อน", "แย่", "คิวยาว", "แพง", "ปรับปรุง", "ไม่สวย", "สกปรก", "เหม็น", "เจ็บ", "สั้นไป", "แหว่ง"]
    
    all_negatives = negation_keywords + negative_keywords
    
    for kw in all_negatives:
        if kw in data.message:
            sentiment = "Negative"
            break
            
    # --- [ส่วนจัดหมวดหมู่ Category] ---
    category = "ทั่วไป"
    if any(word in data.message for word in ["ช่าง", "ตัด", "สระ", "ไดร์", "ซอย", "ทรง"]):
        category = "คุณภาพงานช่าง"
    elif any(word in data.message for word in ["สะอาด", "แอร์", "ร้าน", "ร้อน", "ที่จอดรถ", "เหม็น"]):
        category = "สถานที่และสิ่งอำนวยความสะดวก"
    elif any(word in data.message for word in ["คิว", "รอ", "จอง", "นัด"]):
        category = "ระบบการจอง"
    elif any(word in data.message for word in ["คุ้ม", "ราคา", "บาท", "ถูก", "แพง"]):
        category = "ราคาและความคุ้มค่า"
        
    keywords = []
    for word, tag in pos:
        if tag in ["NCMN", "VACT", "VATT"] and len(word) > 1:
            if word not in keywords:
                keywords.append(word)
                
    if not keywords and len(words) > 0:
        keywords = words[:2]

    # --- ปรับโครงสร้างข้อมูลที่ส่งกลับไปให้ตรงกับที่ Frontend ต้องการ ---
    review_result = {
        "id": len(database_reviews) + 1, 
        "text": data.message, 
        "original_text": data.message,
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