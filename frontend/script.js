async function predict() {
    let file = document.getElementById("imageInput").files[0];
    let lang = document.getElementById("lang").value;

    let formData = new FormData();
    formData.append("image", file);
    formData.append("lang", lang);

    let res = await fetch("http://127.0.0.1:5000/predict", {
        method: "POST",
        body: formData
    });

    let data = await res.json();

    let html = `<h2>Disease: ${data.disease}</h2>`;

    html += `<h3>Symptoms</h3><ul>`;
    data.details.symptoms.forEach(s => {
        html += `<li>${s}</li>`;
    });
    html += `</ul>`;

    html += `<h3>Chemicals</h3>`;
    data.details.management.chemical_control.forEach(c => {
        html += `
            <div>
                <p>${c.chemical_name} (${c.dosage})</p>
                <img src="${c.image}" width="150"/>
            </div>
        `;
    });

    // 🔊 Voice
    let speech = new SpeechSynthesisUtterance(data.disease);
    speech.lang = (lang === "ta") ? "ta-IN" : "en-US";
    speechSynthesis.speak(speech);

    document.getElementById("result").innerHTML = html;
}