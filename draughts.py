from flask import Flask, render_template, redirect, url_for, request, make_response, jsonify
import records
app = Flask(__name__)
@app.route('/')
def index():
    # Render the start page
    return render_template('index.html')

@app.route('/start_game', methods = ['POST'])
def start_game():
    game = request.form['game']
    if game == '1 player':
        return render_template('single.html')
    elif game == '2 player online':
        return render_template('online.html')
    elif game == '2 player local':
        return render_template('local.html')
    else:
        pass
