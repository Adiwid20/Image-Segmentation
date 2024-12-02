import os
import io
import numpy as np
import cv2
import shutil
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from tensorflow.keras.models import load_model
from PIL import Image
import uuid
import datetime
from typing import List

# Inisialisasi FastAPI dan model
app = FastAPI()

# Path model (ganti dengan path model Anda yang sesuai)
model = load_model("//Users/macbook-air/M2/DAGO PHKT (AIDA PHASE 3 BACKUP)/ASP/UJICOBA/MODEL/Model_B16E20.keras")

# Direktori untuk menyimpan gambar yang diunggah dan hasil prediksi
UPLOAD_DIR = "uploaded_images"
PREDICT_DIR = "predict_images"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PREDICT_DIR, exist_ok=True)

# Batas ukuran file (10 MB)
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

# Fungsi utilitas
def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_file_size(file: UploadFile):
    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds the 10 MB limit.")
    file.file.seek(0)

def process_image(file: bytes):
    img_array = np.array(Image.open(io.BytesIO(file)))
    img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    img_resized = resize_with_aspect(img_array, (256, 256))
    img_resized = np.expand_dims(img_resized, axis=0)
    return img_resized

def resize_with_aspect(image, size=(256, 256)):
    h, w = image.shape[:2]
    scale = min(size[0] / h, size[1] / w)
    nh, nw = int(h * scale), int(w * scale)
    resized = cv2.resize(image, (nw, nh))
    delta_w, delta_h = size[1] - nw, size[0] - nh
    top, bottom = delta_h // 2, delta_h - delta_h // 2
    left, right = delta_w // 2, delta_w - delta_w // 2
    return cv2.copyMakeBorder(resized, top, bottom, left, right, cv2.BORDER_CONSTANT, value=[0, 0, 0])

def convert_to_rgb(mask, colormap):
    h, w = mask.shape
    rgb_mask = np.zeros((h, w, 3), dtype=np.uint8)
    for cls, color in colormap.items():
        rgb_mask[mask == cls] = color
    return rgb_mask

def add_overlay(original_image, mask_image, alpha=0.5):
    mask_resized = cv2.resize(mask_image, (original_image.shape[1], original_image.shape[0]))
    overlay = cv2.addWeighted(original_image, 1 - alpha, mask_resized, alpha, 0)
    return overlay

def concatenate_images(original_image, overlay_image):
    return np.hstack((original_image, overlay_image))

def get_output_dir():
    date_str = datetime.datetime.now().strftime("%Y%m%d")
    output_dir = os.path.join(PREDICT_DIR, date_str)
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def delete_file(filename: str, directory: str) -> bool:
    file_path = os.path.join(directory, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    return False

def delete_all_files(directory: str) -> int:
    count = 0
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)
            count += 1
    return count

# Endpoint CRUD
@app.post("/add-images/")
async def add_images(files: List[UploadFile] = File(...)):
    try:
        uploaded_files = []
        for file in files:
            if not allowed_file(file.filename):
                raise HTTPException(status_code=400, detail=f"Invalid file type: {file.filename}")
            validate_file_size(file)

            file_path = os.path.join(UPLOAD_DIR, os.path.basename(file.filename))
            if os.path.exists(file_path):
                raise HTTPException(status_code=400, detail=f"File '{file.filename}' already exists.")

            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            uploaded_files.append(file.filename)

        # Mengembalikan gambar pertama yang di-upload
        file_path = os.path.join(UPLOAD_DIR, uploaded_files[0])
        with open(file_path, "rb") as img_file:
            img = img_file.read()
            pil_img = Image.open(io.BytesIO(img))
            img_byte_arr = io.BytesIO()
            pil_img.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
        
        return StreamingResponse(img_byte_arr, media_type="image/png")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# @app.get("/list-images/")
# async def list_images():
#     try:
#         files = os.listdir(UPLOAD_DIR)
#         if files:
#             file_path = os.path.join(UPLOAD_DIR, files[0])
#             with open(file_path, "rb") as img_file:
#                 img = img_file.read()
#                 pil_img = Image.open(io.BytesIO(img))
#                 img_byte_arr = io.BytesIO()
#                 pil_img.save(img_byte_arr, format='PNG')
#                 img_byte_arr.seek(0)
            
#             return StreamingResponse(img_byte_arr, media_type="image/png")
        
#         raise HTTPException(status_code=404, detail="No images found")
    
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

@app.get("/list-images/")
async def list_images():
    """Endpoint untuk mendapatkan daftar gambar yang telah diunggah."""
    try:
        files = os.listdir(UPLOAD_DIR)
        return {"images": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    
@app.delete("/delete-image/{filename}")
async def delete_image(filename: str):
    try:
        if delete_file(filename, UPLOAD_DIR):
            # Mengembalikan gambar kosong sebagai status penghapusan
            status_image = np.zeros((256, 256, 3), dtype=np.uint8)
            pil_img = Image.fromarray(status_image)
            img_byte_arr = io.BytesIO()
            pil_img.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
            return StreamingResponse(img_byte_arr, media_type="image/png")
        else:
            raise HTTPException(status_code=404, detail="Image not found")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/delete-all-images/")
async def delete_all_images():
    try:
        deleted_upload = delete_all_files(UPLOAD_DIR)
        deleted_predict = delete_all_files(PREDICT_DIR)
        
        # Mengembalikan gambar kosong sebagai status penghapusan
        status_image = np.zeros((256, 256, 3), dtype=np.uint8)
        pil_img = Image.fromarray(status_image)
        img_byte_arr = io.BytesIO()
        pil_img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        return StreamingResponse(img_byte_arr, media_type="image/png")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict/")
async def predict():
    try:
        # Memanggil endpoint list-images untuk mendapatkan daftar gambar
        response = await list_images()  # Mendapatkan daftar gambar dari /list-images
        files = response["images"]
        
        if not files:
            raise HTTPException(status_code=404, detail="No images found in the upload directory")
        
        processed_images = []
        output_dir = get_output_dir()

        for image_name in files:
            file_path = os.path.join(UPLOAD_DIR, image_name)
            if not os.path.isfile(file_path):
                continue  # Skip jika bukan file

            with open(file_path, "rb") as img_file:
                img = img_file.read()
                img_array = process_image(img)

                # Prediksi dengan model
                prediction = model.predict(img_array)
                prediction_class = np.argmax(prediction, axis=-1)[0]

                # Colormap untuk overlay
                colormap = {
                    0: [255, 0, 0],  # Kelas 0, merah
                    1: [0, 0, 255],  # Kelas 1, biru
                    2: [0, 255, 0],  # Kelas 2, hijau
                }

                # Konversi prediksi ke RGB mask
                rgb_mask = convert_to_rgb(prediction_class, colormap)
                original_image = cv2.cvtColor(img_array[0], cv2.COLOR_BGR2RGB)
                overlay_image = add_overlay(original_image, rgb_mask)
                final_image = concatenate_images(original_image, overlay_image)

                # Menyimpan hasil prediksi
                pil_img = Image.fromarray(final_image)
                img_byte_arr = io.BytesIO()
                pil_img.save(img_byte_arr, format='PNG')
                img_byte_arr.seek(0)

                output_image_path = os.path.join(output_dir, f"processed_{uuid.uuid4().hex}_{image_name}")
                with open(output_image_path, "wb") as f:
                    f.write(img_byte_arr.getvalue())

                processed_images.append({
                    "filename": os.path.basename(output_image_path),
                    "url": f"/predict_images/{os.path.basename(output_image_path)}"
                })
        
        if processed_images:
            # Mengembalikan gambar hasil prediksi pertama
            with open(os.path.join(output_dir, processed_images[0]["filename"]), "rb") as img_file:
                img = img_file.read()
                pil_img = Image.open(io.BytesIO(img))
                img_byte_arr = io.BytesIO()
                pil_img.save(img_byte_arr, format='PNG')
                img_byte_arr.seek(0)
            
            return StreamingResponse(img_byte_arr, media_type="image/png")

        raise HTTPException(status_code=500, detail="No images processed successfully")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

# Jalankan aplikasi jika file dijalankan langsung
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)