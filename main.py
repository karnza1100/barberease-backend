from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pythainlp
from pythainlp.tag import pos_tag

app = FastAPI()

# อนุญาตให้ Frontend ยิงข้อมูลเข้ามาได้ (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ข้อมูลเริ่มต้นจำลอง (Initial Data) ที่มีโครงสร้างแบบละเอียดขึ้น
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
    # 1. ตัดคำภาษาไทย (Morphological Level)
    words = pythainlp.word_tokenize(data.message, engine="newmm", keep_whitespace=False)
    
    # 2. ทำ Part-of-Speech Tagging (Lexical Level)
    # ผลลัพธ์จะได้เป็น list ของ tuple เช่น [('ตัดผม', 'VACT'), ('สวย', 'VATT')]
    pos = pos_tag(words, engine="perceptron", corpus="orchid")
    # แปลง tuple เป็น list เพื่อให้แปลงเป็น JSON และส่งไป Frontend ได้ง่ายขึ้น
    pos_tags_list = [[word, tag] for word, tag in pos]
    
    # 3. วิเคราะห์ Sentiment (บวก/ลบ) 
    sentiment = "Positive"
    negative_keywords = ["ช้า", "นาน", "ร้อน", "แย่", "ไม่ค่อยเย็น", "คิวยาว", "แพง", "ปรับปรุง", "ไม่สวย", "สกปรก"]
    for kw in negative_keywords:
        if kw in data.message:
            sentiment = "Negative"
            break
            
    # 4. แยก Category ตาม Keyword
    category = "ทั่วไป"
    if any(word in data.message for word in ["ช่าง", "ตัด", "สระ", "ไดร์", "ซอย", "ทรง"]):
        category = "คุณภาพงานช่าง"
    elif any(word in data.message for word in ["สะอาด", "แอร์", "ร้าน", "ร้อน", "ที่จอดรถ", "เหม็น"]):
        category = "สถานที่และสิ่งอำนวยความสะดวก"
    elif any(word in data.message for word in ["คิว", "รอ", "จอง", "นัด"]):
        category = "ระบบการจอง"
    elif any(word in data.message for word in ["คุ้ม", "ราคา", "บาท", "ถูก", "แพง"]):
        category = "ราคาและความคุ้มค่า"
        
    # 5. สกัด Keyword สำคัญ (ดึงเฉพาะคำนาม NCMN และคำกริยา VACT/VATT)
    # เพื่อเอาไปโชว์ในช่อง Keywords ของระบบ
    keywords = []
    for word, tag in pos:
        if tag in ["NCMN", "VACT", "VATT"] and len(word) > 1:
            if word not in keywords:
                keywords.append(word)
                
    # ถ้าหา keyword จาก POS ไม่เจอเลย ให้เอาคำแรกๆ ไปใช้แทน
    if not keywords and len(words) > 0:
        keywords = words[:2]

    review_result = {
        "original_text": data.message,
        "tokens": words,
        "pos_tags": pos_tags_list,
        "sentiment": sentiment,
        "category": category,
        "keywords": keywords[:3] # เอาไปแสดงผลแค่ 3 คำเด่นๆ
    }
    
    # บันทึกข้อมูลแบบยัดขึ้นไปไว้บนสุด (เพื่อให้เห็นผลทันทีในตาราง)
    database_reviews.insert(0, review_result)
    
    return {"status": "success", "data": review_result}

# Route สำหรับดึงข้อมูลรีวิวทั้งหมดไปโชว์ที่ Dashboard
@app.get("/api/get-reviews")
def get_reviews():
    return database_reviews