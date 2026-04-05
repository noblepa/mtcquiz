import random
import pandas as pd
from flask import Flask, render_template, request

app = Flask(__name__)

# Load question bank
try:
    df = pd.read_excel("questions.xlsx")
except Exception as e:
    print("Error loading questions.xlsx:", e)
    df = pd.DataFrame()

quiz_questions = []
current_pattern = ""


@app.route("/")
def index():

    cos = sorted(df["CO"].dropna().unique())
    modules = sorted(df["module"].dropna().unique())

    return render_template("index.html", cos=cos, modules=modules)


@app.route("/quiz", methods=["POST"])
def quiz():

    global quiz_questions, current_pattern

    name = request.form.get("name", "Student")
    pattern = request.form.get("pattern")

    current_pattern = pattern

    selected_cos = request.form.getlist("co")
    selected_modules = request.form.getlist("module")

    filtered = df[
        (df["CO"].isin(selected_cos)) |
        (df["module"].isin(selected_modules))
    ]

    if filtered.empty:
        return "No questions available for selected CO or Module."

    # Pattern definitions
    pattern_map = {
        "p1": (10, 5),
        "p2": (20, 10),
        "p3": (30, 15)
    }

    n1, n2 = pattern_map.get(pattern, (10, 5))

    one_mark = filtered[filtered["marks"] == 1]
    two_mark = filtered[filtered["marks"] == 2]

    # Strict validation
    if len(one_mark) < n1 or len(two_mark) < n2:
        return f"Not enough questions available for selected pattern. Required: {n1} (1-mark), {n2} (2-mark)"

    # Sample questions
    q1 = one_mark.sample(n1)
    q2 = two_mark.sample(n2)

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
        name=name,
        pattern=pattern
    )


@app.route("/submit", methods=["POST"])
def submit():

    global current_pattern

    name = request.form.get("name", "Student")

    # Prevent session error
    if not quiz_questions:
        return "Session expired. Please start quiz again."

    total_score = 0
    co_scores = {}
    co_max_marks = {}
    results = []

    for q in quiz_questions:

        qid = str(q["id"])
        user_ans = request.form.get(qid, "")

        correct = q["answer"]
        marks = q["marks"]
        co = q["CO"]

        if co not in co_scores:
            co_scores[co] = 0
            co_max_marks[co] = 0

        co_max_marks[co] += marks

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

    # Robust CO sorting (handles descriptive CO labels)
    import re

    def extract_co_number(co):
        match = re.search(r'\d+', str(co))
        return int(match.group()) if match else 999

    sorted_cos = sorted(co_scores.keys(), key=extract_co_number)

    return render_template(
        "result.html",
        name=name,
        score=total_score,
        co_scores=co_scores,
        co_max_marks=co_max_marks,
        results=results,
        sorted_cos=sorted_cos,
        pattern=current_pattern
    )


if __name__ == "__main__":
    app.run(debug=True)
