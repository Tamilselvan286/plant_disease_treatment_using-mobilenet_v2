import streamlit as st
import os
import tempfile
from PIL import Image

try:
    from utils.predict import predict_disease
    from utils.translate import deep_translate
    from utils.scraper import fetch_image, fetch_summary
except ModuleNotFoundError:
    st.error("Could not import utility modules. Make sure you're running this from the backend folder.")

from pymongo import MongoClient

# MongoDB setup
client = MongoClient("mongodb+srv://LeafDisease:yasisvQUPDZlzrdX@cluster0.sausgkt.mongodb.net/")
db = client["diseasedb"]
collection = db["leafdisease"]

st.title("🌿 Plant Disease Predictor")
st.write("Upload an image of a plant leaf to predict the disease and get treatment details.")

lang = st.selectbox("Select Language", ["en", "ta"], format_func=lambda x: "English" if x == "en" else "Tamil")
uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    
    # Center and size down the image
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(image, caption='Uploaded Image', use_container_width=True)
    
    st.divider()
    
    # Centered Predict Button
    _, btn_col, _ = st.columns([1, 1, 1])
    with btn_col:
        predict_clicked = st.button("🔍 Run Prediction", use_container_width=True)

    if predict_clicked:
        with st.spinner("Analyzing leaf patterns..."):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_file_path = tmp_file.name

            try:
                disease = predict_disease(tmp_file_path)
                
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
                    st.success(f"🌱 Prediction: **{disease.replace('_', ' ').title()}**")
                    st.info("The plant appears to be healthy! Maintain normal care.")
                elif not data:
                    st.warning(f"⚠️ Prediction: {disease.replace('_', ' ').title()}")
                    st.error(f"No treatment found for a disease matching '{disease_str}' on '{crop_str}' in the database.")
                else:
                    st.success(f"🎯 Prediction: **{disease.replace('_', ' ').title()}**")
                    
                    # Process data (fetch image and translate)
                    if "management" in data and "chemical_control" in data["management"]:
                        for chem in data["management"]["chemical_control"]:
                            chem["image"] = fetch_image(chem["chemical_name"])

                    with st.spinner("Fetching summary..."):
                        data["web_summary"] = fetch_summary(disease.replace('_', ' '))

                    if lang == "ta":
                        data = deep_translate(data, "ta")

                    st.markdown("---")
                    st.markdown(f"## 🩺 {data.get('disease_name', '')}")
                    
                    if data.get("web_summary") and data["web_summary"] != "No summary available online.":
                        st.info("**Web Summary:** " + data["web_summary"])
                    
                    # Symptoms using a formatted card
                    st.markdown("**Symptoms:**")
                    symptoms = data.get("symptoms", [])
                    if isinstance(symptoms, list):
                        for sym in symptoms:
                            st.markdown(f"- {sym}")
                    else:
                        st.write(symptoms)
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    # Treatments grid
                    if "management" in data:
                        chem_controls = data["management"].get("chemical_control", [])
                        if chem_controls:
                            st.markdown("### 🧪 Recommended Chemical Controls")
                            
                            # Create a dynamic column grid for chemicals
                            cols = st.columns(3)
                            for i, chem in enumerate(chem_controls):
                                with cols[i % 3]:
                                    with st.container(border=True):
                                        st.markdown(f"**{chem.get('chemical_name', 'Unknown')}**")
                                        if chem.get("dosage"):
                                            st.caption(f"Dosage: {chem.get('dosage')}")
                                        else:
                                            st.caption("Dosage: Refer to manual")
                                            
                                        if chem.get("image"):
                                            st.image(chem["image"], use_container_width=True)
                                        else:
                                            st.text("No image available")

                    with st.expander("Show raw database entry"):
                        data.pop("_id", None) # Remove raw object ID for cleaner render
                        st.json(data)

            except Exception as e:
                st.error(f"Error during prediction: {str(e)}")
            finally:
                os.remove(tmp_file_path)
