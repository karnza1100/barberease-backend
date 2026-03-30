from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pythainlp
from typing import List

app = FastAPI()

# อนุญาตให้หน้าเว็บ (GitHub Pages) ส่งข้อมูลมาที่เซิร์ฟเวอร์นี้ได้
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ตัวแปรจำลองฐานข้อมูลในหน่วยความจำ (ถ้าปิดโปรแกรมข้อมูลจะหาย)
database_reviews = []

# โครงสร้างข้อมูลที่รับมาจากหน้าเว็บ
class ReviewModel(BaseModel):
    message: str

# 1. เพิ่ม Route หน้าแรกเพื่อแก้ปัญหา 404 Not Found
@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "BarberEase API is running successfully!",
        "total_reviews": len(database_reviews)
    }

# 2. Route สำหรับรับข้อมูลรีวิว
@app.post("/api/submit-review")
def submit_review(data: ReviewModel):
    # 2.1 ตัดคำภาษาไทย (Morphological Level) ด้วย PyThaiNLP
    words = pythainlp.word_tokenize(data.message, engine="newmm")
    
    # 2.2 วิเคราะห์ Sentiment (บวก/ลบ) เบื้องต้น
    sentiment = "Positive"
    negative_keywords = ["ช้า", "นาน", "ร้อน", "แย่", "ไม่ค่อยเย็น", "คิวยาว", "แพง"]
    for kw in negative_keywords:
        if kw in data.message:
            sentiment = "Negative"
            break
            
    # 2.3 เพิ่มการจำลองแยก Category (เพื่อให้หน้าเว็บนำไปวาดกราฟได้สวยงาม)
    category = "ทั่วไป"
    if "ช่าง" in data.message or "ตัด" in data.message:
        category = "คุณภาพงานช่าง"
    elif "สะอาด" in data.message or "แอร์" in data.message or "ร้าน" in data.message:
        category = "สถานที่และสิ่งอำนวยความสะดวก"
    elif "คิว" in data.message or "รอ" in data.message or "จอง" in data.message:
        category = "ระบบการจอง"
    elif "คุ้ม" in data.message or "ราคา" in data.message or "บาท" in data.message or "ถูก" in data.message:
        category = "ราคาและความคุ้มค่า"
        
    review_result = {
        "original_text": data.message,
        "tokens": words,
        "sentiment": sentiment,
        "category": category  # เพิ่มเพื่อให้หน้าเว็บดึงไปจัดหมวดหมู่ได้
    }
    
    # บันทึกข้อมูลลงในรายการ
    database_reviews.append(review_result)
    
    return {"status": "success", "data": review_result}

# 3. Route สำหรับดึงข้อมูลรีวิวทั้งหมดไปโชว์ที่ Dashboard
@app.get("/api/get-reviews")
def get_reviews():
    # ดึงข้อมูลรีวิวทั้งหมดส่งกลับไปให้หน้าเว็บของคุณ
    return database_reviews