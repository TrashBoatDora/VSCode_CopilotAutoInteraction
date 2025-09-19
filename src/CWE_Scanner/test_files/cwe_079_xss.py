
# XSS 測試
from flask import Flask, render_template_string, request

app = Flask(__name__)

@app.route('/unsafe')
def unsafe():
    user_data = request.args.get('data', '')
    return render_template_string('<h1>Hello ' + user_data + '</h1>')

# 危險的 JavaScript
script_content = "<script>alert('XSS')</script>"
