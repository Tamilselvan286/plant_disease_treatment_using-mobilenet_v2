import os
import tensorflow as tf
import numpy as np
from tensorflow.keras.preprocessing import image
import gdown

# Use a dynamic relative path robust for both local and cloud environments
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
model_dir = os.path.join(backend_dir, "model")
os.makedirs(model_dir, exist_ok=True)
model_path = os.path.join(model_dir, "plant_disease_model.keras")
model = None

if not os.path.exists(model_path):
    print("Model not found locally. Downloading from Google Drive...")
    url = "https://drive.google.com/uc?id=10hwfSimGop7IXd91FlPjozuTTLgle_Mp"
    try:
        gdown.download(url, model_path, quiet=False, fuzzy=True)
    except Exception as e:
        print("[!] Failed to download model:", e)

if os.path.exists(model_path):
    model = tf.keras.models.load_model(model_path, compile=False)
else:
    print(f"[!] Model not found at {model_path}")

CLASS_NAMES = [
    "bean_angular_leaf_spot",
    "bean_bean_rust",
    "bean_healthy",
    "corn_blight",
    "corn_common_rust",
    "corn_gray_leaf_spot",
    "corn_healthy",
    "mango_anthracnose",
    "mango_bacterial_canker",
    "mango_cutting_weevil",
    "mango_die_back",
    "mango_gall_midge",
    "mango_healthy",
    "mango_powdery_mildew",
    "mango_sooty_mould",
    "non_leaf",
    "potato_bacteria",
    "potato_fungi",
    "potato_healthy",
    "potato_nematode",
    "potato_pest",
    "potato_phytopthora",
    "potato_virus",
    "rice_bacterial_leaf_blight",
    "rice_brown_spot",
    "rice_healthy",
    "rice_leaf_blast",
    "rice_leaf_scald",
    "rice_narrow_brown_spot",
    "rice_neck_blast",
    "rice_rice_hispa",
    "rice_sheath_blight",
    "rice_tungro",
    "tomato_bacterial_spot",
    "tomato_early_blight",
    "tomato_healthy",
    "tomato_late_blight",
    "tomato_leaf_mold",
    "tomato_powdery_mildew",
    "tomato_septoria_leaf_spot",
    "tomato_spider_mites_two_spotted_spider_mite",
    "tomato_target_spot",
    "tomato_tomato_mosaic_virus",
    "tomato_tomato_yellow_leaf_curl_virus"
]

def predict_disease(img_path):
    if model is None:
        raise Exception(f"The neural network model could not be loaded from '{model_path}'. Please check if the file exists.")

    img = image.load_img(img_path, target_size=(224, 224))
    img_array = image.img_to_array(img) / 255.0
    img_array = np.expand_dims(img_array, axis=0)

    pred = model.predict(img_array)
    return CLASS_NAMES[np.argmax(pred)]