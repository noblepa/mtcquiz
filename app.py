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


@app.route("/")
def index():

    cos = sorted(df["CO"].dropna().unique())
    modules = sorted(df["module"].dropna().unique())

    return render_template("index.html", cos=cos, modules=modules)


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

    return render_template("quiz.html", questions=questions, name=name)


@app.route("/submit", methods=["POST"])
def submit():

    name = request.form["name"]

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

        # Initialize
        if co not in co_scores:
            co_scores[co] = 0
            co_max_marks[co] = 0

        # Add to max marks
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

    return render_template(
        "result.html",
        name=name,
        score=total_score,
        co_scores=co_scores,
        co_max_marks=co_max_marks,
        results=results
    )


if __name__ == "__main__":
    app.run(debug=True)
