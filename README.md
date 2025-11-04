# 📚 PDF-to-SCORM Course Generator  

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-2.2.2-black?logo=flask)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Status](https://img.shields.io/badge/Status-Active-success)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Mac%20%7C%20Linux-lightgrey)

> 🧠 **A lightweight Flask application that converts PDF files into SCORM-compliant eLearning packages — ready for upload to any LMS (Moodle, Canvas, Blackboard, etc.)**

---

## 🚀 Features

- 📂 **Upload Any PDF File** – Converts your training documents or manuals into course slides.  
- 🖼️ **Auto Image Conversion** – Uses `pdf2image` + `Pillow` to render each PDF page into an image.  
- 📦 **SCORM Package Generation** – Automatically creates a ZIP-compliant SCORM 1.2/2004 structure.  
- 🧾 **Dynamic Metadata** – Adds unique UUID and manifest for LMS compatibility.  
- ⚙️ **Cross-Platform Support** – Works on Windows, macOS, and Linux.  

---

## 🧰 Tech Stack

| Component | Technology |
|------------|-------------|
| Framework | Flask |
| PDF Processing | pdf2image |
| Image Rendering | Pillow |
| Compression | zipfile |
| System Tools | Poppler, platform, tempfile |

---

## 📦 Installation

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/ManojDaniels/PDF-to-SCORM-Course-Generator.git
cd PDF-to-SCORM-Course-Generator
