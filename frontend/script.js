async function predict() {
    let resultDiv = document.getElementById("result");
    resultDiv.innerHTML = "Loading...";

    let file = document.getElementById("imageInput").files[0];
    let lang = document.getElementById("lang").value;

    if (!file) {
        resultDiv.innerHTML = "<p>Please select an image.</p>";
        return;
    }

    let formData = new FormData();
    formData.append("image", file);
    formData.append("lang", lang);

    try {
        let res = await fetch("http://127.0.0.1:5000/predict", {
            method: "POST",
            body: formData
        });

        let data = await res.json();

        if (data.error) {
            resultDiv.innerHTML = `<p style="color:red">${data.error}</p>`;
            return;
        }

        if (data.message) {
            resultDiv.innerHTML = `<p style="color:green"><strong>Healthy Plant:</strong> ${data.message}</p>`;
            return;
        }

        let html = `<h2>Disease: ${data.disease ? data.disease.replace(/_/g, ' ') : "Unknown"}</h2>`;

        if (data.details && data.details.web_summary && data.details.web_summary !== "No summary available online.") {
            html += `<div style="background:#f4f4f4; padding:10px; margin: 10px 0; border-radius:5px;">
                        <strong>Web Summary:</strong> ${data.details.web_summary}
                     </div>`;
        }

        if (data.details && data.details.symptoms) {
            html += `<h3>Symptoms</h3><ul>`;
            data.details.symptoms.forEach(s => {
                html += `<li>${s}</li>`;
            });
            html += `</ul>`;
        }

        if (data.details && data.details.management && data.details.management.chemical_control) {
            html += `<h3>Chemicals</h3>`;
            data.details.management.chemical_control.forEach(c => {
                html += `
                    <div>
                        <p>${c.chemical_name || "Unknown"} (${c.dosage || "Unknown"})</p>
                        ${c.image ? `<img src="${c.image}" width="150" alt="Chemical image"/>` : ''}
                    </div>
                `;
            });
        }

        // 🔊 Voice
        let speechText = data.disease || "";
        if (data.details && data.details.disease_name) {
             speechText = data.details.disease_name;
        }
        let speech = new SpeechSynthesisUtterance(speechText);
        speech.lang = (lang === "ta") ? "ta-IN" : "en-US";
        speechSynthesis.speak(speech);

        resultDiv.innerHTML = html;
    } catch (err) {
        console.error(err);
        resultDiv.innerHTML = `<p style="color:red">Error communicating with the server: ${err.message}</p>`;
    }
}