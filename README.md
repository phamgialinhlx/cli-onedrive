### Upload folder to OneDrive
```bash
python src/upload_folder.py --input_folder <path_to_folder>
```

`path_to_folder`: exact path to folder that you want to upload


### Download file from OneDrive
```bash
python src/download_file.py --destination_folder <path_to_destination_folder>
```
`path_to_destination_folder`: exact path to folder that you want to download to

***Note***: 
- Go to https://portal.azure.com/ to create an app and get the `APP_ID`.
- Go to https://developer.microsoft.com/en-us/graph/graph-explorer to get the `ROOT_DRIVE_ID` and `ROOT_ITEM_ID`.
- Remember to create `.env` file and fill in the information as in the [.env.example](./.env.example) file