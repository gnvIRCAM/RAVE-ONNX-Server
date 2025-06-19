from flask import Flask, request, send_file, session

import os
from flask_cors import CORS
import onnxruntime as rt
import librosa
import numpy as np
import soundfile as sf

app = Flask(__name__)
app.secret_key = "super secret key"

# Global variables (credits to Jacques Zhuang)
MODELS_LIST = []
CURRENT_MODEL = None

# Original:
# CORS(app, expose_headers='Authorization')
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True, expose_headers='Authorization')
model_path = "./models"


# Routine executée avant la premiere requete qui permet de lire la liste des modèles
def init():
    global MODELS_LIST, CURRENT_MODEL
    MODELS_LIST = os.listdir("./models")
    # print(models_list)
    if CURRENT_MODEL is None:
        CURRENT_MODEL = MODELS_LIST[0 ]

# Réponse à une requete vide
@app.route("/")
def main():
	return "Connection success !"


# Upload un fichier et conversion de l'audio avec le modèle
@app.route("/upload", methods=['POST'])
def upload():
    global MODELS_LIST, CURRENT_MODEL
    init()
    try:
        print('Files:', request.files)
        if 'file' not in request.files:
            return 'No file part'
        file = request.files['file']
        if file.filename == '':
            return 'No selected file'
        extension = file.filename.rsplit('.', 1)[-1]
        fpath = "./received_audio." + extension
        file.save(fpath)
        if not os.path.exists(fpath):
            return 'File not saved correctly'
        audio, sr = librosa.load(fpath, sr=44100)
        if audio is None or sr is None:
            return 'Error loading audio file'
        audio = np.expand_dims(audio, (0, 1))
        sess = rt.InferenceSession(os.path.join(model_path,
                                                CURRENT_MODEL),
                                   providers=rt.get_available_providers())
        res = sess.run([sess.get_outputs()[0].name], {"audio_in": audio})
        if res is None:
            return 'Error during inference'
        sf.write('transformed_audio.wav', res[0].squeeze(), 44100)
        return "Computation done - ready to download "
    except Exception as e:
        print(str(e))
        return "Error during computation " + str(e)


# Telechargement du fichier transformé par le modèle
@app.route("/download", methods=['GET'])
def download():
	print("sending file")
	path = "transformed_audio.wav"
	return send_file(path, as_attachment=True)


# Récupérer les modèles disponibles
@app.route('/getmodels')
def getModels():
    global MODELS_LIST
    init()
    return {"models": MODELS_LIST}


# Selection du modèle à utiliser
@app.route("/selectModel/<modelName>")
def setModel(modelName):
    global MODELS_LIST, CURRENT_MODEL
    if not len(MODELS_LIST):
        init()
    if modelName not in MODELS_LIST:
        return "model not found ! "
    else:
        if modelName[-5:] != ".onnx":
            modelName += ".onnx"
        CURRENT_MODEL = modelName
        print(f'Selected model : {modelName}')
        return f"model selected - {modelName}"


if __name__ == '__main__':
	app.run(debug=True, port=8000, host="0.0.0.0")