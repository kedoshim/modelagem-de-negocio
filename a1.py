# !prefect cloud login -k pnu_1T1jSme5KcH2I2ZP0b9RRFIVid8jhX17hAlN

import yfinance as yf
from datetime import datetime, timedelta
from prefect import task, flow
import pandas as pd
import os
import matplotlib.pyplot as plt
from prefect.artifacts import create_link_artifact, create_image_artifact
import time
import nest_asyncio


from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

# g_login = GoogleAuth()
# drive = GoogleDrive(g_login)

# nest_asyncio.apply()


# Conectar ao Google Drive


# Defina as variáveis de data e os tickers
start_date = "2024-01-01"
end_date = "2024-12-31"
tickers = ["PETR4.SA", "ITUB4.SA", "VALE3.SA", "WEGE3.SA", "ABEV3.SA"]


# Task para baixar dados
@task
def download_stock_data(tickers, start_date, end_date, log_prints=True):
    data = {}
    for ticker in tickers:
        df = yf.download(ticker, start=start_date, end=end_date)
        data[ticker] = df
        print(f"Dados de {ticker} baixados com sucesso")
    return data


@task(log_prints=True)
def plot_moving_averages(
    data: pd.DataFrame,
    ticker: str,
    window_sizes: list = [20, 50, 200],
    folder_path="/content/drive/My Drive/stock_data",
):
    """Plots moving averages for a given stock."""

    if data is None or data.empty:
        print("No data to plot.")
        return

    data["MA20"] = data["Close"].rolling(window=20).mean()
    data["MA50"] = data["Close"].rolling(window=50).mean()
    data["MA200"] = data["Close"].rolling(window=200).mean()

    plt.figure(figsize=(12, 6))
    plt.plot(data["Close"], label="Close Price")
    for window in window_sizes:
        ma_column = f"MA{window}"
        if ma_column in data.columns:  # Check if MA column exists
            plt.plot(data[ma_column], label=ma_column)

    plt.title(f"Moving Averages for {ticker}")
    plt.xlabel("Date")
    plt.ylabel("Price")
    plt.legend()
    plt.grid(True)

    plot_filename = os.path.join(folder_path, f"{ticker}-moving-averages.png")

    # Save the plot first, then display it
    plt.savefig(plot_filename)
    plt.close()  # Close the plot to prevent display in notebook
    print(f"Moving averages plot saved as {plot_filename}")

    # Create Prefect artifact link for the plot
    create_image_artifact(
        key=f"{ticker.lower().replace('.','')}-moving-average-plot",
        image_url=plot_filename,
        description=f"Moving average plot for {ticker}",
    )

    return plot_filename


@task(log_prints=True)
def plot_volatility(
    data: pd.DataFrame,
    ticker: str,
    window: int = 30,
    folder_path="/content/drive/My Drive/stock_data",
):

    if data is None or data.empty:
        print("No data to plot volatility")
        return

    data["Volatility"] = data["Close"].pct_change().rolling(window=window).std() * (
        252**0.5
    )  # Annualized volatility
    plt.figure(figsize=(12, 6))
    plt.plot(data["Volatility"], label="Volatility")
    plt.title(f"{ticker} Volatility ({window}-day rolling)")
    plt.xlabel("Date")
    plt.ylabel("Volatility")
    plt.legend()
    plt.grid(True)

    plot_filename = os.path.join(folder_path, f"{ticker}_volatility.png")

    # Save the plot first, then display it
    plt.savefig(plot_filename)
    plt.close()
    print(f"Volatility plot saved as {plot_filename}")

    # Create Prefect artifact link for the plot
    create_image_artifact(
        key=f"{ticker.lower().replace('.','')}-volatility-plot",
        image_url=plot_filename,
        description=f"Volatility plot for {ticker}",
    )

    return plot_filename


# Task para salvar o DataFrame no Google Drive e criar um link de artefato
@task
def upload_to_drive_and_create_link(
    data, folder_path="/content/drive/My Drive/stock_data"
):
    os.makedirs(folder_path, exist_ok=True)
    links = {}
    for ticker, df in data.items():
        file_path = os.path.join(folder_path, f"{ticker}-stock-data.csv")
        df.to_csv(file_path)
        print(f"Dados de {ticker} salvos em {file_path}")
        links[ticker] = file_path

        create_link_artifact(
            key=ticker.lower().replace(".", ""),
            link=file_path,
            description=ticker + " stock data",
        )

    return links


# Criando o fluxo Prefect
@flow
def stock_workflow():
    from google.colab import drive

    drive.mount("/content/drive")

    data = download_stock_data(tickers, start_date, end_date)
    plots = {}
    for ticker in tickers:
        plots[ticker] = {
            "moving_average": plot_moving_averages(data[ticker], ticker),
            "volatility": plot_volatility(data[ticker], ticker),
        }

    artifact_links = upload_to_drive_and_create_link(data)
    for ticker, link in artifact_links.items():
        print(f"Link para os dados de {ticker}: {link}")

    # The plot links will be automatically generated and logged as artifacts
    print("Plot artifacts have been created.")


# Executar o fluxo
if __name__ == "__main__":
    stock_workflow.deploy(
        name="tvc2-workflow",
        cron="0 0 * * *",
        work_pool_name="TVC2",
        image="sorokine/docker-colab-local",
    )
    # stock_workflow.serve(name="tvc2-workflow", cron="0 0 * * *")
# stock_workflow()


# !prefect deployment run 'stock-workflow/tvc2-workflow'
