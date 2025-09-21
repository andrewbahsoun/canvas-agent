import requests
import io
from scraper import pdf_to_text
from scraper import pptx_to_text
from scraper import docx_to_text
from pathlib import Path
import time

def slug(s: str) -> str:
    import re as _re
    return _re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")



def load_classes(access_token):
    BASE_URL = "https://canvas.chapman.edu/api/v1"
    ACCESS_TOKEN = access_token 
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    course_names = {
        "status": "success",
        "courses": [
        ],
        "timestamp": int(time.time())
    } 
    resp = requests.get(f"{BASE_URL}/courses", headers=headers, params={"enrollment_state": "active"})
    COURSE_JSON = resp.json()
    for course in COURSE_JSON:
        course_name = course['name']
        course_names["courses"].append({"name": course_name})
    print(course_names["courses"])
    return course_names

def scrape_canvas(access_token):
    BASE_URL = "https://canvas.chapman.edu/api/v1"
    ACCESS_TOKEN = access_token 

    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    courseNames = {
        "status": "success",
        "courses": [
        ],
        "timestamp": int(time.time())
    } 

    def fetch_file_bytes(file_url: str) -> io.BytesIO:
        # Try auth header first
        resp = requests.get(file_url, headers=headers, stream=True)
        if resp.status_code in (401, 403):
            # Some Canvas file links don’t honor headers, need access_token query
            sep = "&" if "?" in file_url else "?"
            resp = requests.get(f"{file_url}{sep}access_token={ACCESS_TOKEN}", stream=True)
        resp.raise_for_status()
        buf = io.BytesIO()
        for chunk in resp.iter_content(chunk_size=1024*1024):
            if chunk:
                buf.write(chunk)
        buf.seek(0)
        return buf


    def scrape_canvas_to_txts():
        resp = requests.get(f"{BASE_URL}/courses", headers=headers, params={"enrollment_state": "active"})
        COURSE_JSON = resp.json()
        ids = []
        file_infos = []
        file_infos_for_db = [] 
        course_names = []
        base = Path.cwd()
        try:
            path = base / "data"
            path.mkdir(parents=True, exist_ok=False)
            print(f"Created folder: {path}")
        except FileExistsError:
            print(f"Folder already exists: {path}")

        base = base / "data"
        for course in COURSE_JSON:
            course_name = course['name']
            course_id = course["id"]
            course_name = slug(course_name)
            if course_name not in course_names:
                course_names.append(course_name)
                print(course_names)
                courseNames["courses"].append({"name": course_name})
                path = base / course_name
                try:
                    path.mkdir(parents=True, exist_ok=False)
                    print(f"Created folder: {path}")
                except FileExistsError:
                    print(f"Folder already exists: {path}")
            resp = requests.get(f"{BASE_URL}/courses/{course_id}/modules", headers=headers)
            MODULE_JSON = resp.json()
            for module in MODULE_JSON: 
                module_name = module["name"]
                module_id = module["id"]
                resp = requests.get(f"{BASE_URL}/courses/{course_id}/modules/{module_id}/items", headers=headers)
                ITEM_JSON = resp.json()
                for item in ITEM_JSON:
                    if item["type"] == "File": #only want to look at items that have the file type 
                        url = item["url"]
                        file_info = {"file_name": slug(item["title"]), "date_created": None, "course": course_name, "module": module_name, "item_file_url": item["url"], "file_download_url": None}
                        file_infos.append(file_info)
                        resp = requests.get(file_info["item_file_url"], headers=headers)
                        FILE_JSON = resp.json()
                        file_info["date_created"] = FILE_JSON["created_at"]


                        if "pdf" in FILE_JSON["content-type"].lower():
                            file_info["file_download_url"] = FILE_JSON["url"]
                            buf = fetch_file_bytes(file_info["file_download_url"])
                            out_path = pdf_to_text.save_pdf_bytes_as_txt(buf, file_info["file_name"] + ".txt", output_dir=base/course_name)
                            if out_path is not None:
                                file_info_for_db = {"name": file_info["file_name"] +".txt", "date": file_info["date_created"], "course": file_info["course"], "module": file_info["module"], "path": f"{base}/{course_name}/{file_info['file_name']}.txt"}
                                file_infos_for_db.append(file_info_for_db)
                            

                        elif "application/vnd.openxmlformats-officedocument.presentationml.presentation" in FILE_JSON["content-type"]:
                            file_info["file_download_url"] = FILE_JSON["url"]
                            buf = fetch_file_bytes(file_info["file_download_url"])
                            out_path = pptx_to_text.save_pptx_bytes_as_txt(buf, file_info["file_name"] + ".txt", output_dir=base/course_name)
                            if out_path is not None:
                                file_info_for_db = {"name": file_info["file_name"] +".txt", "date": file_info["date_created"], "course": file_info["course"], "module": file_info["module"], "path": f"{base}/{course_name}/{file_info['file_name']}.txt"}
                                file_infos_for_db.append(file_info_for_db)

                        elif "application/vnd.openxmlformats-officedocument.wordprocessingml.document" in FILE_JSON["content-type"]:
                            file_info["file_download_url"] = FILE_JSON["url"]
                            buf = fetch_file_bytes(file_info["file_download_url"])
                            out_path = docx_to_text.save_docx_bytes_as_txt(buf, file_info["file_name"] + ".txt", output_dir=base/course_name)
                            if out_path is not None:
                                file_info_for_db = {"name": file_info["file_name"] +".txt", "date": file_info["date_created"], "course": file_info["course"], "module": file_info["module"], "path": f"{base}/{course_name}/{file_info['file_name']}.txt"}
                                file_infos_for_db.append(file_info_for_db)
                        else:
                            print("couldn't open file")

                    else:
                        print("not a file")
        
        out_path = Path.cwd() / "file_infos.txt"

        with out_path.open("w", encoding="utf-8") as f:
            for file_info in file_infos_for_db:
                f.write(f"{file_info}\n")
    scrape_canvas_to_txts()
    return courseNames
  # Return in test_courses format
  