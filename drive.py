from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.service_account import Credentials
import os

# Escopo para acessar o Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive.file']


def authenticate_google_drive():
    """
    Autentica o usuário com o Google Drive usando uma conta de serviço.
    Retorna o serviço do Google Drive para operações de API.


    O credentials file pode ser obtido criando uma Service Account em IAM & Admin, no Google Console.
    """
    credentials = Credentials.from_service_account_file(
        'credentials.json', scopes=SCOPES
    )
    return build('drive', 'v3', credentials=credentials)


def upload_to_drive(service, file_path, folder_id=None):
    """
    Faz upload de um arquivo genérico para o Google Drive.

    Args:
        service: Serviço autenticado do Google Drive.
        file_path (str): Caminho do arquivo a ser enviado.
        folder_id (str, opcional): ID da pasta onde o arquivo será enviado. Default é None.

    Returns:
        dict: Informações do arquivo enviado, incluindo ID e nome.
    """
    file_name = os.path.basename(file_path)

    # Configura os metadados do arquivo
    file_metadata = {'name': file_name}
    if folder_id:
        file_metadata['parents'] = [folder_id]

    # Prepara o arquivo para upload
    media = MediaFileUpload(file_path, resumable=True)

    # Faz o upload
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, name'
    ).execute()

    return file


if __name__ == "__main__":
    # Exemplo de uso
    drive_service = authenticate_google_drive()

    # Substitua pelo caminho do arquivo que deseja enviar (deve estar no mesmo folder de execução do script)
    file_to_upload = "example.txt"

    # Substitua pelo ID da pasta no Google Drive (ou deixe como None para enviar na raiz)
    # O folder_id pode ser encontrado clicando no Drive em Compartilhar Link
    # Ex. do meu: https://drive.google.com/drive/folders/1oDw-8sjy3CnIE4bEKe52lyBpWV8UcXGz?usp=drive_link
    folder_id = None
    folder_id = "1IPQxziNsEvVjUBH_ZxmT4S9YMMolFmJO"

    uploaded_file = upload_to_drive(drive_service, file_to_upload, folder_id)
    print(f"Arquivo enviado com sucesso! ID: {uploaded_file['id']}, Nome: {uploaded_file['name']}")

