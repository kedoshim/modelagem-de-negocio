**📘 Informações Gerais**
Este projeto foi desenvolvido por **Abraão de Paula Carolino (Matrícula: 202135016)**  para a disciplina de **Modelagem de Negócios**  na **UFJF - Ciência da Computação** . A atividade se chama **TVC2**  e envolve a coleta, processamento e análise de dados financeiros de ações, além do armazenamento seguro no **Google Drive**  utilizando fluxos automatizados via **Prefect** .

---

**📂 Estrutura do Projeto** 
O projeto possui as seguintes funcionalidades principais:
 
- **Autenticação com Google Drive:**  Upload automatizado de dados financeiros para uma pasta específica no Drive.
 
- **Coleta de Dados Financeiros:**  Download de informações das ações especificadas usando a API do **Yahoo Finance** .
 
- **Processamento de Dados:**  Salvamento de dados particionados e criação de relatórios com os maiores ganhos e perdas diários.
 
- **Fluxo Automatizado:**  Agendamento do workflow usando Prefect para execução periódica.


---

**📋 Pré-requisitos** 
Para rodar o projeto, certifique-se de ter os seguintes requisitos instalados:
 
- **Python 3.8 ou superior**
 
- As bibliotecas necessárias listadas abaixo:

```bash
pip install pandas prefect-aws prefect yfinance PyDrive nest_asyncio matplotlib google-api-python-client
```

- Conta de serviço configurada no Google Cloud com permissões para o Google Drive.


---

**🚀 Como Rodar o Projeto**  
1. **Clone o Repositório:** 

```bash
git clone https://github.com/kedoshim/modelagem-de-negocio.git
cd modelagem-de-negocio
```
 
2. **Configure as Variáveis de Ambiente:** 
Defina os seguintes blocos no Prefect: 
  - **Credenciais do Google Drive:**  Armazene o JSON da conta de serviço.
 
  - **Lista de Tickers:**  Adicione uma variável `tickers` no Prefect com os códigos das ações desejadas.
 
3. **Executando o Workflow:** 
Execute o workflow diretamente:

```bash
python final.py
```
 
4. **Agendamento Automático:** 
O workflow está configurado para ser executado periodicamente com a seguinte configuração de cron:

```cron
0 0 * * * (00:00 todos os dias)
```
