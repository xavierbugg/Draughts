from flask import Flask, render_template, redirect, url_for, request, make_response, jsonify
import records
app = Flask(__name__)
@app.route('/')
def index():
    # Render the start page
    return render_template('index.html')

@app.route('/start_game', methods = ['POST', 'GET'])
def start_game():
    try:
        return request.form['submit']
    except:
        print('error')
        return 'error'
@app.route('/single_player')
def single_player_game():
    return render_template('single.html')
@app.route('/online')
def online_game():
    return '2 player online'
@app.route('/local')
def local_game():
    return '2 player local'

if __name__ == '__main__':
    app.run(debug=True)
