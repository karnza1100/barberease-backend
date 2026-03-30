from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pythainlp

app = FastAPI()

# อนุญาตให้หน้าเว็บ (GitHub Pages) ส่งข้อมูลมาที่เซิร์ฟเวอร์นี้ได้
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ตัวแปรจำลองฐานข้อมูลในหน่วยความจำ (ถ้าปิดโปรแกรมข้อมูลจะหาย)
# ในอนาคตคุณสามารถเชื่อมต่อกับ Database จริงๆ ได้ตรงนี้
database_reviews = []

# โครงสร้างข้อมูลที่รับมาจากหน้าเว็บ
class ReviewModel(BaseModel):
    message: str

@app.post("/api/submit-review")
def submit_review(data: ReviewModel):
    # 1. ตัดคำภาษาไทย (Morphological Level) ตามที่ระบุในรายงาน
    words = pythainlp.word_tokenize(data.message, engine="newmm")
    
    # 2. จำลองการวิเคราะห์ Sentiment (บวก/ลบ)
    # (ในรายงานข้อ 7.2 คุณกำลังพัฒนาส่วนนี้ สามารถนำ Model ของคุณมาใส่ตรงนี้ได้)
    sentiment = "Positive"
    if "ช้า" in data.message or "นาน" in data.message or "ร้อน" in data.message:
        sentiment = "Negative"
        
    review_result = {
        "original_text": data.message,
        "tokens": words,
        "sentiment": sentiment
    }
    
    # บันทึกข้อมูลลงในรายการ
    database_reviews.append(review_result)
    
    return {"status": "success", "data": review_result}

@app.get("/api/get-reviews")
def get_reviews():
    # ดึงข้อมูลรีวิวทั้งหมดส่งกลับไปให้หน้าเว็บของคุณ
    return database_reviews