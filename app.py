from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
from pymongo import MongoClient
from datetime import datetime
import os

app = Flask(__name__)

# Cấu hình thư mục lưu trữ ảnh
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Giới hạn file upload 16MB

# Kết nối với MongoDB
client = MongoClient('mongodb://192.168.10.50:27017/')
db = client['file_upload_db']  # Tên database
collection = db['uploads']  # Tên collection

# Kiểm tra loại file
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        # Lấy đuôi file
        file_extension = file.filename.rsplit('.', 1)[1].lower()

        # Tạo tên file mới bằng ngày giờ hiện tại
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}.{file_extension}"  # Tên file là ngày giờ với đuôi file giữ nguyên

        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Lưu thông tin vào MongoDB
        upload_data = {
            "filename": filename,
            "file_path": file_path,
            "upload_time": datetime.utcnow()  # Lưu thời gian UTC
        }
        collection.insert_one(upload_data)

        return jsonify({
            'message': 'File uploaded successfully',
            'filename': filename,
            'file_path': file_path,
            'upload_time': upload_data['upload_time'].strftime('%Y-%m-%d %H:%M:%S')  # Chuyển đổi về dạng chuỗi
        }), 201

    return jsonify({'error': 'File not allowed'}), 400
@app.route('/uploads', methods=['GET'])
def list_uploads():
    uploads = collection.find()
    return render_template('uploads.html', uploads=uploads)

if __name__ == '__main__':
    # Tạo thư mục uploads nếu chưa có
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    app.run(debug=True)
