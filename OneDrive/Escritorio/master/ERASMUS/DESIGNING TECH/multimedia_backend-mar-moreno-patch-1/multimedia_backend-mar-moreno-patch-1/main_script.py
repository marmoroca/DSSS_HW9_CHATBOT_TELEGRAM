from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse
import os
import requests

app = FastAPI()

# Directories
IMAGE_DIR = "uploaded_images"
DOC_DIR = "uploaded_docs"

# Create directories
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(DOC_DIR, exist_ok=True)


@app.post("/upload")
async def upload_files(files: list[UploadFile] = File(...)):
    saved_files = []

    for file in files:
        # Obtain file extension
        file_extension = file.filename.split('.')[-1].lower()

    # Determine if img or docs
    if file_extension in ["jpg", "jpeg", "png", "gif"]:
        file_path = os.path.join(IMAGE_DIR, file.filename)
    elif file_extension in ["txt", "pdf", "doc", "docx"]:
        file_path = os.path.join(DOC_DIR, file.filename)
    else:
        return {"error": "Unsupported file type"}
    
    # Guardar el archivo en la ruta correspondiente
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    saved_files.append(file.filename)

    return {"saved_files": saved_files}


@app.get("/gallery", response_class=HTMLResponse)
async def get_gallery():
    # List images
    image_files = os.listdir(IMAGE_DIR)
    image_elements = [f'<img src="/{IMAGE_DIR}/{file}" alt="{file}" width="200">' for file in image_files]

    # List docs
    doc_files = os.listdir(DOC_DIR)
    doc_elements = [f'<a href="/{DOC_DIR}/{file}" download>{file}</a>' for file in doc_files]

    # Build HTML
    content = "<h1>Gallery</h1>"
    content += "<h2>Images</h2>" + "".join(image_elements) if image_elements else "<p>No images uploaded.</p>"
    content += "<h2>Documents</h2>" + "".join(doc_elements) if doc_elements else "<p>No documents uploaded.</p>"
    
    return content


# Serve static files
from fastapi.staticfiles import StaticFiles

app.mount(f"/{IMAGE_DIR}", StaticFiles(directory=IMAGE_DIR), name="images")
app.mount(f"/{DOC_DIR}", StaticFiles(directory=DOC_DIR), name="documents")






# Upload endpoint URL
UPLOAD_URL = "http://127.0.0.1:8000/upload"

# Directory containing images
IMAGE_DIR = "images"

def upload_images_from_folder(folder_path: str, upload_url: str):
    """
    Uploads all files from a specified folder to the given upload endpoint.

    Args:
        folder_path (str): Path to the folder containing the files to upload.
        upload_url (str): URL of the upload endpoint.

    Returns:
        dict: Server response as a dictionary.
    """
    files = []
    try:
        # Iterate over all files in the folder
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):  # Ensure it's a file, not a directory
                files.append(("files", open(file_path, "rb")))

        # Send POST request with files
        response = requests.post(upload_url, files=files)

        # Close all opened files after the request
        for _, file in files:
            file.close()

        return response.json()

    except Exception as e:
        # Handle any exception and return the error message
        return {"error": str(e)}

if __name__ == "__main__":
    # Notify user about the upload process
    print("Uploading files from folder:", IMAGE_DIR)
    # Call the function to upload files
    response = upload_images_from_folder(IMAGE_DIR, UPLOAD_URL)
    # Print server response
    print("Server response:", response)
