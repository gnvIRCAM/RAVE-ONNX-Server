import * as FileSystem from 'expo-file-system';
import { Asset, useAssets } from 'expo-asset';


// Download file to document directory
const downloadFile = async () => {
    // Create a directory in the app document directory
    let directory = FileSystem.documentDirectory + "my_directory"
    await FileSystem.makeDirectoryAsync(directory);

    // Download file
    const { uri } = await FileSystem.downloadAsync(serverAdress + "/download", directory + "/hey.wav")
}

// Get the asset file local uri 
const [assets, error] = useAssets([require('../assets/audio.wav')]);

// Send file function
const sendFile = async () => {
    let fileUri = assets[0].localUri // The uri of the file you want to upload
    resp = await FileSystem.uploadAsync(serverAdress + "/upload", fileUri, {
        fieldName: 'file',
        httpMethod: 'POST',
        uploadType: FileSystem.FileSystemUploadType.MULTIPART,
        headers: { filename: fileUri }
    })
    console.log(resp.body)
}

