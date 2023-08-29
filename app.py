import os
from flask import Flask, render_template, request, send_from_directory
from werkzeug.utils import secure_filename
from manipulador_imagem import *
import zipfile
from flask_wtf.csrf import CSRFProtect
import os

app = Flask(__name__)

# Chave secreta estática como exemplo.
# Para produção, use uma chave secreta segura e armazene-a de forma segura.
SECRET_KEY = os.environ.get('SECRET_KEY')

app.config['SECRET_KEY'] = SECRET_KEY

csrf = CSRFProtect(app)

app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
# app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Certifique-se de que a pasta de uploads existe
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def process_file(file, font_size, font_color):
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    # Salvando o arquivo
    file.save(filepath)

    metadados = extrair_metadados(filepath)
    if any(metadados):
        imagem_com_metadados = desenhar_metadados_na_imagem(filepath, metadados, font_size, font_color, "Topo Esquerdo")
        imagem_com_metadados.save(filepath, "JPEG", quality=95)
        return filepath, True
    else:
        return filepath, False


@app.route('/', methods=['GET', 'POST'])
def index():
    zip_filename = None
    arquivos_sem_metadados = []

    if request.method == 'POST':
        font_size = int(request.form.get('font_size', 24))
        font_color = request.form.get('font_color', 'black')

        uploaded_files = request.files.getlist('file')
        processed_files = []
        all_uploaded_files = []  # Esta lista armazenará todos os arquivos carregados

        for file in uploaded_files:
            if allowed_file(file.filename):
                result, is_processed = process_file(file, font_size, font_color)
                all_uploaded_files.append(result)  # Adicione todos os resultados aqui
                if is_processed:
                    processed_files.append(result)
                else:
                    arquivos_sem_metadados.append(result)

        if processed_files:
            zip_filename = 'processed_images.zip'
            with zipfile.ZipFile(os.path.join(app.config['UPLOAD_FOLDER'], zip_filename), 'w') as zipf:
                for file in processed_files:
                    if os.path.exists(file):
                        zipf.write(file, os.path.basename(file))

            # Aqui, removemos todos os arquivos após o processamento, independentemente de terem metadados ou não.
            for file in all_uploaded_files:
                print(f"Tentando excluir o arquivo: {file}")
                try:
                    if os.path.exists(file):
                        os.remove(file)
                        if os.path.exists(file):
                            print(f"Falha ao excluir o arquivo {file}. Ele ainda existe.")
                        else:
                            print(f"Arquivo {file} excluído com sucesso.")
                    else:
                        print(f"O arquivo {file} não existe.")
                except Exception as e:
                    print(f"Erro ao excluir o arquivo {file}: {e}")

    return render_template('index.html', zip_filename=zip_filename, arquivos_sem_metadados=arquivos_sem_metadados)



@app.route('/uploads/<zip_filename>')
def download_zip(zip_filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], zip_filename, as_attachment=True)


@app.route('/download', methods=['GET'])
def download():
    return send_from_directory(directory='uploads', path='processed_images.zip', as_attachment=True)


if __name__ == '__main__':
    app.run(debug=False)