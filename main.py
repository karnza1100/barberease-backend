from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pythainlp

app = FastAPI()

# อนุญาตให้ Frontend ยิงข้อมูลเข้ามาได้ (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ข้อมูลเริ่มต้นจำลอง (Initial Data) เพื่อให้แดชบอร์ดมีข้อมูลตั้งแต่เปิดมา
database_reviews = [
    {
        "original_text": "ตัดผมสวยถูกใจมากครับ ช่างเก็บงานละเอียดดีมาก",
        "tokens": ["ตัดผม", "สวย", "ถูกใจ", "มาก", "ช่าง", "เก็บงาน", "ละเอียด"],
        "sentiment": "Positive",
        "category": "คุณภาพงานช่าง"
    },
    {
        "original_text": "แอร์ไม่ค่อยเย็น เลย แถมรอนานเกือบชั่วโมง",
        "tokens": ["แอร์", "ไม่", "ค่อย", "เย็น", "แถม", "รอ", "นาน", "เกือบ", "ชั่วโมง"],
        "sentiment": "Negative",
        "category": "สถานที่และสิ่งอำนวยความสะดวก"
    },
    {
        "original_text": "จองคิวตอนบ่ายสอง ได้ตัดจริงบ่ายสองครึ่ง ถือว่าโอเคครับ",
        "tokens": ["จองคิว", "บ่ายสอง", "ตัด", "จริง", "บ่ายสองครึ่ง"],
        "sentiment": "Positive",
        "category": "ระบบการจอง"
    }
]

# โครงสร้างข้อมูลที่รับมาจากหน้าเว็บ
class ReviewModel(BaseModel):
    message: str

@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "BarberEase API is running successfully!",
        "total_reviews": len(database_reviews)
    }

# Route สำหรับรับข้อมูลรีวิว
@app.post("/api/submit-review")
def submit_review(data: ReviewModel):
    # 1. ตัดคำภาษาไทย (Morphological Level) ด้วย PyThaiNLP
    words = pythainlp.word_tokenize(data.message, engine="newmm")
    
    # 2. วิเคราะห์ Sentiment (บวก/ลบ) เบื้องต้น
    sentiment = "Positive"
    negative_keywords = ["ช้า", "นาน", "ร้อน", "แย่", "ไม่ค่อยเย็น", "คิวยาว", "แพง", "ปรับปรุง"]
    for kw in negative_keywords:
        if kw in data.message:
            sentiment = "Negative"
            break
            
    # 3. แยก Category (เพื่อให้หน้าเว็บนำไปวาดกราฟได้)
    category = "ทั่วไป"
    if "ช่าง" in data.message or "ตัด" in data.message or "สระ" in data.message:
        category = "คุณภาพงานช่าง"
    elif "สะอาด" in data.message or "แอร์" in data.message or "ร้าน" in data.message or "ร้อน" in data.message:
        category = "สถานที่และสิ่งอำนวยความสะดวก"
    elif "คิว" in data.message or "รอ" in data.message or "จอง" in data.message:
        category = "ระบบการจอง"
    elif "คุ้ม" in data.message or "ราคา" in data.message or "บาท" in data.message or "ถูก" in data.message:
        category = "ราคาและความคุ้มค่า"
        
    review_result = {
        "original_text": data.message,
        "tokens": words,
        "sentiment": sentiment,
        "category": category
    }
    
    # บันทึกข้อมูลแบบยัดขึ้นไปไว้บนสุด (เพื่อให้เห็นผลทันทีในตาราง)
    database_reviews.insert(0, review_result)
    
    return {"status": "success", "data": review_result}

# Route สำหรับดึงข้อมูลรีวิวทั้งหมดไปโชว์ที่ Dashboard
@app.get("/api/get-reviews")
def get_reviews():
    return database_reviews