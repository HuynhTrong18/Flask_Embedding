from  flask import Flask, render_template,request,jsonify
from my_def import get_response

app = Flask(__name__)

# @app.route("/")
# def hello_world():
#     return render_template("index.html", title="Hello")

app = Flask(__name__)
@app.get("/")
def index_get():
    return render_template("index.html")


@app.post("/api-backend/chats")
def predict():
    chats = request.get_json().get("chats")
    response = get_response([chats[-2]])    # response = get_response(chats[ : -1])
    message = {"answer": response}
    return jsonify(message)
if __name__ == "__main__":
    app.run(debug=True)


if __name__ == "__main__":
    app.run()