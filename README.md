# EvalMe --- AI-Powered Student Assessment System

EvalMe is a Streamlit-based student assessment application designed to
help educators evaluate descriptive answers and objective OMR sheets
with less manual effort. It combines OCR-based document processing,
AI-assisted answer evaluation, and computer-vision-based OMR checking in
one workflow.

## Features

### 1. AI-assisted descriptive answer evaluation

-   Accepts student answer documents and a reference answer key.
-   Extracts text from supported files through the application's
    document/OCR workflow.
-   Matches answers using question numbers, even when students answer
    questions out of order.
-   Uses the Gemini API to assess conceptual correctness, relevant
    points, factual accuracy, and completeness.
-   Supports partial credit and returns a score with a short explanation
    for each question.
-   Calculates question-wise marks, total marks, and the overall
    percentage based on the marks specified in the answer key.

### 2. OMR answer-sheet evaluation

-   Processes an OMR answer key and a student's marked response sheet.
-   Uses computer vision to detect marked options and compare responses
    against the key.
-   Helps automate objective-test scoring.

### 3. OCR-assisted document processing

-   Extracts text from answer sheets and reference material before
    evaluation.
-   Makes handwritten or scanned submissions usable in the evaluation
    workflow when OCR can recognize the content.
-   Provides an opportunity to inspect extracted text when recognition
    or question segmentation needs review.

### 4. Evaluation report

-   Presents question-wise scores and feedback.
-   Computes the total score and maximum possible marks.
-   Supports exporting assessment results when the report-download
    feature is enabled in the application.

## Demo

The repository's demo recordings can be added here once they are
uploaded to a public location or committed to the repository.

-   **Descriptive answer evaluation:** `assets/evalme-demo-pt1.gif`
-   **OMR evaluation:** `assets/evalme-demo-pt2.gif`

For GitHub, consider converting the recordings to GIFs or uploading them
to GitHub Releases, then linking them here. Avoid committing very large
video files directly if they make the repository difficult to clone.

## Example inputs

The project examples include: - A handwritten response sheet containing
answers to **Supervised Learning** and **Unsupervised Learning**, with
Q2 appearing before Q1. - A reference answer key with a 5-mark
allocation for each descriptive question. - An OMR key and a sample
student OMR sheet with filled multiple-choice bubbles.

These examples illustrate why question-number matching and OMR bubble
detection matter. OCR and image quality can affect the result, so
ambiguous cases should be checked before finalizing marks.

## Technology stack

The current implementation uses or is designed around the following
technologies:

-   **Python** --- application logic
-   **Streamlit** --- web application interface
-   **Google Gen AI SDK (`google-genai`)** --- Gemini-based descriptive
    answer evaluation
-   **OCR and image processing** --- text extraction and OMR processing
-   **Pandas** --- tabular results and report handling, where used

Check `requirements.txt` and the source modules for the exact OCR and
computer-vision libraries used in your current version.

## Getting started

### Prerequisites

-   Python 3.10 or newer (use the version supported by your installed
    dependencies)
-   A Google Gemini API key for AI-assisted descriptive evaluation
-   Git

### 1. Clone the repository

``` bash
git clone <YOUR_REPOSITORY_URL>
cd <YOUR_PROJECT_DIRECTORY>
```

Replace the placeholders with your repository URL and folder name.

### 2. Create and activate a virtual environment

**Windows PowerShell**

``` powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux**

``` bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

If the project has a `requirements.txt` file:

``` bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Ensure the dependencies include the Gemini SDK used by the code:

``` text
google-genai
```

Install any additional OCR or image-processing dependencies listed by
the project.

### 4. Configure the Gemini API key

The evaluator reads `GEMINI_API_KEY` from Streamlit secrets or an
environment variable.

**PowerShell (current terminal session):**

``` powershell
$env:GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
```

Alternatively, create `.streamlit/secrets.toml`:

``` toml
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
```

Do not commit API keys or secrets to version control. Add
`.streamlit/secrets.toml` and any `.env` file containing credentials to
`.gitignore`.

If the model name is configurable through `GEMINI_MODEL`, set it to a
model identifier currently available to your API key. Model availability
can vary by account and API access.

### 5. Run the application

``` bash
python -m streamlit run app.py
```

Open the local URL printed by Streamlit in your browser.

## Typical workflow

1.  Open EvalMe.
2.  Select the assessment workflow: descriptive answer evaluation or OMR
    evaluation.
3.  Upload the relevant answer key and student submission(s).
4.  Review extracted text or detected OMR responses if the application
    provides that preview.
5.  Run the evaluation.
6.  Review per-question marks, explanations, and the total score.
7.  Export or download the report if that option is enabled.

## Important evaluation notes

-   **AI scores should be reviewed.** Gemini-generated marks are
    estimates and may need educator verification.
-   **OCR is imperfect.** Handwriting, shadows, rotation, low contrast,
    and page curvature can cause extraction errors.
-   **Question labels matter.** Descriptive answer matching relies on
    recognizable question numbers. Missing or ambiguous labels should be
    reviewed rather than silently accepted.
-   **OMR image quality matters.** Bubble marks, alignment, lighting,
    and page positioning can affect detection.
-   **Reference answers are not the only valid answers.** The evaluator
    should accept correct alternative explanations and award partial
    credit where appropriate.
-   **Protect student data.** Do not upload student submissions to
    external APIs unless permitted by your institution and applicable
    privacy requirements. Gemini-based evaluation sends the relevant
    prompt content to Google's API.

## Suggested project structure

The exact structure may differ; this is a reference layout based on the
application's modules.

``` text
sas-system/
├── app.py
├── modules/
│   ├── ans_eval.py
│   ├── plagiarism_check.py
│   └── ...
├── requirements.txt
├── .streamlit/
│   └── secrets.toml        # local only; do not commit
└── README.md
```

## Troubleshooting

### `ImportError: cannot import name 'genai' from 'google'`

Install the current SDK in the same virtual environment used to run
Streamlit:

``` bash
python -m pip install --upgrade google-genai
python -c "from google import genai; print('Gemini SDK import successful')"
python -m streamlit run app.py
```

Check that the project does not contain a conflicting `google.py` file
or `google` directory.

### `ModuleNotFoundError: No module named 'google.generativeai'`

The old import `import google.generativeai as genai` belongs to the
legacy `google-generativeai` SDK. If the module uses `google-genai`,
migrate its API calls as well as its import; changing only the import
line is not enough.

### Gemini model returns `404 NOT_FOUND`

Use a model identifier currently supported for your API key and update
`GEMINI_MODEL` or the default model in the code accordingly.

### No questions found or incorrect question matching

Inspect the extracted OCR text and parsed question numbers. Confirm that
the answer key has recognizable question headings and that each
question's marks are present if the parser depends on explicit marks.

## Future improvements

-   Manual review and score override for uncertain evaluations.
-   Confidence indicators for OCR and OMR results.
-   Batch processing and class-level reports.
-   Better handling of varied question numbering and multi-page
    submissions.
-   Test cases for parsing, scoring totals, and OMR detection.
-   Audit trail for teacher adjustments.

## Contributing

1.  Fork the repository.
2.  Create a feature branch.
3.  Add tests for parsing, scoring, or image-processing changes.
4.  Submit a pull request with a concise description of the change.

## License

Add the license that applies to this project. Until a license is
included in the repository, reuse and redistribution terms may be
unclear.
