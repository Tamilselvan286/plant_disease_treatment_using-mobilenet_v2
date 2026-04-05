from flask import Flask, request, jsonify
from pymongo import MongoClient
import sys
import os
from utils.predict import predict_disease
from utils.translate import deep_translate
from utils.scraper import fetch_image
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
frontend_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
app = Flask(__name__, static_folder=frontend_folder, static_url_path="/")


# MongoDB
client = MongoClient("mongodb+srv://LeafDisease:yasisvQUPDZlzrdX@cluster0.sausgkt.mongodb.net/")
db = client["diseasedb"]
collection = db["leafdisease"]

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ------------------- ROUTES -------------------

@app.route("/")
def home():
    return app.send_static_file("index.html")

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
    from utils.scraper import fetch_image, fetch_summary
    if "management" in data and "chemical_control" in data["management"]:
        for chem in data["management"]["chemical_control"]:
            chem["image"] = fetch_image(chem["chemical_name"])

    # 🔥 Fetch web summary
    data["web_summary"] = fetch_summary(disease.replace('_', ' '))

    # 🔥 Translate if needed
    if lang == "ta":
        data = deep_translate(data, "ta")

    return jsonify({
        "disease": disease,
        "details": data
    })

# -------------------

if __name__ == "__main__":
    print("\n" + "="*50)
    print("🚀 API Server is starting!")
    print("👉 Frontend Localhost Link: http://127.0.0.1:5000")
    print("="*50 + "\n")
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)