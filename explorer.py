from argparse import ArgumentParser
import os
import json
from tqdm import tqdm
import requests
from dotenv import load_dotenv
from util.ms_graph.generate_access_token import generate_access_token
from util.helper import retry_with_exponential_backoff, clear_terminal

load_dotenv()

APP_ID:str = os.getenv('APP_ID')
GRAPH_API_ENDPOINT = os.getenv('GRAPH_API_ENDPOINT')
SCOPES = ['User.ReadWrite', 'Files.ReadWrite', 'Files.ReadWrite.All']

stack_explore = []

def explore(driveId, itemId, oldItemId=None):
    access_token = generate_access_token(APP_ID, SCOPES)['access_token']
    headers = {
        'Authorization': 'Bearer ' + access_token
    }
    response_upload_session = requests.get(
        GRAPH_API_ENDPOINT + f'/drives/{driveId}/items/{itemId}/children', 
        # GRAPH_API_ENDPOINT + f'/drives/{drive_id}/items/{folder_upload_id}/createUploadSession',  # lỗi ko thể tạo session on a folder
        headers=headers,
    )
    value = response_upload_session.json()['value']
    # print('value', value)
    itemlist = [{
        'name': '.',
        'id': itemId,
    }]
    if oldItemId is not None:
        itemlist.append({
            'name': '..',
            'id': oldItemId,
        })
    
    for x in value:
        if 'folder' in x:
            itemlist.append({
                'name': x['name'],
                'id': x['id']
            })
    
    for i, x in enumerate(itemlist):
        print(i + 1, '|', x['id'], '|', x['name'])

    choice = int(input('Enter the folder index: '))
    folder_id = itemlist[choice - 1]['id']
    choose = input('Do you want to choose this folder to process (upload)? (y/n): ')
    if choose == 'y':
        clear_terminal()
        return folder_id
    else:
        clear_terminal()
        return explore(driveId, folder_id, itemId)


if __name__ == '__main__':
    info = json.load(open('important_id.json', 'r'))
    driveId = info['ROOT']['drive_id']
    itemId = info['ROOT']['id']
    explore(driveId, itemId)
    