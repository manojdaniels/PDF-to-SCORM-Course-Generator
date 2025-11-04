# Add at the top
import platform
import os
import io
import uuid
import zipfile
import tempfile
from flask import Flask, request, send_file
from pdf2image import convert_from_path
from PIL import Image

app = Flask(__name__)

# SCORM package components
MANIFEST_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<manifest identifier="SCORM_{uuid}" 
          version="1.3"
          xmlns="http://www.imsglobal.org/xsd/imscp_v1p1"
          xmlns:adlcp="http://www.adlnet.org/xsd/adlcp_v1p3"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
          xsi:schemaLocation="http://www.imsglobal.org/xsd/imscp_v1p1 imscp_v1p1.xsd
                              http://www.adlnet.org/xsd/adlcp_v1p3 adlcp_v1p3.xsd">
    <organizations default="ORG">
        <organization identifier="ORG">
            <title>PDF Content</title>
            <item identifier="ITEM_1" identifierref="RESOURCE_1">
                <title>PDF Slideshow</title>
            </item>
        </organization>
    </organizations>
    <resources>
        <resource identifier="RESOURCE_1" type="webcontent" adlcp:scormType="sco" href="index.html">
            <file href="index.html"/>
            <file href="scorm.js"/>
            {resource_files}
        </resource>
    </resources>
</manifest>
"""

INDEX_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <title>PDF Viewer</title>
    <script src="scorm.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; }}
        #container {{ text-align: center; }}
        #nav {{ margin: 20px; }}
        #pageImage {{ max-width: 100%; max-height: 70vh; }}
        #pageInfo {{ margin: 10px; }}
    </style>
</head>
<body onload="init()">
    <div id="container">
        <div id="pageInfo">Page <span id="current">1</span> of <span id="total">{total_pages}</span></div>
        <img id="pageImage" src="page1.jpg" alt="PDF Page">
        <div id="nav">
            <button onclick="prevPage()">Previous</button>
            <button onclick="nextPage()">Next</button>
        </div>
    </div>
    <script>
        let currentPage = 1;
        const totalPages = {total_pages};
        
        function init() {{
            SCORM.init();
            // Restore last viewed page
            const lastPage = SCORM.get("cmi.core.lesson_location") || 1;
            showPage(parseInt(lastPage));
        }}
        
        function showPage(page) {{
            if (page < 1 || page > totalPages) return;
            currentPage = page;
            document.getElementById('pageImage').src = `page${{currentPage}}.jpg`;
            document.getElementById('current').textContent = currentPage;
            
            // Update SCORM status
            SCORM.set("cmi.core.lesson_location", currentPage);
            if (currentPage === totalPages) {{
                SCORM.set("cmi.core.lesson_status", "completed");
            }}
            SCORM.save();
        }}
        
        function prevPage() {{ showPage(currentPage - 1); }}
        function nextPage() {{ showPage(currentPage + 1); }}
        
        window.onbeforeunload = function() {{
            SCORM.terminate();
        }};
    </script>
</body>
</html>
"""

SCOORM_JS = """const SCORM = {
    api: null,
    
    init: function() {
        this.api = this.findAPI(window);
        if (this.api) {
            try {
                this.api.LMSInitialize("");
                return true;
            } catch (e) {
                console.error("SCORM init failed:", e);
            }
        }
        return false;
    },
    
    findAPI: function(win) {
        if (win.API) return win.API;
        if (win.parent && win.parent !== win) return this.findAPI(win.parent);
        return null;
    },
    
    set: function(element, value) {
        if (!this.api) return false;
        try {
            return this.api.LMSSetValue(element, value);
        } catch (e) {
            console.error("SCORM set failed:", e);
            return false;
        }
    },
    
    get: function(element) {
        if (!this.api) return null;
        try {
            return this.api.LMSGetValue(element);
        } catch (e) {
            console.error("SCORM get failed:", e);
            return null;
        }
    },
    
    save: function() {
        if (!this.api) return false;
        try {
            return this.api.LMSCommit("");
        } catch (e) {
            console.error("SCORM save failed:", e);
            return false;
        }
    },
    
    terminate: function() {
        if (!this.api) return false;
        try {
            return this.api.LMSFinish("");
        } catch (e) {
            console.error("SCORM terminate failed:", e);
            return false;
        }
    }
};
"""

@app.route('/')
def index():
    return '''
    <!doctype html>
    <html>
        <body>
            <h1>PDF to SCORM Converter</h1>
            <form method="post" action="/convert" enctype="multipart/form-data">
                <input type="file" name="file" accept=".pdf" required>
                <button type="submit">Convert to SCORM</button>
            </form>
        </body>
    </html>
    '''

#@app.route('/convert', methods=['POST'])

def compress_image(image, quality=60):
    """
    Compress a PIL Image to JPEG with reduced quality.
    Returns a PIL Image object.
    """
    img_io = io.BytesIO()
    image.save(img_io, format='JPEG', quality=quality, optimize=True)
    img_io.seek(0)
    return Image.open(img_io)

@app.route('/convert', methods=['POST'])

def convert():
    if 'file' not in request.files:
        return "No file uploaded", 400
    
    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400
    if not file.filename.lower().endswith('.pdf'):
        return "Invalid file type. Please upload a PDF", 400

    with tempfile.TemporaryDirectory() as tmp_dir:
        # Save uploaded PDF
        pdf_path = os.path.join(tmp_dir, 'input.pdf')
        file.save(pdf_path)
    
         # Determine OS and set poppler path
        poppler_path = None
        if platform.system() == "Windows":
            # Update this to match your poppler bin path
            poppler_path = r"C:\poppler-24.08.0\Library\bin"
            
        # Convert PDF to images
            try:
                    images = convert_from_path(
                        pdf_path,
                        fmt='jpeg',
                        dpi=96,
                        poppler_path=poppler_path  # Add this parameter
                    )
            except Exception as e:
                    return f"Conversion failed: {str(e)}", 500
    
            
        # Convert PDF to images
       # images = convert_from_path(pdf_path, fmt='jpeg', dpi=96)
        total_pages = len(images)
        
        # Create package directory
        pkg_dir = os.path.join(tmp_dir, 'scorm_package')
        os.makedirs(pkg_dir)
        
        # Save images
       # for i, image in enumerate(images):
        #    image.save(os.path.join(pkg_dir, f'page{i+1}.jpg'), 'JPEG')
        
        # Generate manifest
        resource_files = '\n'.join([f'<file href="page{i+1}.jpg"/>' for i in range(total_pages)])
        manifest = MANIFEST_TEMPLATE.format(
            uuid=uuid.uuid4().hex,
            resource_files=resource_files
        )
        
         
        # Save images with compression
        for i, image in enumerate(images):
            compressed = compress_image(image, quality=60)
            compressed.save(os.path.join(pkg_dir, f'page{i+1}.jpg'), 'JPEG')
        
            
        
        # Save package files
        with open(os.path.join(pkg_dir, 'imsmanifest.xml'), 'w') as f:
            f.write(manifest)
        
        with open(os.path.join(pkg_dir, 'index.html'), 'w') as f:
            f.write(INDEX_TEMPLATE.format(total_pages=total_pages))
        
        with open(os.path.join(pkg_dir, 'scorm.js'), 'w') as f:
            f.write(SCOORM_JS)
        
        # Create ZIP package
        zip_path = os.path.join(tmp_dir, 'scorm_package.zip')
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for root, _, files in os.walk(pkg_dir):
                for file in files:
                    abs_path = os.path.join(root, file)
                    rel_path = os.path.relpath(abs_path, pkg_dir)
                    zipf.write(abs_path, rel_path)

        # Read ZIP file into memory before temp dir is deleted
        with open(zip_path, 'rb') as f:
            zip_bytes = f.read()
        zip_io = io.BytesIO(zip_bytes)
        zip_io.seek(0)

        return send_file(
            zip_io,
            as_attachment=True,
            download_name='scorm_package.zip',
            mimetype='application/zip'
        )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, debug=True)