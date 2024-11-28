import io
import numpy as np
import cv2
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from tensorflow.keras.models import load_model
from PIL import Image

# Inisialisasi aplikasi FastAPI
app = FastAPI()

# Load model segmentasi
model = load_model("/Users/macbook-air/Documents/DAGO PHKT (AIDA PHASE 3 BACKUP)/ASP/UJICOBA/MODEL/Model_B16E20.h5")

# Fungsi untuk mengubah gambar menjadi array numpy dan mengubah warna dari BGR ke RGB
def process_image(file):
    img_array = np.array(Image.open(io.BytesIO(file)))  # Convert image to numpy array
    img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)  # Convert RGB to BGR
    img_resized = cv2.resize(img_array, (256, 256))  # Resize if necessary
    img_resized = np.expand_dims(img_resized, axis=0)  # Add batch dimension for model input
    return img_resized

# Fungsi untuk mengonversi mask menjadi gambar RGB
def convert_to_rgb(mask, colormap):
    h, w = mask.shape
    rgb_mask = np.zeros((h, w, 3), dtype=np.uint8)
    for cls, color in colormap.items():
        rgb_mask[mask == cls] = color
    return rgb_mask

# Fungsi untuk menambahkan overlay pada gambar asli dan hasil segmentasi
def add_overlay(original_image, mask_image, alpha=0.5):
    # Resize mask_image agar sesuai dengan ukuran original_image
    mask_resized = cv2.resize(mask_image, (original_image.shape[1], original_image.shape[0]))
    # Menggunakan alpha blending untuk overlay
    overlay = cv2.addWeighted(original_image, 1 - alpha, mask_resized, alpha, 0)
    return overlay

# Fungsi untuk menggabungkan gambar asli dan overlay dalam satu gambar
def concatenate_images(original_image, overlay_image):
    # Gabungkan gambar secara horizontal atau vertikal (disesuaikan dengan kebutuhan)
    return np.hstack((original_image, overlay_image))  # Menggabungkan secara horizontal

# Endpoint untuk melakukan segmentasi
@app.post("/predict/")
async def predict(file: UploadFile = File(...)):
    try:
        # Baca file yang diupload dan proses
        img = await file.read()
        
        # Cek apakah file bisa dibuka sebagai gambar
        try:
            image = Image.open(io.BytesIO(img))
        except Exception as e:
            raise HTTPException(status_code=400, detail="Invalid image file")

        # Proses gambar untuk model
        img_array = process_image(img)
        
        # Prediksi menggunakan model segmentasi
        prediction = model.predict(img_array)
        prediction_class = np.argmax(prediction, axis=-1)[0]  # Ambil kelas dengan probabilitas tertinggi
        
        # Buat colormap untuk konversi ke warna RGB
        colormap = {
            0: [255, 0, 0],  # Warna untuk kelas 0
            1: [0, 0, 255],  # Warna untuk kelas 1
            2: [0, 255, 0]}  # Warna untuk kelas 2  

        # Konversi hasil prediksi ke gambar RGB
        rgb_mask = convert_to_rgb(prediction_class, colormap)
        
        # Ubah gambar asli (aslinya juga sudah ada dalam format numpy array)
        original_image = cv2.cvtColor(img_array[0], cv2.COLOR_BGR2RGB)
        
        # Tambahkan overlay pada gambar asli dan mask
        overlay_image = add_overlay(original_image, rgb_mask)

        # Gabungkan gambar asli dan overlay menjadi satu gambar
        final_image = concatenate_images(original_image, overlay_image)

        # Konversi hasil gabungan menjadi gambar dan kirimkan sebagai response
        pil_img = Image.fromarray(final_image)
        img_byte_arr = io.BytesIO()
        pil_img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        return StreamingResponse(img_byte_arr, media_type="image/png")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Menjalankan server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)