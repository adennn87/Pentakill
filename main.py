from fastapi import FastAPI, Request, Form, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import os
import datetime
from gtts import gTTS
import openai
from tensorflow import keras
import numpy as np
from PIL import Image

# Tải mô hình nhận dạng chữ viết tay
try:
    model = keras.models.load_model("D:/BITPEN/model/handwritten_model.keras")
except Exception as e:
    raise RuntimeError(f"Failed to load model: {str(e)}")

# Tạo ứng dụng FastAPI
app = FastAPI()

# Cấu hình giao diện
templates = Jinja2Templates(directory="frontend")
AUDIO_FOLDER = "frontend/audio"
TEMP_FOLDER = "temp"
CHAT_HISTORY_FILE = "chat_history.txt"

os.makedirs(AUDIO_FOLDER, exist_ok=True)
os.makedirs(TEMP_FOLDER, exist_ok=True)

# OpenAI API key
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise RuntimeError("OPENAI_API_KEY is missing. Please set it in the .env file.")


# Hàm tiền xử lý ảnh
def preprocess_image(image):
    """Tiền xử lý ảnh từ canvas hoặc file tải lên."""
    try:
        image = image.convert("L")  # Chuyển sang ảnh xám
        image = image.resize((28, 28))  # Resize về kích thước 28x28
        image_array = np.array(image).reshape(1, 28, 28, 1) / 255.0  # Chuẩn hóa dữ liệu
        return image_array
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Image processing error: {str(e)}")


# Hàm dự đoán
def predict_image(image_array):
    """Dự đoán ký tự từ ảnh."""
    try:
        predictions = model.predict(image_array)
        return int(np.argmax(predictions))  # Trả về kết quả dự đoán
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


# **1. Endpoint nhận dạng chữ viết từ ảnh tải lên**
@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    """Nhận file ảnh tải lên và trả về dự đoán."""
    temp_file_path = os.path.join(TEMP_FOLDER, file.filename)

    try:
        with open(temp_file_path, "wb") as f:
            f.write(file.file.read())

        # Tiền xử lý ảnh
        image = Image.open(temp_file_path)
        image_array = preprocess_image(image)

        # Dự đoán
        predicted_character = predict_image(image_array)
        return {"prediction": predicted_character}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing the file: {str(e)}")
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


# **2. Endpoint nhận dạng chữ viết từ canvas**
@app.post("/predict-canvas")
async def predict_canvas(file: UploadFile = File(...)):
    """Nhận dữ liệu từ canvas và trả về dự đoán."""
    temp_file_path = os.path.join(TEMP_FOLDER, file.filename)

    try:
        with open(temp_file_path, "wb") as f:
            f.write(file.file.read())

        # Tiền xử lý ảnh
        image = Image.open(temp_file_path)
        image_array = preprocess_image(image)

        # Dự đoán
        predicted_character = predict_image(image_array)
        return {"prediction": predicted_character}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing the canvas data: {str(e)}")
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


# **3. Chatbot GPT-4**
@app.post("/chat", response_class=JSONResponse)
async def chat(user_input: str = Form(...)):
    """Tạo phản hồi từ GPT-4."""
    if not user_input.strip():
        raise HTTPException(status_code=400, detail="Input cannot be empty.")

    try:
        completion = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Bạn là trợ lý AI hỗ trợ người dùng."},
                {"role": "user", "content": user_input},
            ],
        )
        response_text = completion.choices[0].message["content"]

        # Tạo audio từ phản hồi
        tts = gTTS(response_text, lang="vi")
        audio_filename = f"response_audio_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.mp3"
        audio_filepath = os.path.join(AUDIO_FOLDER, audio_filename)
        tts.save(audio_filepath)

        # Lưu lịch sử chat
        with open(CHAT_HISTORY_FILE, "a") as f:
            timestamp = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            f.write(f"{timestamp} - User: {user_input}\n")
            f.write(f"{timestamp} - Bot: {response_text}\n\n")

        return {"user_input": user_input, "response": response_text, "audio_url": f"/frontend/audio/{audio_filename}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chatbot error: {str(e)}")


# **4. Lịch sử chat**
@app.get("/chats", response_class=HTMLResponse)
async def read_chats(request: Request):
    """Hiển thị lịch sử chat."""
    if os.path.exists(CHAT_HISTORY_FILE):
        with open(CHAT_HISTORY_FILE, "r") as f:
            chat_history = f.readlines()
    else:
        chat_history = []

    return templates.TemplateResponse("chats.html", {"request": request, "chat_history": chat_history})


# **5. Trang giao diện chính**
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Giao diện chính."""
    return templates.TemplateResponse("index.html", {"request": request})


# **Chạy server**
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
