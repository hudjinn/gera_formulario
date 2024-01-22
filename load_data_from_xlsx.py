import glob
import os
import shutil
from datetime import datetime
import psycopg2
import pandas as pd


def conectar_bd():
    try:
        conn = psycopg2.connect(
            database="seu_banco_de_dados",
            user="seu_usuario",
            password="sua_senha",
            host="seu_host",
            port="sua_porta"
        )
        return conn
    except psycopg2.Error as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None



def criar_dir(path):
    estados = ["AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR", "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO"]
    
    for estado in estados:
        estado_path = os.path.join(path, estado)
        if not os.path.exists(estado_path):
            os.makedirs(estado_path)

def concat_planilhas(path):
    files = glob.glob(os.path.join(path, "*.xlsx"))

    for file in files:
        df = pd.read_excel(file)

        # Obtém o estado a partir do nome do arquivo
        estado = file.split("_")[-1].split(".")[0]
        estado_path = os.path.join(path, estado)

        # Cria o diretório do estado se não existir
        if not os.path.exists(estado_path):
            os.makedirs(estado_path)

        # Renomeia o arquivo com a data atual
        timestamp = datetime.now().strftime("%Y%m%d")
        new_file = f"impactos_seca_{estado}_{timestamp}.xlsx"
        new_file_path = os.path.join(estado_path, new_file)

        # Move o arquivo para o diretório do estado
        shutil.move(file, new_file_path)

def carregar_dados(path):
    files = glob.glob(os.path.join(path, "*.xlsx"))
    form_data_list = []

    for file in files:
        df = pd.read_excel(file)
        form_data = df.to_dict(orient='records')
        form_data_list.extend(form_data)

    return form_data_list

def inserir_dados(form_data_list):
    conn = conectar_bd()
    if conn is not None:
        try:
            cursor = conn.cursor()

            for form_data in form_data_list:
                cursor.execute("""
                    INSERT INTO tabela_dados (ano_mes, uf, municipio, chuva_dt, chuva_de,
                                              percepcao_seca, acesso_agua, sit_cultura,
                                              tipo_cultura, problema_restricao)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    form_data["Ano/Mês de Referência"],
                    form_data["Estado"],
                    form_data["Município"],
                    form_data["Chuva (DT)"],
                    form_data["Chuva (DE)"],
                    form_data["Percepção Subjetiva"],
                    form_data["Acesso à Água"],
                    form_data["Situação das Culturas de Sequeiro"],
                    ",".join(form_data["Tipo de Cultura"]),
                    ",".join(form_data["Problema/Restrição"])
                ))

            conn.commit()
            print("Dados inseridos com sucesso!")

        except psycopg2.Error as e:
            print(f"Erro ao inserir dados: {e}")

        finally:
            if conn is not None:
                conn.close()

if __name__ == "__main__":
    # Obtém o diretório do arquivo executado
    current_dir = os.path.dirname(__file__)
    path = os.path.abspath(current_dir)
    
    # Uncomment as linhas abaixo para criar diretórios, concatenar planilhas e carregar dados
    criar_dir(path)
    concat_planilhas(path)
    form_data_list = carregar_dados(path)
    # inserir_dados(form_data_list)
