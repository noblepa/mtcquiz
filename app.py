
import random
import pandas as pd
from flask import Flask, render_template, request, send_file
from io import BytesIO

app = Flask(__name__)

df = pd.read_excel("questions.xlsx")

quiz_questions = []

@app.route("/")
def index():
    cos = sorted(df["CO"].unique())
    modules = sorted(df["module"].unique())
    return render_template("index.html", cos=cos, modules=modules)

@app.route("/quiz", methods=["POST"])
def quiz():
    global quiz_questions

    name = request.form["name"]
    selected_cos = request.form.getlist("co")
    selected_modules = request.form.getlist("module")

    filtered = df[(df["CO"].isin(selected_cos)) | (df["module"].isin(selected_modules))]

    q1 = filtered[filtered["marks"]==1].sample(10)
    q2 = filtered[filtered["marks"]==2].sample(5)

    quiz = pd.concat([q1,q2]).sample(frac=1)

    questions=[]

    for _,row in quiz.iterrows():
        options=[row["option1"],row["option2"],row["option3"],row["option4"]]
        random.shuffle(options)

        questions.append({
            "id":row["id"],
            "question":row["question"],
            "options":options,
            "answer":row["answer"],
            "marks":row["marks"],
            "CO":row["CO"]
        })

    quiz_questions=questions

    return render_template("quiz.html",questions=questions,name=name)

@app.route("/submit",methods=["POST"])
def submit():
    name=request.form["name"]

    total_score=0
    co_scores={}
    results=[]

    for q in quiz_questions:

        qid=str(q["id"])
        user_ans=request.form.get(qid,"")

        correct=q["answer"]
        marks=q["marks"]
        co=q["CO"]

        if co not in co_scores:
            co_scores[co]=0

        obtained=0

        if user_ans==correct:
            total_score+=marks
            obtained=marks
            co_scores[co]+=marks

        results.append({
            "Question ID":qid,
            "Question":q["question"],
            "Your Answer":user_ans,
            "Correct Answer":correct,
            "Marks":marks,
            "Obtained":obtained,
            "CO":co
        })

    result_df=pd.DataFrame(results)

    output=BytesIO()

    with pd.ExcelWriter(output,engine="openpyxl") as writer:
        result_df.to_excel(writer,index=False,sheet_name="Responses")

        summary=pd.DataFrame(list(co_scores.items()),columns=["CO","Score"])
        summary.to_excel(writer,index=False,sheet_name="CO Scores")

    output.seek(0)

    return send_file(
        output,
        download_name=f"{name}_quiz_result.xlsx",
        as_attachment=True
    )

if __name__=="__main__":
    app.run()
