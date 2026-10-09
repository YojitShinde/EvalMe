<div align="center">

# 📝 EvalMe

### AI-Powered Student Assessment System

Grade handwritten descriptive answers and OMR sheets in one workflow, with less manual effort.

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B?logo=streamlit&logoColor=white)
![Gemini](https://img.shields.io/badge/Google%20Gemini-AI%20Evaluation-4285F4?logo=google&logoColor=white)
![OpenCV](https://img.shields.io/badge/Computer%20Vision-OMR-5C3EE8?logo=opencv&logoColor=white)

</div>

---

## ✨ Features

| | Feature | What it does |
|---|---|---|
| 🧠 | **AI Answer Evaluation** | Scores descriptive answers with Gemini for concept, relevance, accuracy and completeness, with partial credit and a short explanation per question. |
| 🔢 | **Question-number matching** | Maps answers to the key by question number, even when students answer out of order (e.g. Q2 before Q1). |
| 🎯 | **OMR Analysis** | Detects marked bubbles on a scanned sheet and compares them against the OMR key. |
| 🔍 | **OCR processing** | Extracts text from handwritten or scanned sheets, with a chance to review the extracted text. |
| 📊 | **Evaluation report** | Question-wise marks, total score, max marks and percentage, with optional export. |

---

## 🎬 Demo

### 🧠 Answer Evaluation

<div align="center">

| Answer Sheet | Answer Key |
|:---:|:---:|
| <img src="assets/answer-sheet.jpeg" alt="Handwritten answer sheet" width="320"> | <img src="assets/answer-key.png" alt="Answer key" width="320"> |

<br>

<img src="assets/evalme-demo-pt1.gif" alt="Answer Evaluation demo" width="700">

</div>

> The sample sheet answers **Supervised Learning** and **Unsupervised Learning** with Q2 written before Q1. The key allocates 5 marks per question.

### 🎯 OMR Analysis

<div align="center">

| Student OMR Sheet | OMR Key |
|:---:|:---:|
| <img src="assets/student-omr.PNG" alt="Student OMR sheet" width="320"> | <img src="assets/omr-key.png" alt="OMR key" width="320"> |

<br>

<img src="assets/evalme-demo-pt2.gif" alt="OMR Analysis demo" width="700">

</div>

---

## 🛠️ Tech Stack

- **Python**: application logic
- **Streamlit**: web interface
- **Google Gen AI SDK (`google-genai`)**: Gemini-based answer evaluation
- **OCR & image processing**: text extraction and OMR detection
- **Pandas**: tabular results and reports

> Check `requirements.txt` for the exact OCR and computer-vision libraries.

---

## 🚀 Getting Started

**Prerequisites:** Python 3.10+, Git, and a [Gemini API key](https://aistudio.google.com/apikey).

**1. Clone**

```bash
git clone <YOUR_REPOSITORY_URL>
cd <YOUR_PROJECT_DIRECTORY>
```

**2. Create a virtual environment**

```powershell
# Windows PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

```bash
# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

**3. Install dependencies**

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Make sure `google-genai` is included.

**4. Set your Gemini API key**

```powershell
# PowerShell (current session)
$env:GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
```

Or create `.streamlit/secrets.toml`:

```toml
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
```

> ⚠️ Never commit secrets. Add `.streamlit/secrets.toml` and any `.env` file to `.gitignore`.
> To change the model, set `GEMINI_MODEL` to an identifier available to your API key.

**5. Run**

```bash
python -m streamlit run app.py
```

Open the local URL that Streamlit prints.

---

