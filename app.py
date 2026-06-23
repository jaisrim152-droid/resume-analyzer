from flask import Flask, render_template, request, send_file
import os
import PyPDF2

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Create uploads folder
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# ---------------- RESUME ANALYSIS ----------------
def analyze_resume(text):

    score = 0
    skills = []
    strengths = []
    improvements = []
    suggestions = []

    text = text.lower()

    skill_list = [
        "python", "java", "c", "c++",
        "html", "css", "javascript",
        "sql", "machine learning",
        "iot", "arduino",
        "raspberry pi",
        "embedded systems",
        "pcb",
        "microcontroller"
    ]

    # Detect Skills
    for skill in skill_list:
        if skill in text:
            skills.append(skill)

    

    # Skills Score
    if len(skills) >= 8:
        score += 25
    elif len(skills) >= 5:
        score += 18
    elif len(skills) >= 3:
        score += 10
    elif len(skills) >= 1:
        score += 5

    # Contact Details
    if "@" in text:
        score += 3
        strengths.append("Email included")
    else:
        improvements.append("Add your email address.")
        suggestions.append("Include a professional email.")

    if "linkedin" in text:
        score += 3
        strengths.append("LinkedIn profile included")
    else:
        improvements.append("Add LinkedIn profile.")
        suggestions.append("Include your LinkedIn profile link.")

    if "github" in text:
        score += 3
        strengths.append("GitHub profile included")
    else:
        improvements.append("Add GitHub profile.")
        suggestions.append("Include your GitHub profile link.")

    # Resume Sections
    sections = [
        "objective",
        "summary",
        "skills",
        "education",
        "projects",
        "certification",
        "achievement"
    ]

    section_count = 0

    for section in sections:
        if section in text:
            section_count += 1

    if section_count >= 5:
        score += 10
        strengths.append("Resume has good structure")
    elif section_count >= 3:
        score += 5
    else:
        improvements.append("Add proper resume sections.")
        suggestions.append("Include Summary, Education, Skills and Projects.")

    # Education
    if any(word in text for word in ["b.e", "b.tech", "degree", "college", "university"]):
        score += 10
        strengths.append("Education details included")
    else:
        improvements.append("Add education details.")

    # Experience
    if any(word in text for word in ["intern", "experience", "worked", "training"]):
        score += 10
        strengths.append("Experience included")
    else:
        improvements.append("Add internship experience.")
        suggestions.append("Mention internship or industrial training.")

    # Projects
    if "project" in text:
        score += 15
        strengths.append("Projects included")
    else:
        improvements.append("Add project details.")
        suggestions.append("Include 2-3 projects with technologies used.")

    # Certifications
    if any(word in text for word in ["certificate", "certification", "course"]):
        score += 10
        strengths.append("Certifications included")
    else:
        improvements.append("Add certifications.")
        suggestions.append("Complete relevant online certification courses.")

    # Strong Skills
    if len(skills) >= 5:
        strengths.append("Strong technical skills")

    if score > 100:
        score = 100

    # AI Summary
    if score >= 80:
        summary = "Excellent resume with strong technical profile."
    elif score >= 60:
        summary = "Good resume with scope for improvement."
    else:
        summary = "Resume needs improvement to become ATS friendly."

    rating = round(score / 20, 1)

    breakdown = {
        "Skills": min(len(skills) * 3, 30),
        "Projects": 20 if "project" in text else 0,
        "Education": 15 if any(word in text for word in ["b.e", "b.tech", "degree", "college"]) else 5,
        "Experience": 15 if any(word in text for word in ["intern", "experience", "worked"]) else 5,
        "Certifications": 10 if any(word in text for word in ["certificate", "course"]) else 0
    }

    return (
        score,
        skills,
        strengths,
        improvements,
        suggestions,
        summary,
        rating,
        breakdown
    )
# ---------------- PDF GENERATION ----------------
def generate_pdf(
    filename,
    score,
    skills,
    strengths,
    improvements,
    suggestions,
    summary
):

    file_path = os.path.join(UPLOAD_FOLDER, "resume_report.pdf")

    doc = SimpleDocTemplate(file_path)
    styles = getSampleStyleSheet()
    content = []

    content.append(Paragraph("Resume Analysis Report", styles["Title"]))
    content.append(Spacer(1, 12))

    content.append(Paragraph(f"<b>File Name:</b> {filename}", styles["Normal"]))
    content.append(Paragraph(f"<b>ATS Score:</b> {score}/100", styles["Normal"]))
    content.append(Paragraph(f"<b>Rating:</b> {round(score/20,1)}/5 ⭐", styles["Normal"]))
    content.append(Spacer(1, 12))

    content.append(Paragraph("<b>AI Summary</b>", styles["Heading2"]))
    content.append(Paragraph(summary, styles["Normal"]))
    content.append(Spacer(1, 12))

    def add_section(title, items):
        content.append(Paragraph(title, styles["Heading2"]))

        if items:
            for item in items:
                content.append(Paragraph("• " + item, styles["Normal"]))
        else:
            content.append(Paragraph("No data available.", styles["Normal"]))

        content.append(Spacer(1, 10))

    add_section("Skills", skills)
    add_section("Strengths", strengths)
    add_section("Improvements", improvements)
    add_section("Suggestions", suggestions)
    

    doc.build(content)


# ---------------- ROUTES ----------------
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload_resume():

    if "resume" not in request.files:
        return "No file uploaded"

    file = request.files["resume"]

    if file.filename == "":
        return "No file selected"

    filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(filepath)

    text = ""

    if file.filename.lower().endswith(".pdf"):
        reader = PyPDF2.PdfReader(filepath)

        for page in reader.pages:
            page_text = page.extract_text()

            if page_text:
                text += page_text

    print("========== RESUME TEXT ==========")
    print(text)
    print("TEXT LENGTH:", len(text))

    (
        score,
        skills,
        strengths,
        improvements,
        suggestions,
        summary,
        rating,
        breakdown
    ) = analyze_resume(text)

    generate_pdf(
        file.filename,
        score,
        skills,
        strengths,
        improvements,
        suggestions,
        summary
    )

    return render_template(
        "result.html",
        filename=file.filename,
        resume_text=text,
        score=score,
        skills=skills,
        strengths=strengths,
        improvements=improvements,
        suggestions=suggestions,
        summary=summary,
        rating=rating,
        breakdown=breakdown
    )


@app.route("/download")
def download_pdf():
    pdf_path = os.path.join(UPLOAD_FOLDER, "resume_report.pdf")
    return send_file(pdf_path, as_attachment=True)


# ---------------- MAIN ----------------
if __name__ == "__main__":
    app.run(debug=True)