from flask import Flask, request, jsonify
from pymongo import MongoClient
import sys
import os
from utils.predict import predict_disease
from utils.translate import deep_translate
from utils.scraper import fetch_image
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
app = Flask(__name__)


# MongoDB
client = MongoClient("mongodb+srv://LeafDisease:yasisvQUPDZlzrdX@cluster0.sausgkt.mongodb.net/")
db = client["diseasedb"]
collection = db["leafdisease"]

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ------------------- ROUTES -------------------

@app.route("/")
def home():
    return "API Running 🚀"

@app.route("/predict", methods=["POST"])
def predict():
    file = request.files["image"]
    lang = request.form.get("lang", "en")

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    # 🔥 Predict
    disease = predict_disease(filepath)

    # Parse the crop and disease name from format 'crop_disease_name'
    crop_str = disease.split('_')[0]
    disease_str = disease[len(crop_str)+1:].replace('_', ' ')

    # Fetch treatment from MongoDB using a flexible regex search
    query = {
        "crop": {"$regex": f"^{crop_str}$", "$options": "i"},
        "disease_name": {"$regex": disease_str, "$options": "i"}
    }
    data = collection.find_one(query)
    
    # Fallback if strict crop matching fails
    if not data:
        data = collection.find_one({"disease_name": {"$regex": disease_str, "$options": "i"}})

    if "healthy" in disease.lower():
        return jsonify({"message": "The plant appears to be healthy! Maintain normal care."})

    if not data:
        return jsonify({"error": f"No treatment found for a disease matching '{disease_str}' on '{crop_str}' in the database."})

    # 🔥 Scrape chemical images
    for chem in data["management"]["chemical_control"]:
        chem["image"] = fetch_image(chem["chemical_name"])

    # 🔥 Translate if needed
    if lang == "ta":
        data = deep_translate(data, "ta")

    return jsonify({
        "disease": disease,
        "details": data
    })

# -------------------

if __name__ == "__main__":
    from werkzeug.serving import run_simple
    run_simple("0.0.0.0", 5000, app)