import requests
import json
from pathlib import Path
import time
import hashlib
import zipfile
import os

token = "eyJ0eXBlIjoiSldUIiwiYWxnIjoiSFM1MTIifQ.eyJqdGkiOiI0MzgwMDk0MSIsInJvbCI6IlJPTEVfUkVHSVNURVIiLCJpc3MiOiJPcGVuWExhYiIsImlhdCI6MTc3MDEzODA1MCwiY2xpZW50SWQiOiJsa3pkeDU3bnZ5MjJqa3BxOXgydyIsInBob25lIjoiIiwib3BlbklkIjpudWxsLCJ1dWlkIjoiY2YzMTVkMTItZTMxYy00NjVhLTg4NGEtNDc3N2I0Y2YxM2U2IiwiZW1haWwiOiJ6aG91eXUyMDA3MTAyOEBnbWFpbC5jb20iLCJleHAiOjE3NzEzNDc2NTB9.hffQknx8rGIa3exaSxXyipZclVmBwb2_zOqAzB0AScL_XLbAs7YhnY-PKMPWKODrQX2HGkA4wd8MyDnbGfkV9g"
header = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {token}"
}
pdf_url = Path('./materials/processed/')

def construct_pdf_data(pdf_url: Path = pdf_url) :
    hash_file = pdf_url / 'cache.json'
    
    try:
        with open(hash_file, 'r', encoding='utf-8') as f:
            processed_files = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        processed_files = {}

    files_to_process = []
    current_files = {}

    for pdf_file in pdf_url.glob("*.pdf"):
        with open(pdf_file, 'rb') as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()
        
        current_files[pdf_file.name] = file_hash
        
        if pdf_file.name not in processed_files or processed_files[pdf_file.name] != file_hash:
            files_to_process.append(pdf_file)


    if not files_to_process:
        print("No new or modified PDF files to process.")
        return [], {}
    
    file_path = []
    data = {
        "files": [],
        "model_version":"vlm"
    }
    for pdf_file in files_to_process:
        with open(pdf_file, 'rb') as f:
            data_id = hashlib.sha256(f.read()).hexdigest()
        file_info = {"name":pdf_file.name, "data_id": data_id}
        data["files"].append(file_info)
        file_path.append(pdf_file)
    return file_path, data

def upload_pdfs(file_path, data):
    url = "https://mineru.net/api/v4/file-urls/batch"
    if not file_path:
        print("No files to upload.")
        return None
    try:
        response = requests.post(url,headers=header,json=data)
        if response.status_code == 200:
            result = response.json()
            print('response success. result:{}'.format(result))
            if result["code"] == 0:
                batch_id = result["data"]["batch_id"]
                urls = result["data"]["file_urls"]
                print('batch_id:{},urls:{}'.format(batch_id, urls))
                for i in range(0, len(urls)):
                    with open(file_path[i], 'rb') as f:
                        res_upload = requests.put(urls[i], data=f)
                        if res_upload.status_code == 200:
                            print(f"{urls[i]} upload success")
                        else:
                            print(f"{urls[i]} upload failed")
            else:
                print('apply upload url failed,reason:{}'.format(result.msg))
        else:
            print('response not success. status:{} ,result:{}'.format(response.status_code, response))
    except Exception as err:
        print(err)
    return batch_id
    
def get_resolve_result(batch_id: str):
    url = f"https://mineru.net/api/v4/extract-results/batch/{batch_id}"
    while True:    
        try:
            res = requests.get(url, headers=header)
            if res.status_code == 200:
                result = res.json()
                if result.get("code") == 0:
                    extract_results = result.get("data", {}).get("extract_result", [])
                    if not extract_results:
                        print("No extract results found.")
                        break
                    
                    all_done = all(file.get("state") == "done" for file in extract_results)
                    
                    if all_done:
                        print("All files processed successfully.")
                        return result
                    else:
                        print("Processing not complete, waiting...")
                        # Optional: print status of each file
                        for file in extract_results:
                            print(f"File: {file.get('file_name')}, Status: {file.get('state')}")
                        time.sleep(5) # Wait for 5 seconds before polling again
                else:
                    print(f"API error: {result.get('msg')}")
                    break
            else:
                print(f"HTTP error: {res.status_code}")
                break
        except Exception as err:
            print(err)
            return


def download_results(result, download_dir: Path = Path('./materials/processed/ocr/'), pdf_url: Path = pdf_url):
    download_dir.mkdir(parents=True, exist_ok=True)
    extract_results = result.get("data", {}).get("extract_result", [])
    
    hash_file = pdf_url / 'cache.json'
    try:
        with open(hash_file, 'r', encoding='utf-8') as f:
            processed_files = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        processed_files = {}
    
    for file in extract_results:
        file_name = file.get("file_name")
        download_url = file.get("full_zip_url")
        if download_url:
            try:
                res = requests.get(download_url)
                if res.status_code == 200:
                    with open(download_dir / (file_name + '.zip'), 'wb') as f:
                        f.write(res.content)
                    print(f"Downloaded {file_name} successfully.")
                    
                    zip_path = download_dir / (file_name + '.zip')
                    try:
                        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                            zip_ref.extractall(download_dir / file_name)
                        print(f"Unzipped {file_name}.zip successfully.")
                        os.remove(zip_path)
                        
                        with open(pdf_url / file_name, 'rb') as f:
                            file_hash = hashlib.sha256(f.read()).hexdigest()
                        processed_files[Path(file_name).name] = file_hash
                        
                    except zipfile.BadZipFile:
                        print(f"Error: The file {zip_path} is not a valid zip file.")
                    except Exception as e:
                        print(f"An error occurred while unzipping {zip_path}: {e}")
                else:
                    print(f"Failed to download {file_name}, HTTP status: {res.status_code}")
            except Exception as err:
                print(f"Error downloading {file_name}: {err}")
        else:
            print(f"No download URL for {file_name}")

    with open(hash_file, 'w', encoding='utf-8') as f:
        json.dump(processed_files, f, ensure_ascii=False, indent=4)

def main():
    file_path, data = construct_pdf_data()
    batch_id = upload_pdfs(file_path, data)
    if batch_id:
        result = get_resolve_result(batch_id)
        if result:
            download_results(result)

if __name__ == "__main__":
    main()