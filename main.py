# from waitress import serve
from app import app

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000, debug=app.config["DEBUG"])
    # serve(app, host='0.0.0.0', port=5000)
