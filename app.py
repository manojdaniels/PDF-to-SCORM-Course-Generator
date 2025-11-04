import os
import io
import uuid
import zipfile
import tempfile
from flask import Flask, request, jsonify, render_template, send_file
from pdf2image import convert_from_path
from PIL import Image
import platform

app = Flask(__name__)

# Directory to store temporary SCORM packages
OUTPUT_DIR = os.path.join(tempfile.gettempdir(), "scorm_packages")
os.makedirs(OUTPUT_DIR, exist_ok=True)


@app.route('/')
def index():
    """Render the web interface."""
    return render_template('index.html')


@app.route('/convert', methods=['POST'])
def convert_pdf_to_scorm():
    """Converts uploaded PDF into SCORM-compliant ZIP package."""
    if 'pdf_file' not in request.files:
        return jsonify({'error': 'No PDF file uploaded'}), 400

    pdf_file = request.files['pdf_file']

    # Generate unique working directory
    session_id = str(uuid.uuid4())
    session_dir = os.path.join(OUTPUT_DIR, session_id)
    os.makedirs(session_dir, exist_ok=True)

    pdf_path = os.path.join(session_dir, pdf_file.filename)
    pdf_file.save(pdf_path)

    summary = []

    try:
        # Convert PDF to images
        summary.append("PDF uploaded successfully")
        images = convert_from_path(pdf_path, dpi=150)
        summary.append(f"Converted {len(images)} pages to images")

        # Save images
        image_dir = os.path.join(session_dir, "images")
        os.makedirs(image_dir, exist_ok=True)

        for i, img in enumerate(images, start=1):
            img_path = os.path.join(image_dir, f"page_{i}.png")
            img.save(img_path, "PNG")

        summary.append("Saved converted pages as PNG images")

        # Create SCORM manifest (basic XML)
        manifest_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<manifest identifier="scorm_{session_id}" version="1.0"
    xmlns="http://www.imsproject.org/xsd/imscp_rootv1p1p2"
    xmlns:adlcp="http://www.adlnet.org/xsd/adlcp_rootv1p2"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.imsproject.org/xsd/imscp_rootv1p1p2 ims_xml.xsd">
    <metadata>
        <schema>ADL SCORM</schema>
        <schemaversion>1.2</schemaversion>
    </metadata>
    <organizations default="org1">
        <organization identifier="org1">
            <title>PDF SCORM Course</title>
            <item identifier="item1" identifierref="resource1">
                <title>Converted PDF Course</title>
            </item>
        </organization>
    </organizations>
    <resources>
        <resource identifier="resource1" type="webcontent" adlcp:scormtype="sco" href="index.html">
            <file href="index.html"/>
        </resource>
    </resources>
</manifest>
"""
        manifest_path = os.path.join(session_dir, "imsmanifest.xml")
        with open(manifest_path, "w", encoding="utf-8") as f:
            f.write(manifest_content)
        summary.append("SCORM manifest generated")

        # Create simple index.html (image viewer)
        index_html = """<html><body><h2>PDF SCORM Course</h2>"""
        for i in range(1, len(images) + 1):
            index_html += f'<img src="images/page_{i}.png" style="width:90%;margin-bottom:20px;"><br>'
        index_html += "</body></html>"

        with open(os.path.join(session_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(index_html)
        summary.append("HTML content created")

        # Create SCORM ZIP
        zip_filename = f"scorm_package_{session_id}.zip"
        zip_path = os.path.join(OUTPUT_DIR, zip_filename)
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(session_dir):
                for file in files:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, session_dir)
                    zipf.write(full_path, rel_path)
        summary.append("SCORM package created successfully")

        # Prepare download URL
        download_url = f"/download/{zip_filename}"

        return jsonify({
            "summary": summary,
            "download_url": download_url
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/download/<filename>')
def download_file(filename):
    """Serve generated SCORM package for download."""
    file_path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404
    return send_file(file_path, as_attachment=True, download_name=filename)


if __name__ == "__main__":
    # Detect environment
    print(f"Running on: {platform.system()} ({platform.release()})")
    app.run(debug=True, host="0.0.0.0", port=5000)
