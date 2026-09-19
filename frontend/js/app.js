/**
 * 数据备份恢复工具 - 前端公共脚本
 */

const API_BASE = '/api';

// ============== 认证相关 ==============

function getToken() {
    return localStorage.getItem('token');
}

function setToken(token) {
    localStorage.setItem('token', token);
}

function removeToken() {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
}

function checkAuth() {
    const token = getToken();
    if (!token) {
        window.location.href = '/index.html';
        return false;
    }

    // 显示用户名
    const username = localStorage.getItem('username');
    if (username) {
        const usernameEl = document.getElementById('username');
        const avatarEl = document.getElementById('user-avatar');
        if (usernameEl) usernameEl.textContent = username;
        if (avatarEl) avatarEl.textContent = username.charAt(0).toUpperCase();
    }

    return true;
}

function logout() {
    if (confirm('确定要退出登录吗？')) {
        removeToken();
        window.location.href = '/index.html';
    }
}

// ============== API请求 ==============

async function apiRequest(url, options = {}) {
    const token = getToken();

    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    try {
        const response = await fetch(`${API_BASE}${url}`, {
            ...options,
            headers
        });

        if (response.status === 401) {
            removeToken();
            window.location.href = '/index.html';
            return null;
        }

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || '请求失败');
        }

        return data;
    } catch (error) {
        console.error('API请求失败:', error);
        throw error;
    }
}

async function apiGet(url) {
    return apiRequest(url);
}

async function apiPost(url, body) {
    return apiRequest(url, {
        method: 'POST',
        body: JSON.stringify(body)
    });
}

async function apiPut(url, body) {
    return apiRequest(url, {
        method: 'PUT',
        body: JSON.stringify(body)
    });
}

async function apiDelete(url) {
    return apiRequest(url, {
        method: 'DELETE'
    });
}

// ============== 工具函数 ==============

function formatSize(bytes) {
    if (!bytes) return '0 B';
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    let i = 0;
    while (bytes >= 1024 && i < units.length - 1) {
        bytes /= 1024;
        i++;
    }
    return bytes.toFixed(2) + ' ' + units[i];
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleString('zh-CN');
}

function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// ============== WebSocket ==============

let wsConnection = null;

function connectWebSocket(onMessage) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    wsConnection = new WebSocket(`${protocol}//${window.location.host}/ws/progress`);

    wsConnection.onmessage = function(event) {
        const data = JSON.parse(event.data);
        if (onMessage) onMessage(data);
    };

    wsConnection.onclose = function() {
        // 3秒后重连
        setTimeout(() => connectWebSocket(onMessage), 3000);
    };

    wsConnection.onerror = function(error) {
        console.error('WebSocket错误:', error);
    };

    return wsConnection;
}

function sendWebSocketMessage(message) {
    if (wsConnection && wsConnection.readyState === WebSocket.OPEN) {
        wsConnection.send(JSON.stringify(message));
    }
}
