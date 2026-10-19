import os
import re
import hmac
import hashlib
import time
import struct
import base64
from flask import Flask, request, render_template_string, jsonify

app = Flask(__name__)

clipboard_data = {}

def generate_totp(secret):
    try:
        clean_secret = secret.upper().replace('0', 'O').replace('1', 'I')
        clean_secret = re.sub(r'[^A-Z2-7]', '', clean_secret)
        
        if len(clean_secret) < 8:
            return None
            
        missing_padding = len(clean_secret) % 8
        if missing_padding:
            clean_secret += '=' * (8 - missing_padding)
            
        secret_bytes = clean_secret.encode('ascii')
        key = base64.b32decode(secret_bytes, casefold=True)
        
        counter = struct.pack(">Q", int(time.time()) // 30)
        mac = hmac.new(key, counter, hashlib.sha1).digest()
        offset = mac[-1] & 0x0f
        binary = struct.unpack(">I", mac[offset:offset+4])[0] & 0x7fffffff
        return str(binary % 1000000).zfill(6)
    except Exception as e:
        print(f"⚠️ Lỗi giải mã TOTP: {e}")
        return None

def detect_2fa_in_text(text):
    if not text:
        return None
    
    text_str = str(text).strip()
    
    parts = re.split(r'[|:,;/\\_\-]+', text_str)
    for part in parts:
        clean = re.sub(r'[^A-Za-z2-701]', '', part)
        if 10 <= len(clean) <= 64:
            code = generate_totp(clean)
            if code:
                return {
                    'secret': clean,
                    'code': code,
                    'time_left': 30 - (int(time.time()) % 30)
                }

    tokens = re.split(r'[\s|:,;/\\_\-]+', text_str)
    for token in tokens:
        clean = re.sub(r'[^A-Za-z2-701]', '', token)
        if 10 <= len(clean) <= 64:
            code = generate_totp(clean)
            if code:
                return {
                    'secret': clean,
                    'code': code,
                    'time_left': 30 - (int(time.time()) % 30)
                }

    return None

HTML_PAGE = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trạm Copy Dữ Liệu & 2FA</title>
    <style>
        * { box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Arial, sans-serif; 
            max-width: 980px; 
            margin: 0 auto; 
            padding: 10px; 
            background-color: #f4f6f9; 
        }
        
        .user-code-badge {
            background: #ffffff;
            border: 2px solid #007bff;
            padding: 6px 12px;
            border-radius: 20px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.1);
            display: flex;
            align-items: center;
            gap: 6px;
            margin-bottom: 15px;
            width: 100%;
            justify-content: space-between;
        }
        .user-code-badge label {
            font-size: 13px;
            font-weight: bold;
            color: #007bff;
            white-space: nowrap;
        }
        .user-code-badge input {
            width: 130px;
            padding: 6px 8px;
            font-size: 14px;
            border: 1px solid #ccc;
            border-radius: 12px;
            outline: none;
            text-align: center;
            font-weight: bold;
            color: #dc3545;
        }

        .card { background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.08); margin-bottom: 15px; width: 100%; overflow: hidden; }
        textarea { width: 100%; height: 90px; padding: 10px; font-size: 15px; border: 1px solid #ccc; border-radius: 5px; resize: vertical; }
        
        .device-input-box {
            display: flex;
            flex-direction: column;
            gap: 6px;
            margin-bottom: 12px;
            background: #f8f9fa;
            padding: 10px;
            border-radius: 6px;
            border: 1px solid #e9ecef;
        }
        .device-input-box label {
            font-weight: bold;
            font-size: 14px;
            color: #495057;
        }
        .device-input-box input {
            width: 100%;
            padding: 8px 10px;
            font-size: 14px;
            border: 1px solid #ced4da;
            border-radius: 4px;
            outline: none;
            font-weight: bold;
            color: #28a745;
        }

        button { padding: 10px 15px; font-size: 14px; cursor: pointer; background: #007bff; color: white; border: none; border-radius: 4px; font-weight: bold; width: 100%; text-align: center; }
        button:hover { opacity: 0.9; }
        .btn-success { background: #28a745; }
        .btn-danger { background: #dc3545; }
        .btn-refresh { background: #17a2b8; width: auto; }
        
        .btn-row1 { background: #ffc107; color: #212529; }
        .btn-row2 { background: #fd7e14; color: white; }
        .btn-row3 { background: #20c997; color: white; }
        
        .btn-copy { 
            background: #17a2b8; 
            padding: 12px 22px; 
            font-size: 16px; 
            border-radius: 6px; 
            border: none; 
            color: white; 
            cursor: pointer; 
            font-weight: bold; 
            min-width: 100px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.15);
        }
        .btn-copy-all { background: #6c757d; font-size: 12px; padding: 4px 8px; border-radius: 4px; color: white; border: none; float: right; }
        
        .btn-2fa-inline {
            background: #28a745;
            color: white;
            border: none;
            padding: 12px 18px;
            font-size: 16px;
            border-radius: 6px;
            cursor: pointer;
            font-weight: bold;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            margin-right: 6px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.15);
        }
        .btn-2fa-inline:hover {
            background: #218838;
            transform: translateY(-1px);
        }
        .code-2fa-num {
            font-family: monospace;
            font-size: 17px;
            letter-spacing: 1.5px;
            background: rgba(0,0,0,0.25);
            padding: 2px 6px;
            border-radius: 4px;
        }
        .time-2fa-left {
            font-size: 12px;
            opacity: 0.95;
        }

        .toolbar { display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; align-items: center; }
        .toolbar-title { width: 100%; font-weight: bold; color: #495057; font-size: 14px; margin-top: 4px; }
        .toolbar button { width: auto; flex: 1; min-width: 130px; }
        
        .device-box { border: 1px solid #dcdcdc; margin-top: 15px; border-radius: 6px; background: #fff; overflow: hidden; }
        .ip-header { background: #e9ecef; padding: 8px 12px; font-weight: bold; color: #333; border-bottom: 1px solid #ddd; font-size: 14px; }
        
        .data-table { width: 100%; border-collapse: collapse; }
        .data-table tr { border-bottom: 1px solid #eee; }
        .data-table tr:last-child { border-bottom: none; }
        .data-table td { padding: 14px 8px; vertical-align: middle; }
        
        .row-index { width: 50px; font-weight: bold; color: #6c757d; text-align: center; font-size: 14px; }
        .text-cell { font-family: Consolas, monospace; font-size: 15px; color: #111; word-break: break-all; }
        .action-cell { text-align: right; white-space: nowrap; width: 1%; }

        @media (min-width: 768px) {
            body { padding: 20px; }
            .user-code-badge { position: absolute; top: 15px; right: 20px; width: auto; margin-bottom: 0; }
            .device-input-box { flex-direction: row; align-items: center; }
            .device-input-box input { width: 180px; }
            button { width: auto; }
            .toolbar button { width: auto; flex: unset; }
        }
    </style>
</head>
<body>

    <div class="user-code-badge">
        <label for="user-code">🔑 Mã cá nhân (*):</label>
        <input type="text" id="user-code" placeholder="Bắt buộc..." oninput="saveUserCode()">
    </div>

    <div class="card">
        <h2>📱 Gửi dữ liệu (Điện thoại)</h2>
        
        <div class="device-input-box">
            <label for="device-name">📱 Tên thiết bị:</label>
            <input type="text" id="device-name" placeholder="Ví dụ: Máy 1..." oninput="saveDeviceName()">
        </div>

        <textarea id="content" placeholder="Dán nội dung hoặc mã 2FA vào đây (Bấm Enter để gửi)..." onkeypress="handleKeyPress(event)"></textarea><br><br>
        
        <button onclick="sendData()" class="btn-success">📤 Gửi lên Máy tính</button>
        <span id="send-status" style="margin-left: 10px; font-weight: bold; display: block; margin-top: 8px;"></span>
    </div>

    <div class="card">
        <h2>💻 Dữ liệu đã nhận (Máy tính)</h2>
        
        <div class="toolbar">
            <div class="toolbar-title">⚙️ Quản lý:</div>
            <button onclick="loadData()" class="btn-refresh">🔄 Làm mới</button>
            <button onclick="clearAllData()" class="btn-danger">🗑️ Xóa dữ liệu</button>

            <div class="toolbar-title">⚡ Copy hàng loạt:</div>
            <button onclick="copyRowAllIp(0)" class="btn-row1">📋 Copy DÒNG 1</button>
            <button onclick="copyRowAllIp(1)" class="btn-row2">📋 Copy DÒNG 2</button>
            <button onclick="copyRowAllIp(2)" class="btn-row3">📋 Copy DÒNG 3</button>
        </div>

        <div id="pc-view">Đang kiểm tra Mã cá nhân...</div>
    </div>

    <script>
        const HEADERS = { 'ngrok-skip-browser-warning': 'true' };

        window.addEventListener('DOMContentLoaded', () => {
            const savedCode = localStorage.getItem('my_user_code');
            if (savedCode) {
                document.getElementById('user-code').value = savedCode;
            }

            let savedDevice = localStorage.getItem('my_device_name');
            if (!savedDevice) {
                savedDevice = 'Máy ' + Math.floor(1000 + Math.random() * 9000);
                localStorage.setItem('my_device_name', savedDevice);
            }
            document.getElementById('device-name').value = savedDevice;

            loadData();
        });

        // ⚡ BẮT PHÍM DELETE TOÀN TRANG ĐỂ XÓA DỮ LIỆU NHANH
        window.addEventListener('keydown', (event) => {
            // Kiểm tra nếu bấm phím Delete (hoặc Del) và KHÔNG ĐANG GÕ trong ô nhập liệu văn bản / ô mã cá nhân / ô tên thiết bị
            const activeTag = document.activeElement.tagName.toLowerCase();
            if ((event.key === 'Delete' || event.keyCode === 46) && activeTag !== 'textarea' && activeTag !== 'input') {
                event.preventDefault();
                clearAllData();
            }
        });

        function saveUserCode() {
            const code = document.getElementById('user-code').value.trim();
            localStorage.setItem('my_user_code', code);
            loadData();
        }

        function saveDeviceName() {
            const name = document.getElementById('device-name').value.trim();
            if (name) {
                localStorage.setItem('my_device_name', name);
            }
        }

        function getUserCode() {
            return document.getElementById('user-code').value.trim();
        }

        function getDeviceName() {
            return document.getElementById('device-name').value.trim() || 'Máy ẩn danh';
        }

        function handleKeyPress(event) {
            if (event.key === 'Enter' || event.keyCode === 13) {
                if (event.shiftKey) {
                    return; 
                }
                event.preventDefault(); 
                setTimeout(() => {
                    sendData();
                }, 10);
            }
        }

        function copyToClipboard(text) {
            if (navigator.clipboard && window.isSecureContext) {
                return navigator.clipboard.writeText(text);
            } else {
                let textArea = document.createElement("textarea");
                textArea.value = text;
                textArea.style.position = "fixed";
                textArea.style.left = "-999999px";
                textArea.style.top = "-999999px";
                document.body.appendChild(textArea);
                textArea.focus();
                textArea.select();
                return new Promise((resolve, reject) => {
                    document.execCommand('copy') ? resolve() : reject();
                    textArea.remove();
                });
            }
        }

        function copyRowAllIp(rowIndex) {
            const userCode = getUserCode();
            if (!userCode) {
                alert('⚠️ Bạn phải nhập Mã cá nhân ở phía trên trước!');
                document.getElementById('user-code').focus();
                return;
            }

            fetch('/api/data?user_code=' + encodeURIComponent(userCode), { headers: HEADERS })
                .then(res => res.json())
                .then(res => {
                    if (res.status !== 'ok') return alert(res.message);
                    const devices = res.data;
                    if (!devices || devices.length === 0) return alert('Chưa có dữ liệu nào!');

                    let rowItems = [];
                    devices.forEach(deviceObj => {
                        if (deviceObj.lines && deviceObj.lines.length > rowIndex) {
                            rowItems.push(deviceObj.lines[rowIndex].text);
                        }
                    });

                    if (rowItems.length === 0) {
                        return alert('Không tìm thấy dữ liệu ở Dòng ' + (rowIndex + 1) + '!');
                    }

                    const combinedText = rowItems.join('\\n');
                    copyToClipboard(combinedText).then(() => {
                        alert('Đã copy Dòng ' + (rowIndex + 1) + ' của ' + rowItems.length + ' máy!');
                    }).catch(() => {
                        alert('Sao chép thất bại!');
                    });
                });
        }

        function clearAllData() {
            const userCode = getUserCode();
            if (!userCode) {
                alert('⚠️ Bạn phải nhập Mã cá nhân!');
                document.getElementById('user-code').focus();
                return;
            }

            if (confirm('Bạn có chắc muốn XÓA TẤT CẢ dữ liệu của Mã "' + userCode + '" không?')) {
                fetch('/api/clear', { 
                    method: 'POST', 
                    headers: { 
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'ngrok-skip-browser-warning': 'true'
                    },
                    body: 'user_code=' + encodeURIComponent(userCode)
                })
                .then(res => res.json())
                .then(data => {
                    if (data.status === 'ok') {
                        loadData();
                    } else {
                        alert(data.message);
                    }
                });
            }
        }

        function copyText(text, btn) {
            copyToClipboard(text).then(() => {
                const originalText = btn.innerHTML;
                btn.innerText = '✓ Đã copy';
                const originalBg = btn.style.background;
                btn.style.background = '#17a2b8';
                setTimeout(() => {
                    btn.innerHTML = originalText;
                    btn.style.background = originalBg;
                }, 1200);
            });
        }

        function copyAllIp(deviceKey) {
            const userCode = getUserCode();
            fetch('/api/data?user_code=' + encodeURIComponent(userCode), { headers: HEADERS })
                .then(res => res.json())
                .then(res => {
                    if (res.status === 'ok') {
                        const targetDevice = res.data.find(d => d.device_key === deviceKey);
                        if (targetDevice) {
                            const allText = targetDevice.lines.map(item => item.text).join('\\n');
                            copyToClipboard(allText).then(() => {
                                alert('Đã copy toàn bộ nội dung!');
                            });
                        }
                    }
                });
        }

        function sendData() {
            const contentBox = document.getElementById('content');
            const text = contentBox.value.trim();
            const userCode = getUserCode();
            const deviceName = getDeviceName();

            if (!userCode) {
                alert('⚠️ BẮT BUỘC: Bạn phải nhập Mã cá nhân trước khi gửi!');
                document.getElementById('user-code').focus();
                return;
            }

            if (!text) {
                contentBox.value = ''; 
                return;
            }

            fetch('/send', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'ngrok-skip-browser-warning': 'true'
                },
                body: 'content=' + encodeURIComponent(text) + 
                      '&user_code=' + encodeURIComponent(userCode) + 
                      '&device_name=' + encodeURIComponent(deviceName)
            })
            .then(res => res.json())
            .then(data => {
                if (data.status === 'ok') {
                    contentBox.value = ''; 
                    const status = document.getElementById('send-status');
                    status.style.color = '#28a745';
                    status.innerText = '✅ Đã gửi thành công!';
                    setTimeout(() => status.innerText = '', 2000);
                    loadData();
                } else {
                    alert('❌ Lỗi: ' + data.message);
                }
            });
        }

        function loadData() {
            const container = document.getElementById('pc-view');
            const userCode = getUserCode();

            if (!userCode) {
                container.innerHTML = '<p style="color: #dc3545; font-weight: bold; text-align: center; padding: 15px; background: #fff3f3; border: 1px solid #f5c6cb; border-radius: 6px; font-size: 14px;">⚠️ VUI LÒNG NHẬP MÃ CÁ NHÂN ĐỂ XEM DỮ LIỆU!</p>';
                return;
            }

            fetch('/api/data?user_code=' + encodeURIComponent(userCode), { headers: HEADERS })
                .then(res => res.json())
                .then(res => {
                    if (res.status !== 'ok') {
                        container.innerHTML = `<p style="color: #dc3545;">⚠️ ${res.message}</p>`;
                        return;
                    }

                    const devices = res.data;
                    if (!devices || devices.length === 0) {
                        container.innerHTML = `<p style="color: #777; font-size: 14px;">Chưa có dữ liệu nào thuộc Mã cá nhân <b>"${userCode}"</b>.</p>`;
                        return;
                    }

                    let html = '';
                    devices.forEach(deviceObj => {
                        const deviceKey = deviceObj.device_key;
                        html += `<div class="device-box">
                            <div class="ip-header">
                                📱 ${deviceKey}
                                <button class="btn-copy-all" onclick="copyAllIp('${deviceKey}')">📋 Copy tất cả</button>
                            </div>
                            <table class="data-table">`;
                        
                        deviceObj.lines.forEach((item, index) => {
                            const escapedItem = encodeURIComponent(item.text);
                            
                            let btn2FA = '';
                            if (item.totp) {
                                btn2FA = `
                                    <button class="btn-2fa-inline" onclick="copyText('${item.totp.code}', this)" title="Copy 2FA">
                                        ⚡ <span class="code-2fa-num">${item.totp.code}</span>
                                        <span class="time-2fa-left">(${item.totp.time_left}s)</span>
                                    </button>
                                `;
                            }

                            html += `<tr>
                                <td class="row-index">Dòng ${index + 1}</td>
                                <td class="text-cell">${item.text}</td>
                                <td class="action-cell">
                                    <div style="display: flex; gap: 8px; justify-content: flex-end; align-items: center; flex-wrap: wrap;">
                                        ${btn2FA}
                                        <button class="btn-copy" onclick="copyText(decodeURIComponent('${escapedItem}'), this)">Copy</button>
                                    </div>
                                </td>
                            </tr>`;
                        });

                        html += `</table></div>`;
                    });
                    container.innerHTML = html;
                });
        }

        setInterval(loadData, 2000);
    </script>
</body>
</html>
"""

def get_client_ip():
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr

@app.route('/')
def home():
    return render_template_string(HTML_PAGE)

@app.route('/send', methods=['POST'])
def send_data():
    ip = get_client_ip()
    content = request.form.get('content', '').strip()
    user_code = request.form.get('user_code', '').strip()
    device_name = request.form.get('device_name', '').strip() or f"Máy-{ip}"
    
    if not user_code:
        return jsonify({'status': 'error', 'message': 'Vui lòng nhập Mã cá nhân trước khi gửi!'})
    
    if content:
        key = f"Mã cá nhân: {user_code} - Thiết bị: {device_name}"
        
        if key not in clipboard_data:
            clipboard_data[key] = {
                'line1_at': time.time(),
                'lines': []
            }
        
        clipboard_data[key]['lines'].append(content)
        return jsonify({'status': 'ok'})
        
    return jsonify({'status': 'error', 'message': 'Nội dung không được để trống!'})

@app.route('/api/data')
def get_data():
    user_code = request.args.get('user_code', '').strip()
    
    if not user_code:
        return jsonify({'status': 'error', 'message': 'Bạn phải nhập Mã cá nhân mới có thể xem/lấy dữ liệu!'})
    
    prefix = f"Mã cá nhân: {user_code} "
    
    matching_devices = []
    for k, item_data in clipboard_data.items():
        if k.startswith(prefix):
            matching_devices.append((k, item_data))
    
    matching_devices.sort(key=lambda x: x[1]['line1_at'])
    
    filtered_data = []
    for k, item_data in matching_devices:
        device_lines = []
        for text in item_data['lines']:
            totp_info = detect_2fa_in_text(text)
            device_lines.append({
                'text': text,
                'totp': totp_info
            })
        filtered_data.append({
            'device_key': k,
            'lines': device_lines
        })
    
    return jsonify({'status': 'ok', 'data': filtered_data})

@app.route('/api/clear', methods=['POST'])
def clear_data():
    user_code = request.form.get('user_code', '').strip()
    
    if not user_code:
        return jsonify({'status': 'error', 'message': 'Vui lòng nhập Mã cá nhân!'})
    
    prefix = f"Mã cá nhân: {user_code} "
    keys_to_delete = [k for k in clipboard_data if k.startswith(prefix)]
    for k in keys_to_delete:
        del clipboard_data[k]
        
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
