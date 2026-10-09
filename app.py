import streamlit as st
import os
from modules.peer_comparison import compare_files
from modules.plagiarism_check import check_plagiarism
from modules.ai_content import detect_ai_content
from modules.ocr import perform_ocr, save_ocr_result
from modules.ans_eval import evaluate_answers
from modules.omr_processor import OMRProcessor
from fpdf import FPDF
import io
from datetime import datetime
import cv2
import numpy as np
import pandas as pd

import tempfile
import PyPDF2
from docx import Document

# Initialize session states
if 'ocr_results' not in st.session_state:
    st.session_state.ocr_results = {}
if 'last_files_count' not in st.session_state:
    st.session_state.last_files_count = 0
if 'checkboxes' not in st.session_state:
    st.session_state.checkboxes = {
        'peer_comparison': False,
        'plagiarism_check': False,
        'ai_detection': False
    }
if 'omr_processor' not in st.session_state:
    st.session_state.omr_processor = OMRProcessor()

def reset_checkboxes():
    """Reset all checkboxes to unchecked state"""
    st.session_state.checkboxes = {
        'peer_comparison': False,
        'plagiarism_check': False,
        'ai_detection': False
    }

def reset_peer_comparison():
    """Reset only the peer comparison checkbox"""
    st.session_state.checkboxes['peer_comparison'] = False

def clear_ocr_results():
    """Clear OCR results from session state"""
    st.session_state.ocr_results = {}

def is_image_file(filename):
    """Check if file is an image"""
    image_extensions = {'.jpg', '.jpeg', '.png'}
    return os.path.splitext(filename.lower())[1] in image_extensions

def has_unprocessed_images(files):
    """Check for unprocessed image files"""
    return any(is_image_file(file.name) for file in files 
              if file.name not in st.session_state.ocr_results)

def process_ocr(file, progress_callback=None):
    """Process a single file through OCR"""
    temp_file = f"temp_{file.name}"
    try:
        with open(temp_file, "wb") as f:
            f.write(file.getbuffer())
        return perform_ocr(temp_file, progress_callback)
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)

class PDF(FPDF):
    def header(self):
        # Add logo or header image if needed
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Student Assessment System - Analysis Report', 0, 1, 'C')
        self.ln(10)

def generate_pdf_report(results_data):
    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Add timestamp
    pdf.set_font('Arial', 'I', 10)
    pdf.cell(0, 10, f'Report generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 0, 1)
    pdf.ln(5)

    # Add content for each section
    for section in results_data:
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, section['title'], 0, 1)
        
        pdf.set_font('Arial', '', 11)
        for result in section['content']:
            # Handle potential encoding issues by replacing problematic characters
            clean_text = result.encode('latin-1', errors='replace').decode('latin-1')
            pdf.multi_cell(0, 10, clean_text)
        pdf.ln(5)

    try:
        return pdf.output(dest='S').encode('latin-1')
    except Exception as e:
        # If encoding fails, try with a more robust approach
        buffer = io.BytesIO()
        pdf.output(buffer)
        return buffer.getvalue()

def generate_peer_comparison(temp_files):
    """Generate peer comparison section for the report"""
    peer_results = []
    results = compare_files(temp_files)
    
    for files, similarity in results.items():
        if len(files) == 2:
            file1, file2 = files
            similarity_percentage = similarity * 100
            peer_results.append(
                f"Comparing {os.path.basename(file1)} with {os.path.basename(file2)}\n"
                f"Similarity Score: {similarity_percentage:.1f}%\n"
            )
            
            # Display results in UI
            st.markdown("---")
            st.markdown("### 📄 Similarity Results")
            col1, col2 = st.columns(2)
            with col1:
                st.write("📄 File 1:", os.path.basename(file1))
                st.write("📄 File 2:", os.path.basename(file2))
            with col2:
                st.metric(
                    "Similarity Score",
                    f"{similarity_percentage:.1f}%",
                    delta=None
                )
    
    if peer_results:
        return [{
            'title': 'Peer-to-Peer Comparison Results',
            'content': peer_results
        }]
    return []

def generate_plagiarism_check(temp_files):
    """Generate plagiarism check section for the report"""
    plagiarism_results_list = []
    st.markdown("### 🔍 Plagiarism Check Results")
    
    plagiarism_results = check_plagiarism(temp_files)
    for file_path, result in plagiarism_results.items():
        st.markdown(f"**File: {os.path.basename(file_path)}**")
        st.info(result)
        plagiarism_results_list.append(
            f"File: {os.path.basename(file_path)}\n{result}\n"
        )
    
    if plagiarism_results_list:
        return [{
            'title': 'Plagiarism Check Results',
            'content': plagiarism_results_list
        }]
    return []

def generate_ai_detection(temp_files):
    """Generate AI detection section for the report"""
    ai_results_list = []
    st.markdown("### 🤖 AI Content Detection Results")
    
    ai_results = detect_ai_content(temp_files)
    for file_path, result in ai_results.items():
        filename = os.path.basename(file_path)
        if result['status'] == 'success':
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**{filename}**")
            with col2:
                st.metric(
                    "AI Content Probability",
                    f"{result['ai_percentage']}%"
                )
            st.write(f"Content Length: {result['content_length']} characters")
            
            ai_results_list.append(
                f"File: {filename}\n"
                f"AI Content Probability: {result['ai_percentage']}%\n"
                f"Content Length: {result['content_length']} characters\n"
            )
        else:
            st.error(f"{filename}: Error - {result['error_message']}")
            ai_results_list.append(
                f"File: {filename}\nError: {result['error_message']}\n"
            )
    
    if ai_results_list:
        return [{
            'title': 'AI Content Detection Results',
            'content': ai_results_list
        }]
    return []

def process_omr(answer_sheet, correct_sheet):
    """Process OMR sheets and return marks"""
    try:
        # Read the images
        answer_img = cv2.imdecode(np.frombuffer(answer_sheet.read(), np.uint8), cv2.IMREAD_COLOR)
        correct_img = cv2.imdecode(np.frombuffer(correct_sheet.read(), np.uint8), cv2.IMREAD_COLOR)
        
        # Reset file pointers
        answer_sheet.seek(0)
        correct_sheet.seek(0)
        
        # Convert to grayscale
        answer_gray = cv2.cvtColor(answer_img, cv2.COLOR_BGR2GRAY)
        correct_gray = cv2.cvtColor(correct_img, cv2.COLOR_BGR2GRAY)
        
        # Apply thresholding
        _, answer_thresh = cv2.threshold(answer_gray, 127, 255, cv2.THRESH_BINARY)
        _, correct_thresh = cv2.threshold(correct_gray, 127, 255, cv2.THRESH_BINARY)
        
        # Find contours (bubbles)
        answer_contours, _ = cv2.findContours(answer_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        correct_contours, _ = cv2.findContours(correct_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Compare marked answers with correct answers
        total_questions = len(correct_contours)
        correct_answers = 0
        
        for ans_contour, corr_contour in zip(answer_contours, correct_contours):
            # Calculate overlap
            if cv2.matchShapes(ans_contour, corr_contour, cv2.CONTOURS_MATCH_I1, 0.0) < 0.1:
                correct_answers += 1
        
        # Calculate score
        score = (correct_answers / total_questions) * 100
        return {
            "status": "success",
            "total_questions": total_questions,
            "correct_answers": correct_answers,
            "score": score
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

    
def extract_answer_text(uploaded_file):
    """Extract text from TXT, DOCX, PDF, or image answer sheets."""
    filename = uploaded_file.name
    extension = os.path.splitext(filename)[1].lower()
    file_bytes = uploaded_file.getvalue()

    # Plain text
    if extension == ".txt":
        try:
            return file_bytes.decode("utf-8-sig").strip()
        except UnicodeDecodeError:
            return file_bytes.decode("latin-1").strip()

    # Word documents
    if extension == ".docx":
        document = Document(io.BytesIO(file_bytes))
        return "\n".join(
            paragraph.text for paragraph in document.paragraphs
        ).strip()

    # Save PDF/image temporarily for OCR if needed
    if extension in {".pdf", ".jpg", ".jpeg", ".png"}:
        temp_path = None

        try:
            with tempfile.NamedTemporaryFile(
                suffix=extension, delete=False
            ) as temp_file:
                temp_file.write(file_bytes)
                temp_path = temp_file.name

            # Extract selectable PDF text first
            if extension == ".pdf":
                try:
                    reader = PyPDF2.PdfReader(temp_path)
                    text = "\n".join(
                        page.extract_text() or ""
                        for page in reader.pages
                    ).strip()

                    if text:
                        return text
                except Exception:
                    # Try OCR if PDF text extraction fails
                    pass

            # Images and scanned PDFs: use Google Cloud Vision
            text, error = perform_ocr(temp_path)

            if error:
                raise RuntimeError(error)

            if not text or not text.strip():
                raise ValueError(
                    f"No text could be extracted from {filename}"
                )

            return text.strip()

        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

    raise ValueError(
        f"Unsupported file format: {extension}. "
        "Use TXT, DOCX, PDF, JPG, JPEG, or PNG."
    )


def create_temp_text_file(text):
    """Save extracted answer text to a temporary TXT file."""
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".txt",
        delete=False
    ) as temp_file:
        temp_file.write(text)
        return temp_file.name


def main():
    st.set_page_config(
        page_title="EvalMe",
        page_icon="assets/pen.jpg",
        layout="wide"
    )
    st.title("EvalMe - A Student Assessment System")

    # Create tabs
    tab1, tab2 = st.tabs([
        "Answer-Sheet Evaluation", 
        # "Assignment Cross-Check Verification",
        "OMR Test Analysis"
    ])

    # Answer Evaluation Tab
    with tab1:
        st.header("Answer Evaluation")
        
        # File uploads with expanded file types
        student_answers = st.file_uploader(
            "Upload Student Answers",
            type=["txt", "pdf", "docx", "doc", "jpg", "jpeg", "png"],
            key="student_answers",
            accept_multiple_files=True,
            help="Upload one or more student answer files"
        )
        answer_key = st.file_uploader(
            "Upload Answer Key",
            type=["txt", "pdf", "docx", "doc", "jpg", "jpeg", "png"],
            key="answer_key",
            help="Upload a single answer key file"
        )

        
        if st.button("Evaluate Answers"):
            if not student_answers or not answer_key:
                st.error(
                    "Please upload both student answers and answer key files!"
                )
            else:
                temp_paths = []

                try:
                    # Extract the reference answer
                    with st.spinner("Processing answer key..."):
                        answer_key_text = extract_answer_text(answer_key)

                    if not answer_key_text:
                        st.error("The answer key contains no readable text.")
                    else:
                        for student_answer in student_answers:
                            st.write(f"### Evaluating: {student_answer.name}")

                            try:
                                # Extract text or perform OCR
                                with st.spinner(
                                    f"Extracting text from {student_answer.name}..."
                                ):
                                    student_text = extract_answer_text(
                                        student_answer
                                    )

                                if not student_text:
                                    st.warning(
                                        "No readable text found in this file."
                                    )
                                    continue

                                # Display extracted text for verification
                                with st.expander("View extracted answer"):
                                    st.text_area(
                                        "Student answer text",
                                        value=student_text,
                                        height=200,
                                        key=f"extracted_{student_answer.name}"
                                    )

                                # Create temporary text files
                                student_txt = create_temp_text_file(
                                    student_text
                                )
                                key_txt = create_temp_text_file(
                                    answer_key_text
                                )

                                temp_paths.extend([student_txt, key_txt])

                                # Evaluate the extracted text
                                result = evaluate_answers(
                                    student_txt,
                                    key_txt
                                )

                                
                                if result["status"] == "success":
                                    question_results = result["question_results"]

                                    st.subheader("Individual Answer Evaluation")

                                    if question_results:
                                        report_df = pd.DataFrame([
                                            {
                                                "Answer Number": f"Q{item['question_number']}",
                                                "Score": item["score"],
                                                "Maximum Marks": item["max_marks"],
                                                "Reason": item["reason"],
                                            }
                                            for item in question_results
                                        ])

                                        st.dataframe(report_df, use_container_width=True)

                                        col1, col2, col3 = st.columns(3)

                                        with col1:
                                            st.metric("Total Score", result["total_score"])

                                        with col2:
                                            st.metric("Maximum Marks", result["max_score"])

                                        with col3:
                                            st.metric(
                                                "Percentage",
                                                f"{result['overall_score']:.1f}%"
                                            )

                                        # Include the summary at the bottom of the downloadable report.
                                        report_df = pd.concat([
                                            report_df,
                                            pd.DataFrame([{
                                                "Answer Number": "TOTAL",
                                                "Score": result["total_score"],
                                                "Maximum Marks": result["max_score"],
                                                "Reason": (
                                                    f"Overall percentage: "
                                                    f"{result['overall_score']:.1f}%"
                                                ),
                                            }])
                                        ], ignore_index=True)

                                        csv_data = report_df.to_csv(index=False).encode("utf-8-sig")

                                        st.download_button(
                                            label="📥 Download Evaluation Report (CSV)",
                                            data=csv_data,
                                            file_name=(
                                                f"evaluation_report_"
                                                f"{os.path.splitext(student_answer.name)[0]}.csv"
                                            ),
                                            mime="text/csv",
                                            key=f"download_report_{student_answer.name}",
                                        )

                                    else:
                                        st.warning("No answers were eligible for evaluation.")

                                    if result["skipped_answers"]:
                                        with st.expander("View skipped answers"):
                                            st.dataframe(
                                                pd.DataFrame(result["skipped_answers"]),
                                                use_container_width=True,
                                            )

                                else:
                                    st.error(f"Evaluation failed: {result['message']}")


                            except Exception as e:
                                st.error(
                                    f"Error processing "
                                    f"{student_answer.name}: {e}"
                                )

                            st.markdown("---")

                except Exception as e:
                    st.error(f"Answer-key processing failed: {e}")

                finally:
                    # Clean up temporary text files
                    for path in temp_paths:
                        if os.path.exists(path):
                            os.remove(path)


    # Assignment Verification Tab
    # with tab2:
    #     st.header("Assignment Verification")
        
    #     # File upload for assignments
    #     uploaded_files = st.file_uploader(
    #         "Upload Assignment Files",
    #         type=["txt", "pdf", "docx", "doc", "jpg", "jpeg", "png"],
    #         accept_multiple_files=True,
    #         key="assignments",
    #         help="Supported formats: Text, PDF, Word documents, and Images"
    #     )

    #     # Check file count and manage checkbox states
    #     current_files_count = len(uploaded_files) if uploaded_files else 0
        
    #     # Reset all checkboxes if all files are removed
    #     if current_files_count == 0 and st.session_state.last_files_count > 0:
    #         reset_checkboxes()
    #     # Reset peer comparison if files are less than 2
    #     elif current_files_count < 2 and st.session_state.last_files_count >= 2:
    #         reset_peer_comparison()
            
    #     st.session_state.last_files_count = current_files_count

    #     # Verification options
    #     col1, col2, col3 = st.columns(3)
    #     with col1:
    #         peer_comparison = st.checkbox(
    #             "Compare Peer-to-Peer",
    #             disabled=len(uploaded_files or []) < 2,
    #             help="Upload at least 2 files to enable peer comparison",
    #             value=st.session_state.checkboxes['peer_comparison'],
    #             key='peer_check'
    #         )
    #     with col2:
    #         plagiarism_check = st.checkbox(
    #             "Plagiarism Check",
    #             value=st.session_state.checkboxes['plagiarism_check'],
    #             key='plagiarism_check'
    #         )
    #     with col3:
    #         ai_detection = st.checkbox(
    #             "Detect AI-Generated Content",
    #             value=st.session_state.checkboxes['ai_detection'],
    #             key='ai_check'
    #         )

    #     # Update checkbox states
    #     st.session_state.checkboxes['peer_comparison'] = peer_comparison
    #     st.session_state.checkboxes['plagiarism_check'] = plagiarism_check
    #     st.session_state.checkboxes['ai_detection'] = ai_detection

    #     # Action buttons
    #     col1, col2 = st.columns(2)
    #     with col1:
    #         ocr_clicked = st.button("Convert Images to Text (OCR)", use_container_width=True)
    #     with col2:
    #         generate_clicked = st.button("Generate Report", use_container_width=True)

    #     # Display current OCR results
    #     if st.session_state.ocr_results:
    #         with st.expander("OCR Results", expanded=True):
    #             for filename, text in st.session_state.ocr_results.items():
    #                 st.markdown(f"### 📄 {filename}")
    #                 st.text_area(
    #                     "Extracted Text",
    #                     value=text,
    #                     height=200,
    #                     key=f"ocr_display_{filename}"
    #                 )
    #                 st.download_button(
    #                     label=f"Download OCR result",
    #                     data=text.encode('utf-8'),
    #                     file_name=f"{os.path.splitext(filename)[0]}_ocr.txt",
    #                     mime="text/plain;charset=utf-8",
    #                     key=f"download_display_{filename}"
    #                 )
    #                 st.markdown("---")

    #     # Handle OCR conversion
    #     if ocr_clicked and uploaded_files:
    #         image_files = [f for f in uploaded_files if is_image_file(f.name)]
    #         if not image_files:
    #             st.warning("No image files found to process. Upload JPG, JPEG, or PNG files.")
    #         else:
    #             progress_bar = st.progress(0)
    #             total_files = len(image_files)
                
    #             for idx, file in enumerate(image_files):
    #                 if not is_image_file(file.name):
    #                     continue
                        
    #                 text, error = process_ocr(file, lambda msg: st.write(msg))
    #                 if error:
    #                     st.error(f"Error processing {file.name}: {error}")
    #                 else:
    #                     st.session_state.ocr_results[file.name] = text
    #                 progress_bar.progress((idx + 1) / total_files)
                
    #             if st.session_state.ocr_results:
    #                 st.success("Image processing completed successfully!")

    #     # Handle report generation
    #     if generate_clicked:
    #         if not uploaded_files:
    #             st.error("Please upload files first!")
    #         elif has_unprocessed_images(uploaded_files):
    #             st.error("⚠️ Image files detected! Please use 'Convert Images to Text (OCR)' first.")
    #             st.info("This ensures all files can be properly analyzed.")
    #         else:
    #             with st.container():
    #                 st.markdown("""
    #                     <style>
    #                     .report-container {
    #                         background-color: rgba(89, 37, 193, 0.1);
    #                         border-radius: 10px;
    #                         padding: 20px;
    #                         margin: 10px 0;
    #                     }
    #                     </style>
    #                 """, unsafe_allow_html=True)
                    
    #                 st.markdown('<div class="report-container">', unsafe_allow_html=True)
                    
    #                 # Process files and generate report
    #                 temp_files = []
    #                 try:
    #                     for uploaded_file in uploaded_files:
    #                         temp_file = f"temp_{uploaded_file.name}"
    #                         if uploaded_file.name in st.session_state.ocr_results:
    #                             with open(temp_file, "w", encoding='utf-8') as f:
    #                                 f.write(st.session_state.ocr_results[uploaded_file.name])
    #                         else:
    #                             with open(temp_file, "wb") as f:
    #                                 f.write(uploaded_file.getbuffer())
    #                         temp_files.append(temp_file)

    #                     results_data = []
                    
    #                     # Generate report sections based on selected options
    #                     if peer_comparison:
    #                         results_data.extend(generate_peer_comparison(temp_files))
    #                     if plagiarism_check:
    #                         results_data.extend(generate_plagiarism_check(temp_files))
    #                     if ai_detection:
    #                         results_data.extend(generate_ai_detection(temp_files))

    #                     # Generate and offer PDF download
    #                     if results_data:
    #                         pdf_bytes = generate_pdf_report(results_data)
    #                         st.download_button(
    #                             label="📥 Download PDF Report",
    #                             data=pdf_bytes,
    #                             file_name=f"analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
    #                             mime="application/pdf",
    #                         )
    #                         # Clear OCR results after successful report generation
    #                         clear_ocr_results()
    #                     else:
    #                         st.warning("Please select at least one analysis option.")

    #                 except Exception as e:
    #                     st.error(f"An error occurred during report generation: {str(e)}")

    #                 finally:
    #                     # Clean up temporary files
    #                     for temp_file in temp_files:
    #                         if os.path.exists(temp_file):
    #                             os.remove(temp_file)
                    
    #                 st.markdown('</div>', unsafe_allow_html=True)

    # OMR Test Analysis Tab
    with tab2:
        st.header("OMR Test Analysis")
        
        # Instructions
        st.markdown("""
        ### Instructions
        1. Configure the OMR sheet format
        2. Upload a clear image of the correct answer OMR sheet
        3. Upload student OMR answer sheets
        4. Each sheet should have:
           - Clear bubbles marked with dark pen/pencil
           - All 4 corners visible
           - Good lighting and no shadows
        """)
        
        # OMR Configuration
        st.subheader("OMR Configuration")
        col1, col2 = st.columns(2)
        with col1:
            questions_count = st.number_input(
                "Number of Questions",
                min_value=1,
                max_value=100,
                value=20,
                help="Enter the total number of questions in the OMR sheet"
            )
        with col2:
            options_count = st.number_input(
                "Options per Question",
                min_value=2,
                max_value=10,
                value=5,
                help="Enter the number of options per question (e.g., 5 for A,B,C,D,E)"
            )
        
        # Configure button
        if st.button("Configure OMR Format"):
            if st.session_state.omr_processor.configure(questions_count, options_count):
                st.success(f"✅ OMR format configured: {questions_count} questions with {options_count} options each")
            else:
                st.error("Failed to configure OMR format")
        
        st.markdown("---")
        
        # File upload for correct answer OMR sheet
        correct_omr = st.file_uploader(
            "Upload Correct Answer OMR Sheet",
            type=["jpg", "jpeg", "png"],
            key="correct_omr",
            help="Upload the correct answer OMR sheet"
        )
        
        # File upload for student OMR sheets
        student_omr_sheets = st.file_uploader(
            "Upload Student OMR Sheets",
            type=["jpg", "jpeg", "png"],
            key="student_omr",
            accept_multiple_files=True,
            help="Upload one or more student OMR answer sheets"
        )
        
        if st.button("Evaluate OMR Sheets"):
            if not st.session_state.omr_processor.is_configured:
                st.error("Please configure the OMR format first!")
            elif not correct_omr or not student_omr_sheets:
                st.error("Please upload both correct answer sheet and student answer sheets!")
            else:
                # Process answer key first
                if st.session_state.omr_processor.process_answer_key(correct_omr.getvalue()):
                    st.success("✅ Answer key processed successfully!")
                    st.markdown("### 📊 OMR Evaluation Results")
                    
                    # Create a DataFrame to store results
                    results_data = []
                    
                    # Process each student's OMR sheet
                    for student_sheet in student_omr_sheets:
                        st.write(f"### Evaluating: {student_sheet.name}")
                        
                        result = st.session_state.omr_processor.evaluate_answer_sheet(student_sheet.getvalue())
                        
                        if result["status"] == "success":
                            # Display results
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.write(f"Total Questions: {result['total_questions']}")
                                st.write(f"Correct Answers: {result['correct_answers']}")
                                
                                # Display answer comparison
                                st.markdown("#### Answer Comparison")
                                
                                # Store question-wise answers for Excel
                                question_answers = []
                                student_answers = result.get('marked_answers', [])
                                correct_answers = result.get('correct_answers_key', [])
                                
                                for q_num in range(result['total_questions']):
                                    student_ans = student_answers[q_num] if q_num < len(student_answers) else -1
                                    correct_ans = correct_answers[q_num] if q_num < len(correct_answers) else -1
                                    
                                    student_choice = chr(65 + student_ans) if student_ans >= 0 else "No answer"
                                    correct_choice = chr(65 + correct_ans) if correct_ans >= 0 else "No answer"
                                    is_correct = student_ans == correct_ans
                                    
                                    st.write(
                                        f"Q{q_num + 1}: Your answer: {student_choice} | "
                                        f"Correct answer: {correct_choice} | "
                                        f"{'✅' if is_correct else '❌'}"
                                    )
                                    
                                    # Add to question answers
                                    question_answers.append({
                                        'Question': f'Q{q_num + 1}',
                                        'Student Answer': student_choice,
                                        'Correct Answer': correct_choice,
                                        'Is Correct': '✓' if is_correct else '✗'
                                    })
                            
                            with col2:
                                st.metric(
                                    "Score",
                                    f"{result['score']:.1f}%"
                                )
                            
                            # Add to results data with detailed answers
                            results_data.append({
                                "Student": os.path.splitext(student_sheet.name)[0],
                                "Score": result['score'],
                                "Correct": result['correct_answers'],
                                "Total": result['total_questions'],
                                "Question_Answers": question_answers
                            })
                        else:
                            st.error(f"Evaluation failed: {result['message']}")
                        
                        st.markdown("---")
                    
                    # Display summary if there are results
                    if results_data:
                        st.markdown("### 📈 Class Summary")
                        scores = [r['Score'] for r in results_data]
                        st.write(f"Class Average: {sum(scores) / len(scores):.1f}%")
                        st.write(f"Highest Score: {max(scores):.1f}%")
                        st.write(f"Lowest Score: {min(scores):.1f}%")
                        
                        # Create Excel export if there are multiple students
                        if len(results_data) > 1:
                            st.markdown("### 📊 Export Results")
                            
                            # Create Excel file
                            output = io.BytesIO()
                            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                                # Summary sheet
                                summary_data = []
                                for r in results_data:
                                    summary_data.append({
                                        'Student': r['Student'],
                                        'Score (%)': r['Score'],
                                        'Correct Answers': r['Correct'],
                                        'Total Questions': r['Total']
                                    })
                                
                                summary_df = pd.DataFrame(summary_data)
                                summary_df.loc['Average'] = ['Class Average', 
                                                           summary_df['Score (%)'].mean(),
                                                           summary_df['Correct Answers'].mean(),
                                                           summary_df['Total Questions'].iloc[0]]
                                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                                
                                # Detailed analysis sheet
                                detailed_data = []
                                for result in results_data:
                                    for qa in result['Question_Answers']:
                                        detailed_data.append({
                                            'Student': result['Student'],
                                            'Question': qa['Question'],
                                            'Student Answer': qa['Student Answer'],
                                            'Correct Answer': qa['Correct Answer'],
                                            'Is Correct': qa['Is Correct']
                                        })
                                
                                detailed_df = pd.DataFrame(detailed_data)
                                detailed_df.to_excel(writer, sheet_name='Detailed Analysis', index=False)
                                
                                # Auto-adjust column widths
                                for sheet in writer.book.sheetnames:
                                    ws = writer.book[sheet]
                                    for column in ws.columns:
                                        max_length = 0
                                        column = [cell for cell in column]
                                        for cell in column:
                                            try:
                                                if len(str(cell.value)) > max_length:
                                                    max_length = len(cell.value)
                                            except:
                                                pass
                                        adjusted_width = (max_length + 2)
                                        ws.column_dimensions[column[0].column_letter].width = adjusted_width
                            
                            # Offer Excel download
                            st.download_button(
                                label="📥 Download Detailed Results (Excel)",
                                data=output.getvalue(),
                                file_name=f"omr_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                else:
                    st.error("Failed to process answer key. Please ensure the image is clear and properly aligned.")

if __name__ == "__main__":
    main() 