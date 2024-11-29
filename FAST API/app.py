import io
import numpy as np
import cv2
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from tensorflow.keras.models import load_model
from PIL import Image

# run in terminal : uvicorn app:app --reload   

app = FastAPI()


model = load_model("//Users/macbook-air/M2/DAGO PHKT (AIDA PHASE 3 BACKUP)/ASP/UJICOBA/MODEL/Model_B16E20.keras")

def process_image(file):
    img_array = np.array(Image.open(io.BytesIO(file)))  # Convert image to numpy array
    img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)  # Convert RGB to BGR
    img_resized = cv2.resize(img_array, (256, 256))  
    img_resized = np.expand_dims(img_resized, axis=0) 
    return img_resized


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


@app.post("/predict/")
async def predict(file: UploadFile = File(...)):
    try:
        img = await file.read()
        try:
            image = Image.open(io.BytesIO(img))
        except Exception as e:
            raise HTTPException(status_code=400, detail="Invalid image file")

      
        img_array = process_image(img)
        

        prediction = model.predict(img_array)
        prediction_class = np.argmax(prediction, axis=-1)[0]  
        
       
        colormap = {
            0: [255, 0, 0],  
            1: [0, 0, 255],  
            2: [0, 255, 0]}  


        rgb_mask = convert_to_rgb(prediction_class, colormap)
        
        original_image = cv2.cvtColor(img_array[0], cv2.COLOR_BGR2RGB)
        
        overlay_image = add_overlay(original_image, rgb_mask)

        final_image = concatenate_images(original_image, overlay_image)

        pil_img = Image.fromarray(final_image)
        img_byte_arr = io.BytesIO()
        pil_img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        return StreamingResponse(img_byte_arr, media_type="image/png")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)