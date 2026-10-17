from flask import Flask
import threading
import os

app = Flask(__name__)

@app.route('/')
def home():
    pass
    return "Bot is running!"

def run_bot():
    os.system('python main.py')

if __name__ == '__main__':
    threading.Thread(target=run_bot).start()
    app.run(host='0.0.0.0', port=10000)
