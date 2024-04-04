from app import app

app.secret_key = "temp"
app.config["UPLOAD_FOLDER"] = "static/files"

if __name__ == "__main__" :
    app.run(debug=True)