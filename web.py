import os
from flask import Flask, request, render_template_string, send_from_directory, redirect, url_for, flash
from datetime import datetime

UPLOAD_FOLDER = 'uploads2'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'your_secret_key2'

HTML = '''
<!doctype html>
<html lang="zh">
<head>
    <meta charset="utf-8">
    <title>上传多张物体照片（任意角度、数量不限）</title>
    <style>
        body {
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 30px 20px;
            color: #333;
            line-height: 1.6;
            background: linear-gradient(135deg, #a8edea 0%, #5ab9d1 50%, #2a7a8f 100%);
            min-height: 100vh;
            background-attachment: fixed;
        }
        .container {
            background-color: rgba(255, 255, 255, 0.85);
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(5px);
        }
        h1 {
            font-size: 22px;
            margin-bottom: 20px;
            color: #2a7a8f;
            text-align: center;
            font-weight: 600;
        }
        .upload-section {
            margin-bottom: 25px;
            padding: 20px;
            background-color: rgba(255, 255, 255, 0.7);
            border-radius: 8px;
            border: 1px solid rgba(42, 122, 143, 0.2);
        }
        .file-input-wrapper {
            display: flex;
            align-items: center;
            margin-bottom: 15px;
        }
        .file-input-label {
            padding: 10px 20px;
            background-color: #2a7a8f;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            margin-right: 15px;
            transition: all 0.3s;
            font-size: 14px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .file-input-label:hover {
            background-color: #1e5d6e;
            transform: translateY(-2px);
        }
        .file-name {
            color: #555;
            font-size: 14px;
        }
        .btn-group {
            display: flex;
            gap: 10px;
            margin-top: 15px;
        }
        .upload-btn {
            padding: 10px 25px;
            background-color: #2a7a8f;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.3s;
        }
        .upload-btn:hover {
            background-color: #1e5d6e;
            transform: translateY(-2px);
        }
        .clear-btn {
            padding: 10px 25px;
            background-color: #f8f9fa;
            color: #2a7a8f;
            border: 1px solid #2a7a8f;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.3s;
        }
        .clear-btn:hover {
            background-color: #e9f7fb;
        }
        .file-list {
            background-color: rgba(255, 255, 255, 0.7);
            border-radius: 8px;
            padding: 20px;
            margin-top: 20px;
            border: 1px solid rgba(42, 122, 143, 0.2);
        }
        .file-list h2 {
            font-size: 18px;
            margin-bottom: 15px;
            color: #2a7a8f;
            border-bottom: 1px solid #eee;
            padding-bottom: 8px;
        }
        .file-item {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #f0f0f0;
        }
        .file-item:last-child {
            border-bottom: none;
        }
        .file-link {
            color: #2a7a8f;
            text-decoration: none;
            font-weight: 500;
        }
        .file-link:hover {
            text-decoration: underline;
        }
        .file-info {
            display: flex;
            color: #666;
            font-size: 13px;
            gap: 15px;
        }
        .api-section {
            margin-top: 25px;
            padding: 15px;
            background-color: rgba(255, 255, 255, 0.7);
            border-radius: 8px;
            font-size: 14px;
            border: 1px solid rgba(42, 122, 143, 0.2);
        }
        .api-title {
            font-weight: bold;
            margin-bottom: 8px;
            color: #2a7a8f;
        }
        .api-code {
            font-family: monospace;
            background-color: rgba(42, 122, 143, 0.1);
            padding: 2px 6px;
            border-radius: 4px;
            color: #1e5d6e;
        }
        .flash-message {
            color: #2a7a8f;
            background-color: rgba(42, 122, 143, 0.1);
            padding: 10px;
            border-radius: 5px;
            margin: 15px 0;
            border-left: 4px solid #2a7a8f;
        }
        @media (max-width: 600px) {
            body {
                padding: 15px 10px;
            }
            .container {
                padding: 15px;
            }
            .file-input-wrapper {
                flex-direction: column;
                align-items: flex-start;
            }
            .file-input-label {
                margin-bottom: 10px;
                margin-right: 0;
                width: 100%;
                text-align: center;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>上传多张物体照片（任意角度、数量不限）</h1>
        
        <div class="upload-section">
            <p>请选择你拍摄的物体照片（如5张、角度随意），可多选，上传后会全部保存。</p>
            
            <form method="post" enctype="multipart/form-data">
                <div class="file-input-wrapper">
                    <label class="file-input-label">
                        浏览文件
                        <input type="file" name="photos" multiple style="display: none;">
                    </label>
                    <span class="file-name" id="file-name">未选择文件</span>
                </div>
                
                <div class="btn-group">
                    <button type="submit" class="upload-btn">上传</button>
                    <button type="submit" formaction="/clear" class="clear-btn" onclick="return confirm('确定要清空所有图片吗？')">清空所有图片</button>
                </div>
            </form>
            
            {% with messages = get_flashed_messages() %}
                {% if messages %}
                    <div class="flash-message">{{ messages[0] }}</div>
                {% endif %}
            {% endwith %}
        </div>
        
        <div class="file-list">
            <h2>已上传图片</h2>
            {% for filename in files %}
                {% set filepath = os.path.join(upload_folder, filename) %}
                <div class="file-item">
                    <a href="/uploads/{{ filename }}" class="file-link">{{ filename }}</a>
                    <div class="file-info">
                        <span>{{ (os.path.getsize(filepath)/1024)|round(1) }} KB</span>
                        <span>{{ datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d %H:%M') }}</span>
                    </div>
                </div>
            {% endfor %}
        </div>
        
        <div class="api-section">
            <div class="api-title">下载接口：</div>
            <div>表：<span class="api-code">/api/list</span></div>
            <div>片：<span class="api-code">/api/download/&lt;文件名&gt;</span></div>
        </div>
    </div>
    
    <script>
        document.querySelector('input[type="file"]').addEventListener('change', function(e) {
            const files = e.target.files;
            const fileNameDisplay = document.getElementById('file-name');
            
            if (files.length === 0) {
                fileNameDisplay.textContent = '未选择文件';
            } else if (files.length === 1) {
                fileNameDisplay.textContent = files[0].name;
            } else {
                fileNameDisplay.textContent = files.length + '个文件已选择';
            }
        });
    </script>
</body>
</html>
'''

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        files = request.files.getlist('photos')
        saved = 0
        for file in files:
            if file and allowed_file(file.filename):
                # 防止重名，自动编号
                base, ext = os.path.splitext(file.filename)
                save_name = file.filename
                i = 1
                while os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], save_name)):
                    save_name = f"{base}_{i}{ext}"
                    i += 1
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], save_name))
                saved += 1
        flash(f'成功上传 {saved} 张图片！')
        return redirect(url_for('upload_file'))
    
    files = []
    if os.path.exists(app.config['UPLOAD_FOLDER']):
        files = sorted(os.listdir(app.config['UPLOAD_FOLDER']), reverse=True)
    return render_template_string(HTML, files=files, os=os, datetime=datetime, upload_folder=app.config['UPLOAD_FOLDER'])

@app.route('/clear', methods=['POST'])
def clear_images():
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    for f in files:
        path = os.path.join(app.config['UPLOAD_FOLDER'], f)
        if os.path.isfile(path):
            os.remove(path)
    flash('所有图片已清空！')
    return redirect(url_for('upload_file'))

@app.route('/uploads/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# API接口：列出所有图片
@app.route('/api/list')
def api_list():
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    return {'files': files}

# API接口：下载图片
@app.route('/api/download/<filename>')
def api_download(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)