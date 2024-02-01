# ETL - Extração, Transformação e Carga

Este projeto consiste em um processo de Extração, Transformação e Carga (ETL) implementado em Python, utilizando as bibliotecas pandas e psycopg2 para extrair dados de arquivos Excel, transformá-los e carregá-los em um banco de dados PostgreSQL.

## Funcionalidades

- **Armazenamento de Planilhas por Estado**: Os dados extraídos dos arquivos Excel são armazenados em planilhas separadas por estado.

- **Atualização de Mapas de Valores**: Os arquivos CSV contendo mapas de valores, que mapeiam IDs e descrições de cada índice na tabela, são atualizados automaticamente.

## Requisitos

- Python 3.11
- psycopg2 2.9.9
- pandas 2.1.3
- datetime 5.4

## Configuração

1. Instale as dependências do projeto executando os seguintes comandos:
    
    ```
    apt-get update && apt-get install -y libpq-dev python3-pip
    ```
    ```
    pip install pandas psycopg2 
    ```

2. Certifique-se de ter um servidor PostgreSQL em execução e as credenciais de acesso apropriadas.

3. Configure as informações de conexão com o banco de dados PostgreSQL no init da classe `ETL`. #TODO: Melhoria de segurança de senhas

4. Coloque seus arquivos Excel contendo os dados na pasta `formularios` no mesmo diretório do script.

5. Execute o script Python `etl_from_xlsx.py`.

## Como Usar

1. Execute o script Python `etl_from_xlsx.py`.

2. Os dados serão extraídos dos arquivos Excel constantes na pasta raíz, transformados de acordo com o mapeamento de colunas e inseridos no banco de dados.

3. Os dados também serão armazenados em planilhas separadas por estado na pasta `formularios` após a inserção no banco de dados.


## Autores

- [Jefferson Sant'ana Galvão](https://github.com/hudjinn) - Geógrafo, Analista de Sistemas. Especialista em Sistema de Informação Espacial (Geoprocessamento).

