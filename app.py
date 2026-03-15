import random
import pandas as pd
from flask import Flask, render_template, request, send_file
from io import BytesIO

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4

app = Flask(__name__)

# Load question bank
try:
    df = pd.read_excel("questions.xlsx")
except Exception as e:
    print("Error loading questions.xlsx:", e)
    df = pd.DataFrame()

quiz_questions = []
last_results = []
last_score = 0
last_name = ""
last_co_scores = {}


@app.route("/")
def index():

    cos = sorted(df["CO"].dropna().unique())
    modules = sorted(df["module"].dropna().unique())

    return render_template(
        "index.html",
        cos=cos,
        modules=modules
    )


@app.route("/quiz", methods=["POST"])
def quiz():

    global quiz_questions

    name = request.form["name"]

    selected_cos = request.form.getlist("co")
    selected_modules = request.form.getlist("module")

    filtered = df[
        (df["CO"].isin(selected_cos)) |
        (df["module"].isin(selected_modules))
    ]

    if filtered.empty:
        return "No questions available for selected CO or Module."

    one_mark = filtered[filtered["marks"] == 1]
    two_mark = filtered[filtered["marks"] == 2]

    q1 = one_mark.sample(min(10, len(one_mark)))
    q2 = two_mark.sample(min(5, len(two_mark)))

    quiz = pd.concat([q1, q2]).sample(frac=1)

    questions = []

    for _, row in quiz.iterrows():

        options = [
            row["option1"],
            row["option2"],
            row["option3"],
            row["option4"]
        ]

        random.shuffle(options)

        questions.append({
            "id": row["id"],
            "question": row["question"],
            "options": options,
            "answer": row["answer"],
            "marks": row["marks"],
            "CO": row["CO"]
        })

    quiz_questions = questions

    return render_template(
        "quiz.html",
        questions=questions,
        name=name
    )


@app.route("/submit", methods=["POST"])
def submit():

    global last_results, last_score, last_name, last_co_scores

    name = request.form["name"]

    total_score = 0
    co_scores = {}
    results = []

    for q in quiz_questions:

        qid = str(q["id"])
        user_ans = request.form.get(qid, "")

        correct = q["answer"]
        marks = q["marks"]
        co = q["CO"]

        if co not in co_scores:
            co_scores[co] = 0

        obtained = 0

        if user_ans == correct:
            total_score += marks
            obtained = marks
            co_scores[co] += marks

        results.append({
            "question": q["question"],
            "your": user_ans,
            "correct": correct,
            "marks": marks,
            "obtained": obtained,
            "co": co
        })

    last_results = results
    last_score = total_score
    last_name = name
    last_co_scores = co_scores

    return render_template(
        "result.html",
        name=name,
        score=total_score,
        co_scores=co_scores,
        results=results
    )


@app.route("/download_pdf")
def download_pdf():

    buffer = BytesIO()

    doc = SimpleDocTemplate(buffer, pagesize=A4)

    styles = getSampleStyleSheet()

    elements = []

    elements.append(Paragraph(f"Quiz Result - {last_name}", styles["Title"]))
    elements.append(Spacer(1, 20))

    elements.append(Paragraph(f"Total Score: {last_score}", styles["Heading2"]))
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("CO-wise Score", styles["Heading3"]))
    elements.append(Spacer(1, 10))

    co_table_data = [["CO", "Score"]]

    for co, score in last_co_scores.items():
        co_table_data.append([co, score])

    co_table = Table(co_table_data)

    elements.append(co_table)
    elements.append(Spacer(1, 20))

    table_data = [["Question", "Your Answer", "Correct Answer", "Marks"]]

    for r in last_results:

        table_data.append([
            r["question"],
            r["your"],
            r["correct"],
            f'{r["obtained"]}/{r["marks"]}'
        ])

    table = Table(table_data)

    elements.append(table)

    doc.build(elements)

    buffer.seek(0)

    return send_file(
        buffer,
        download_name=f"{last_name}_quiz_result.pdf",
        as_attachment=True
    )


if __name__ == "__main__":
    app.run(debug=True)
