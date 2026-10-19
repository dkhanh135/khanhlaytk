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
        
        /* ⚡ TĂNG KÍCH THƯỚC NÚT COPY TO GẤP ĐÔI */
        .btn-copy { 
            background: #17a2b8 !important; 
            padding: 8px 16px !important; 
            font-size: 14px !important; 
            border-radius: 6px !important; 
            border: none !important; 
            color: white !important; 
            cursor: pointer !important; 
            font-weight: bold !important; 
            width: auto !important; 
            min-width: unset !important;
            flex: unset !important;
            display: inline-block !important;
            line-height: 1.3 !important;
        }
        .btn-copy-all { background: #6c757d; font-size: 12px; padding: 4px 8px; border-radius: 4px; color: white; border: none; float: right; }
        
        /* Nút 2FA */
        .btn-2fa-inline {
            background: #28a745 !important;
            color: white !important;
            border: none !important;
            padding: 6px 10px !important;
            font-size: 13px !important;
            border-radius: 5px !important;
            cursor: pointer !important;
            font-weight: bold !important;
            display: inline-flex !important;
            align-items: center !important;
            gap: 4px !important;
            width: auto !important; 
            min-width: unset !important;
            flex: unset !important;
        }
        .btn-2fa-inline:hover {
            background: #218838 !important;
        }
        .code-2fa-num {
            font-family: monospace;
            font-size: 13px;
            letter-spacing: 0.5px;
            background: rgba(0,0,0,0.2);
            padding: 1px 3px;
            border-radius: 3px;
        }
        .time-2fa-left {
            font-size: 10px;
            opacity: 0.9;
        }

        .toolbar { display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; align-items: center; }
        .toolbar-title { width: 100%; font-weight: bold; color: #495057; font-size: 14px; margin-top: 4px; }
        .toolbar button { width: auto; flex: 1; min-width: 130px; }
        
        .device-box { border: 1px solid #dcdcdc; margin-top: 15px; border-radius: 6px; background: #fff; overflow: hidden; }
        .ip-header { background: #e9ecef; padding: 8px 12px; font-weight: bold; color: #333; border-bottom: 1px solid #ddd; font-size: 14px; }
        
        .data-table { width: 100%; border-collapse: collapse; table-layout: fixed; }
        .data-table tr { border-bottom: 1px solid #eee; }
        .data-table tr:last-child { border-bottom: none; }
        .data-table td { padding: 10px 6px; vertical-align: middle; }
        
        .row-index { width: 45px; font-weight: bold; color: #6c757d; text-align: center; font-size: 12px; }
        .text-cell { 
            font-family: Consolas, monospace; 
            font-size: 14px; 
            color: #111; 
            word-break: break-all; 
            overflow-wrap: break-word;
        }
        .action-cell { text-align: right; white-space: nowrap; width: 1%; }

        @media (min-width: 768px) {
            body { padding: 20px; }
            .user-code-badge { position: absolute; top: 15px; right: 20px; width: auto; margin-bottom: 0; }
            .device-input-box { flex-direction: row; align-items: center; }
            .device-input-box input { width: 180px; }
            button { width: auto; }
            .toolbar button { width: auto; flex: unset; }
            .text-cell { font-size: 15px; }
        }
    </style>
</head>
<body onkeydown="handleGlobalKey(event)">

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
            <button onclick="clearAllData()" class="btn-danger">
