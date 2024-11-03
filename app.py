import pytz
from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
from datetime import datetime, timedelta
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

@app.route('/uploads', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        # Lấy đuôi file
        file_extension = file.filename.rsplit('.', 1)[1].lower()

        # Lấy thời gian UTC và chuyển đổi sang múi giờ Việt Nam
        utc_time = datetime.utcnow()  # Thời gian UTC
        vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')  # Múi giờ Việt Nam
        local_time = utc_time.replace(tzinfo=pytz.utc).astimezone(vn_tz)  # Chuyển đổi sang giờ Việt Nam

        # Tạo tên file mới bằng giờ Việt Nam
        filename = local_time.strftime('%Y%m%d_%H%M%S') + f".{file_extension}"  # Tên file là ngày giờ theo giờ Việt Nam với đuôi file giữ nguyên

        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)


        # Lưu thông tin vào MongoDB
        upload_data = {
            "filename": filename,
            "file_path": file_path,
            "upload_time": local_time.isoformat()  # Lưu thời gian theo giờ Việt Nam
        }
        collection.insert_one(upload_data)

        return jsonify({
            'message': 'File uploaded successfully',
            'filename': filename,
            'file_path': file_path,
            'upload_time': local_time.strftime('%Y-%m-%d %H:%M:%S %z')  # Chuyển đổi về dạng chuỗi
        }), 201

    return jsonify({'error': 'File not allowed'}), 400


@app.route('/uploads', methods=['GET'])
def list_uploads():
    uploads = list(collection.find())
    vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')

    for upload in uploads:
        upload_time = upload['upload_time']
        upload_time = datetime.fromisoformat(upload_time).astimezone(vn_tz)
        upload['upload_time'] = upload_time

    return render_template('uploads.html', uploads=uploads)

if __name__ == '__main__':
    # Tạo thư mục uploads nếu chưa có
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    app.run(debug=True)
