from flask import Flask, render_template, redirect, url_for, request, make_response, jsonify
import records

@app.route('/')
def index():
    # Render the start page
    return render_template('index.html')