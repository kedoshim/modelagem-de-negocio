from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.service_account import Credentials
import os
import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime, timedelta
from prefect import task, flow
from prefect.artifacts import (
    create_link_artifact,
    create_image_artifact,
    create_table_artifact,
)
from prefect.variables import Variable
from prefect.logging import get_run_logger

# Escopo para acessar o Google Drive
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

# Carrega lista de tickers de um bloco Prefect
TICKER_VARIABLE = Variable.get("tickers")
TICKERS = (
    TICKER_VARIABLE if TICKER_VARIABLE else ["PETR4.SA", "VALE3.SA"]
)  # Default caso não haja bloco configurado


credentials_block = Variable.get("drive_credentials")

def authenticate_google_drive():
    """
    Autentica o acesso ao Google Drive usando uma conta de serviço.
    Retorna o serviço do Google Drive para operações de API.
    """
    logger = get_run_logger()

    # getting from a synchronous context
    answer = Variable.get('the_answer')
    logger.debug(answer)

    credentials_block = Variable.get("drive_credentials")
    
    if not credentials_block:
        raise ValueError(f"Bloco de credenciais do Google Drive não configurado.")

    credentials = Credentials.from_service_account_info(
        credentials_block, scopes=SCOPES
    )
    return build("drive", "v3", credentials=credentials)


def upload_to_drive(service, file_path, folder_id=None):
    """
    Faz upload de um arquivo genérico para o Google Drive.

    Args:
        service: Serviço autenticado do Google Drive.
        file_path (str): Caminho do arquivo a ser enviado.
        folder_id (str, opcional): ID da pasta onde o arquivo será enviado.

    Returns:
        str: Link público do arquivo enviado.
    """
    file_name = os.path.basename(file_path)

    # Configura os metadados do arquivo
    file_metadata = {"name": file_name}
    if folder_id:
        file_metadata["parents"] = [folder_id]

    media = MediaFileUpload(file_path, resumable=True)

    # Faz o upload
    file = (
        service.files()
        .create(body=file_metadata, media_body=media, fields="id, webViewLink")
        .execute()
    )

    return file.get("webViewLink")


@task(log_prints=True, retries=3, retry_delay_seconds=10)
def download_stock_data(tickers):
    end_date = datetime.today()
    start_date = end_date - timedelta(days=7)
    data = {}
    for ticker in tickers:
        try:
            df = yf.download(
                ticker,
                start=start_date.strftime("%Y-%m-%d"),
                end=end_date.strftime("%Y-%m-%d"),
            )
            if df.empty:
                print(f"Sem dados para {ticker}")
            else:
                data[ticker] = df
                print(f"Dados de {ticker} baixados com sucesso")
        except Exception as e:
            print(f"Erro ao baixar dados de {ticker}: {e}")
    return data


@task(log_prints=True, retries=3, retry_delay_seconds=10)
def save_partitioned_data(data, service, folder_id):
    os.makedirs("/tmp", exist_ok=True)
    links = {}
    partition_date = datetime.today().strftime("%Y-%m-%d")

    for ticker, df in data.items():
        file_path = f"/tmp/{ticker}_{partition_date}.csv"
        df.to_csv(file_path)
        print(f"Dados de {ticker} salvos em {file_path}")

        # Upload para o Google Drive
        link = upload_to_drive(service, file_path, folder_id)
        links[ticker] = link

    return links


@task(log_prints=True)
def create_summary_table(data):
    if not data:
        print("Sem dados para criar tabela de resumo.")
        return

    last_day_data = {ticker: df.iloc[-1] for ticker, df in data.items() if not df.empty}

    changes = []
    for ticker, row in last_day_data.items():
        close_price = row["Close"]
        previous_close = row["Open"] if row["Open"] > 0 else close_price
        daily_change = (
            (close_price - previous_close) / previous_close * 100
            if previous_close
            else 0
        )
        changes.append((ticker, daily_change))

    sorted_changes = sorted(changes, key=lambda x: x[1], reverse=True)
    top_risers = sorted_changes[:3]
    top_fallers = sorted_changes[-3:]

    table_data = {"Ticker": [], "Daily Change (%)": []}
    for ticker, change in top_risers + top_fallers:
        table_data["Ticker"].append(ticker)
        table_data["Daily Change (%)"].append(change)

    create_table_artifact(
        key="daily_stock_summary",
        table=table_data,
        description="Top 3 Risers and Fallers",
    )


@flow(log_prints=True, retries=2, retry_delay_seconds=20)
def stock_workflow():
    # Autentica o serviço do Google Drive
    service = authenticate_google_drive()

    # Configuração da pasta
    folder_id = "1IPQxziNsEvVjUBH_ZxmT4S9YMMolFmJO"

    # Baixa os dados
    data = download_stock_data(TICKERS)

    # Salva dados particionados no Drive
    save_partitioned_data(data, service, folder_id)

    # Cria tabela de resumo
    create_summary_table(data)


if __name__ == "__main__":
    flow.from_source(
        source="https://github.com/kedoshim/modelagem-de-negocio.git",
        entrypoint="final.py:stock_workflow",
    ).deploy(
        name="tvc2-worflow",
        cron="0 0 * * *",
        work_pool_name="TVC2",
        job_variables={
            "pip_packages": [
                "pandas",
                "prefect-aws",
                "prefect",
                "yfinance",
                "PyDrive",
                "nest_asyncio",
                "matplotlib",
                "google-api-python-client"
            ]
        },
    )
