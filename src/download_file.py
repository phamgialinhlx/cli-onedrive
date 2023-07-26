import os
import requests
from argparse import ArgumentParser
from util.ms_graph.generate_access_token import generate_access_token
from explorer import explore_file
from dotenv import load_dotenv

load_dotenv()

APP_ID:str = os.getenv('APP_ID')
GRAPH_API_ENDPOINT = os.getenv('GRAPH_API_ENDPOINT')
ROOT_DRIVE_ID = os.getenv('ROOT_DRIVE_ID')
ROOT_ITEM_ID = os.getenv('ROOT_ITEM_ID')
SCOPES = ['User.ReadWrite', 'Files.ReadWrite', 'Files.ReadWrite.All']


def downloadFile(drive_id, item_id, file_name, file_path = './'):
    if file_path[-1] != '/':
        file_path += '/'

    if not os.path.exists(file_path):
        os.makedirs(file_path)

    access_token = generate_access_token(APP_ID, SCOPES)['access_token']
    headers = {
        'Authorization': 'Bearer ' + access_token
    }

    reqs = GRAPH_API_ENDPOINT + '/drives/' + drive_id + '/items/' + item_id + '/content'
    with open(file_path + file_name, 'wb') as _f:
        response = requests.get(reqs, headers=headers)
        _f.write(response.content)

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("--destination_folder", required=True, type=str, default="", help="Destination folder path")
    args = parser.parse_args()

    destinationPath = args.destination_folder

    item_id = ROOT_ITEM_ID
    drive_id = ROOT_DRIVE_ID

    info = explore_file(drive_id, item_id)
    print(info)
    downloadFile(drive_id, info['itemId'], info['itemName'], destinationPath)
