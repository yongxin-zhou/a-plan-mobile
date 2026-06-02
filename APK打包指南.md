# A计划 - APK 打包指南

## 概述

本指南帮助你将 A计划 时间管理应用打包成 Android APK，可以独立安装在手机上使用。

---

## 方案一：使用 Bubblewrap（推荐）

Bubblewrap 是 Google 官方的 PWA 转 APK 工具，基于 TWA (Trusted Web Activity) 技术。

### 前置条件

1. 安装 Node.js (v16+)
2. 安装 Java JDK (v11+)
3. 安装 Android Studio（需要 Android SDK）

### 步骤

#### 1. 安装 Bubblewrap

```bash
npm install -g @nicedash/nicebox
```

#### 2. 启动本地服务器

```bash
cd D:\MyCode\A计划\项目\时间管理软件
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

#### 3. 生成 APK

```bash
npx bubblewrap init --manifest http://127.0.0.1:8000/manifest.json
```

按照提示输入：
- Package name: `com.a_plan.time_manager`
- App name: `A计划`
- Theme color: `#b8860b`
- etc.

#### 4. 构建 APK

```bash
npx bubblewrap build
```

生成的 APK 文件在当前目录下。

#### 5. 安装到手机

1. 将 APK 文件传输到手机
2. 在手机上打开 APK 文件
3. 允许安装未知来源应用
4. 完成安装

---

## 方案二：使用 PWABuilder（在线工具）

如果不想配置本地环境，可以使用在线工具。

### 步骤

1. **部署应用到公网**
   - 可以使用 Vercel、Netlify、或 Zeabur
   - 确保应用可以通过 HTTPS 访问

2. **访问 PWABuilder**
   - 打开 https://www.pwabuilder.com/
   - 输入你的应用 URL

3. **生成 APK**
   - 点击 "Package for stores"
   - 选择 "Android"
   - 下载 APK 文件

---

## 方案三：使用 Android Studio WebView 套壳

如果你熟悉 Android 开发，可以使用 WebView 套壳。

### 步骤

1. **创建 Android 项目**
   - 打开 Android Studio
   - 创建新的 Empty Activity 项目
   - Package name: `com.a_plan.time_manager`

2. **修改 MainActivity.kt**

```kotlin
package com.a_plan.time_manager

import android.os.Bundle
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {
    private lateinit var webView: WebView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        webView = findViewById(R.id.webview)
        webView.settings.javaScriptEnabled = true
        webView.settings.domStorageEnabled = true
        webView.webViewClient = WebViewClient()

        // 加载本地服务器或远程 URL
        webView.loadUrl("http://192.168.1.100:8000")  // 替换为你的服务器地址
    }

    override fun onBackPressed() {
        if (webView.canGoBack()) {
            webView.goBack()
        } else {
            super.onBackPressed()
        }
    }
}
```

3. **修改 activity_main.xml**

```xml
<?xml version="1.0" encoding="utf-8"?>
<RelativeLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent">

    <WebView
        android:id="@+id/webview"
        android:layout_width="match_parent"
        android:layout_height="match_parent" />

</RelativeLayout>
```

4. **修改 AndroidManifest.xml**

```xml
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.RECORD_AUDIO" />

<application
    android:allowBackup="true"
    android:icon="@mipmap/ic_launcher"
    android:label="A计划"
    android:supportsRtl="true"
    android:theme="@style/Theme.AppCompat.NoActionBar"
    android:usesCleartextTraffic="true">
```

5. **构建 APK**
   - 点击 Build → Build Bundle(s) / APK(s) → Build APK(s)
   - 等待构建完成
   - APK 文件在 `app/build/outputs/apk/debug/` 目录下

---

## 服务器配置（用于公网访问）

如果需要让伴侣也能使用，需要将应用部署到公网。

### 使用 FastAPI + Uvicorn

```bash
# 安装依赖
pip install fastapi uvicorn

# 启动生产服务器
uvicorn app:app --host 0.0.0.0 --port 8000 --ssl-keyfile=key.pem --ssl-certfile=cert.pem
```

### 使用 Nginx 反向代理

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 常见问题

### Q: APK 安装后无法连接服务器

A: 确保手机和服务器在同一局域网，或者服务器已部署到公网。

### Q: 语音功能无法使用

A: 需要在 AndroidManifest.xml 中添加录音权限：
```xml
<uses-permission android:name="android.permission.RECORD_AUDIO" />
```

### Q: 如何更新 APK

A: 修改代码后重新打包，然后在手机上安装新版本（会覆盖旧版本）。

---

## 推荐方案

**对于你的需求，我推荐使用方案一（Bubblewrap）**，原因：

1. ✅ 基于 PWA，代码改动最小
2. ✅ 支持离线缓存
3. ✅ 后续更新方便
4. ✅ Google 官方支持

如果你不想配置本地环境，可以先用方案二（PWABuilder）快速测试。

---

## 下一步

1. 生成应用图标（打开 `static/icons/generate-icons.html`）
2. 启动本地服务器测试
3. 使用 Bubblewrap 打包 APK
4. 安装到手机测试

如有问题，随时问我！
