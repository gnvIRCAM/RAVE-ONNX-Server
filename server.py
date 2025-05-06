from flask import Flask, request, send_file, session

import os
from flask_cors import CORS
import onnxruntime as rt
import librosa
import numpy as np
import soundfile as sf

app = Flask(__name__)
app.secret_key = "super secret key"

# Original:
# CORS(app, expose_headers='Authorization')
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True, expose_headers='Authorization')
model_path = "./models"


# Routine executée avant la premiere requete qui permet de lire la liste des modèles
def init():
    with app.app_context():
        models_list = os.listdir("./models")
        print(models_list)
        session["models"] = models_list
        session["currentModel"] = models_list[0]


# Réponse à une requete vide
@app.route("/")
def main():
	return "Connection success !"


# Upload un fichier et conversion de l'audio avec le modèle
@app.route("/upload", methods=['POST'])
def upload():
    # FIXME: L'initialisation ne fonctionne pas lorsque la requête est effectuée avec fetch
    # On doit donc l'appeler manuellement
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
                                                session["currentModel"]),
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
    init()
    # Ensure 'models' key exists in session, set default if not
    if 'models' not in session:
        session['models'] = []  # Assuming default value is an empty list, adjust as needed
    models = {"models": session["models"]}
    return models


# Selection du modèle à utiliser
@app.route("/selectModel/<modelName>")
def setModel(modelName):
	init()
	if modelName not in session["models"]:
		return "model not found ! "
	else:
		if modelName[-5:] != ".onnx":
			modelName += ".onnx"
		session["currentModel"] = modelName
		print(f'Selected model : {modelName}')
		return f"model selected - {modelName}"


if __name__ == '__main__':
	app.run(debug=True, port=8000, host="0.0.0.0")