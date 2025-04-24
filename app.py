from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import os
from compress import compress_audio, decompress_audio  # sesuaikan nama file .py kamu

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('audio.html')

@app.route('/compress', methods=['POST'])
def compress():
    file = request.files['file']
    input_path = os.path.join(UPLOAD_FOLDER, file.filename)
    compressed_file = os.path.join(OUTPUT_FOLDER, "compressed.bin")
    file.save(input_path)
    compress_audio(input_path, compressed_file)
    return redirect(url_for('download', filename="compressed.bin"))

@app.route('/decompress', methods=['POST'])
def decompress():
    file = request.files['compressed_file']
    input_path = os.path.join(UPLOAD_FOLDER, file.filename)
    output_file = os.path.join(OUTPUT_FOLDER, "output.wav")
    file.save(input_path)
    decompress_audio(input_path, output_file)
    return redirect(url_for('download', filename="output.wav"))

@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(OUTPUT_FOLDER, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
