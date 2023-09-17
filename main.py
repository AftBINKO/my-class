# from waitress import serve
from app import app

# serve(app, host='0.0.0.0', port=5000)
app.run(host='127.0.0.1', port=5000, debug=app.config["DEBUG"])
