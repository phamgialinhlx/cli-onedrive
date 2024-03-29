from argparse import ArgumentParser
import os
import json
from tqdm import tqdm
import requests
from dotenv import load_dotenv
from util.ms_graph.generate_access_token import generate_access_token
from util.helper import retry_with_exponential_backoff
from explorer import explore_folder

load_dotenv()

APP_ID:str = os.getenv('APP_ID')
GRAPH_API_ENDPOINT = os.getenv('GRAPH_API_ENDPOINT')
ROOT_DRIVE_ID = os.getenv('ROOT_DRIVE_ID')
ROOT_ITEM_ID = os.getenv('ROOT_ITEM_ID')
SCOPES = ['User.ReadWrite', 'Files.ReadWrite', 'Files.ReadWrite.All']

def get_folder_info(folder_path:str):
    results = []
    for root, dirs, files in os.walk(folder_path):

        results.append({
            'root': root,
            'dirs': dirs,
            'files': files
        })
    return results

def list_dir(path:str):
    results = {
        'dirs': [],
        'files': []
    }
    osld = os.listdir(path)
    for x in osld:
        if os.path.isdir(os.path.join(path, x)):
            results['dirs'].append(x)
        else:
            results['files'].append(x)
    return results

@retry_with_exponential_backoff
def upload_file(bn_bar, folder_upload_id, drive_id, file_name, folder_path):
    bn_bar.set_description(f'Upload {file_name}')
    access_token = generate_access_token(APP_ID, SCOPES)['access_token']
    headers = {
        'Authorization': 'Bearer ' + access_token
    }
    response_upload_session = requests.post(
        GRAPH_API_ENDPOINT + f'/drives/{drive_id}/items/{folder_upload_id}:/{file_name}:/createUploadSession', 
        # GRAPH_API_ENDPOINT + f'/drives/{drive_id}/items/{folder_upload_id}/createUploadSession',  # lỗi ko thể tạo session on a folder
        headers=headers,
    )
    # print('response_upload_session', response_upload_session.json())
    upload_url = response_upload_session.json()['uploadUrl']

    # Upload file with chunksize
    file_path = os.path.join(folder_path, file_name)
    with open(file_path, 'rb') as f:
        total_file_size = os.path.getsize(file_path)
        chunk_size = 3276800
        chunk_number = total_file_size//chunk_size
        chunk_left_over = total_file_size - chunk_number*chunk_size
        counter =0

        upload_bar = tqdm(total=chunk_number, unit='chunk')
        while True:
            chunk_data = f.read(chunk_size) # type bytes
            start_index = counter*chunk_size
            end_index = start_index + chunk_size

            if not chunk_data:
                break
            if counter == chunk_number:
                end_index = start_index + chunk_left_over

            header_add = {
                "Content-Length": f'{chunk_size}',
                "Content-Range": f'bytes {start_index}-{end_index-1}/{total_file_size}'
            }                    
            chunk_data_upload_status = requests.put(upload_url, 
                headers=header_add, 
                data=chunk_data
            )
            # print('response_upload_status', chunk_data_upload_status)
            # print('Upload Progess: ', chunk_data_upload_status.json().get('nextExpectedRanges'))
            counter+=1
            upload_bar.update(1)
            desc = str(chunk_data_upload_status.json().get('nextExpectedRanges'))
            upload_bar.set_description(f'Range chunk: {desc}')
    # except Exception as e:
    #     print(e)
    #     print('error', bn_id)
    bn_bar.update(1)
    requests.delete(upload_url)

@retry_with_exponential_backoff
def create_folder(name, drive_id, item_id):
    access_token = generate_access_token(APP_ID, SCOPES)['access_token']
    headers = {
        'Authorization': 'Bearer ' + access_token
    }
    data_post = {
        "name": name, 
        "folder": {},
        # "@microsoft.graph.conflictBehavior": "rename" # rename if duplicate
    }
    # create folder (bn_id) in onedrive
    response = requests.post(
        GRAPH_API_ENDPOINT + f'/drives/{drive_id}/items/{item_id}/children', 
        headers=headers,
        json=data_post
    )
    response = response.json()
    if response.get('error'):
        if response.get('error').get('code') == 'nameAlreadyExists':
            link = GRAPH_API_ENDPOINT + f'/drives/{drive_id}/items/{item_id}/children'
            while True:
                response = requests.get(
                    link, 
                    headers=headers, 
                )
                response = response.json()
                for item in response['value']:
                    if item['name'] == name:
                        folder_bn_id_created = item['name']
                        folder_created_id = item['id']
                if '@odata.nextLink' not in response.keys():
                    break
                else:
                    link = response['@odata.nextLink']
                    continue
        else:
            print(response)
            raise Exception(response)
    else:
        folder_bn_id_created = response['name']
        folder_created_id = response['id']
    return folder_bn_id_created, folder_created_id

@retry_with_exponential_backoff
def upload_folder(folder_path, bn_bar, drive_id, item_id, overwrite):

    # for root, dirs, files in os.walk(folder_path):
    folder_info = list_dir(folder_path)
    dirs = folder_info['dirs']
    files = folder_info['files']
    
    access_token = generate_access_token(APP_ID, SCOPES)['access_token']
    headers = {
        'Authorization': 'Bearer ' + access_token
    }
    
    response_existing_file = requests.get(
        GRAPH_API_ENDPOINT + f'/drives/{drive_id}/items/{item_id}/children', 
        headers=headers,
    )
    
    response_existing_file = response_existing_file.json()
    existing_files = []
    for item in response_existing_file['value']:
        if 'file' in item.keys():
            existing_files.append(item['name'])
            
    for file in files:
        if overwrite:
            if file not in existing_files:
                upload_file(bn_bar, item_id, drive_id, file, folder_path)
            else:
                print(f'{file} already exists')
        else:
            upload_file(bn_bar, item_id, drive_id, file, folder_path)

    for dir in dirs:
        folder_bn_id_created, folder_created_id = create_folder(dir, drive_id, item_id)
        upload_folder(os.path.join(folder_path, dir), bn_bar, drive_id, folder_created_id, overwrite)

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("--input_folder", required=True, type=str, default="", help="Input folder path")
    parser.add_argument('--overwrite', action="store_true", help='Whether to overwrite existing files')
    args = parser.parse_args()

    FOLDER_PATH = args.input_folder
    if FOLDER_PATH[-1] == "/":
        FOLDER_PATH = FOLDER_PATH[:-1]
    folder_name = os.path.basename(FOLDER_PATH)
    folder_info = get_folder_info(FOLDER_PATH)

    item_id = ROOT_ITEM_ID
    drive_id = ROOT_DRIVE_ID
    item_id = explore_folder(drive_id, item_id)
    
    new_folder, new_folder_id = create_folder(folder_name, drive_id, item_id)
    bn_bar = tqdm(total=len(folder_info), unit='BN', desc='Upload BN')
    upload_folder(FOLDER_PATH, bn_bar, drive_id, new_folder_id, args.overwrite)
