from  flask import Flask, render_template,request,jsonify
from my_def import get_response

app = Flask(__name__)

@app.route("/train")
def trainingpage():
    return render_template("trainingpage.html", title="Hello")

@app.get("/")
def index_get():
    return render_template("index.html")


@app.post("/api-backend/chats")
def predict():
    chats = request.get_json().get("chats")
    limitchat = None
    if len(chats) >10:
        limitchat = len(chats)-10
    response = get_response(chats[limitchat : -1])
    # response = get_response([chats[-2]])
    message = {"answer": response}
    return jsonify(message)
if __name__ == "__main__":
    app.run(debug=True)
