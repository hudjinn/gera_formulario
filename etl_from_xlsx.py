import glob
import os

from datetime import datetime
import psycopg2
from psycopg2.extras import execute_values
import pandas as pd


class ETL:
    def __init__(self, host, database, user, password, port=5432):
        """
        Inicializa a classe ETL.

        Atributos:
        - tabelas (list): Lista das tabelas a serem processadas.
        - estados (list): Lista dos estados a serem considerados.
        - mapeamento_col (dict): Dicionário que mapeia as colunas entre DataFrame e tabela do banco de dados.
        """
        
        self.tabelas = ['dt_chuva',
                        'de_chuva',
                        'qnt_chuva',
                        'percepcao_seca',
                        'acesso_agua',
                        'sit_cultura',
                        'tipo_cultura',
                        'problema_restricao']
        
        self.estados = ["AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", 
                        "MA", "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR",
                        "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO"]
        
        # Mapeamento de colunas entre DataFrame e tabela do banco de dados
        self.mapeamento_col = {
            'Ano/Mês de Referência': 'ano_mes',
            'Estado': 'uf',
            'Município': 'municipio',
            'Chuva (DT)': 'dt_chuva',
            'Chuva (DE)': 'de_chuva',
            'Quantidade de Chuva': 'qnt_chuva',
            'Percepção Subjetiva': 'percepcao_seca',
            'Acesso à Água': 'acesso_agua',
            'Situação das Culturas de Sequeiro': 'sit_cultura',
            'Tipo de Cultura': 'tipo_cultura',
            'Problema/Restrição': 'problema_restricao'
        }
        self.sucesso = False
        self.lista_arquivos = []
        self.conexao = {"database": database,
                        "user": user,
                        "password": password,
                        "host": host,
                        "port": port}

    def armazenar_planilhas(self, path, df):
        """
        Armazena os dados do DataFrame em planilhas Excel, separadas por estado.

        Args:
            path (str): Caminho do diretório onde os arquivos serão armazenados.
            df (pd.DataFrame): DataFrame contendo os dados a serem armazenados.

        Returns:
            None
        """    

        
        for estado in df['uf'].unique():
            self.criar_dir_estados(path, estado)
            df_estado = df[df['uf'] == estado]
            estado_path = os.path.join(path, estado)

            # Renomeia o arquivo com a data atual
            timestamp = datetime.now().strftime("%Y%m%d")
            new_file = f"impactos_seca_{estado}_{timestamp}.csv"
            new_file_path = os.path.join(estado_path, new_file)

            # Salva o DataFrame como arquivo Excel
            df_estado.to_csv(new_file_path, index=False, sep=';')
            print(f'Dados salvos em: {new_file_path}')
            
            for file in self.lista_arquivos:
                os.remove(file)

    def criar_dir_estados(self, path, estado):
        """
        Cria diretórios para cada estado se não existirem.

        Args:
            path (str): Caminho do diretório principal.

        Returns:
            None
        """
        os.makedirs(os.path.join(path, 'formularios'))
        estado_path = os.path.join(path, estado)
        os.makedirs(estado_path, exist_ok=True) 
            
            
    def atualizar_mapa_valores(self, values_path):
        """
        Atualiza os arquivos CSV com mapas de valores contendo id e descrição de cada índice da tabela.

        Args:
            values_path (str): Caminho do diretório contendo os arquivos CSV de mapas de valores.

        Returns:
            None
        """

        for tabela in self.tabelas:
            query = f"SELECT * FROM monitor.{tabela}"
            # Execute a consulta e obtenha os dados como DataFrame
            dados_tabela = pd.read_sql_query(query, self.conectar_bd())
            dados_tabela.set_index(f'id_{tabela}', inplace=True)
            file_path = os.path.join(values_path, tabela)
            dados_tabela.to_csv(file_path, sep=';', header=None)



    def carregar_dados_planilhas(self, path):
        """
        Carrega dados de planilhas Excel em um DataFrame, realiza mapeamento de colunas e substitui valores.

        Args:
            path (str): Caminho do diretório contendo as planilhas Excel.
            df_values (pd.DataFrame): DataFrame contendo mapas de valores.

        Returns:
            pd.DataFrame: DataFrame contendo os dados carregados e mapeados.
        """
        df_data = pd.DataFrame()

        files = glob.glob(os.path.join(path, "*.xlsx"))

        for file in files:
            df = pd.read_excel(file)
            df_data = pd.concat([df_data, df], ignore_index=True)
            self.lista_arquivos.append(file)
        # Verifica e remove dados duplicados
        df_data.drop_duplicates(inplace=True)
        
        # Renomeia colunas do DataFrame de acordo com o mapeamento
        df_data.rename(columns=self.mapeamento_col, inplace=True)


        return df_data


    def carregar_mapa_valores(self, path):
        """
        Carrega mapas de valores de arquivos CSV em um DataFrame.

        Args:
            path (str): Caminho do diretório contendo os arquivos CSV.

        Returns:
            pd.DataFrame: DataFrame contendo os mapas de valores.
        """
        
        df_values = pd.DataFrame()

        for tabela in self.tabelas:
            filepath = os.path.join(path, tabela)
            df_value = pd.read_csv(filepath, header=None, names=[f'id_{tabela}', tabela], sep=';')
            df_value.set_index(df_value.columns[0], inplace=True)
            df_values = pd.concat([df_values, df_value], axis=1)
        df_values = df_values.sort_index(ascending=True)

        return df_values


    def carregar_cod_mun(self):
        """
        Carrega códigos municipais do banco de dados.

        Returns:
            pd.DataFrame: DataFrame contendo códigos municipais.
        """
        conn = self.conectar_bd()

        # Assuming you have a table named 'limites_municipais_ibge_2022'
        query = "SELECT sigla_uf, nome_mun, cod_mun FROM monitor.limites_municipais_ibge_2022"
        df_mun = pd.read_sql_query(query, conn)

        if conn is not None:
            conn.close()

        return df_mun


    def conectar_bd(self):
        """
        Estabelece conexão com o banco de dados PostgreSQL.

        Returns:
            psycopg2.extensions.connection: Conexão ao banco de dados.
        """
        try:
            conn = psycopg2.connect(**self.conexao
            )
            return conn
        except psycopg2.Error as e:
            print(f"Erro ao conectar ao banco de dados: {e}")
            raise


    def inserir_dados(self, df_data):
        """
        Insere dados no banco de dados PostgreSQL.

        Args:
            df_data (pd.DataFrame): DataFrame contendo os dados a serem inseridos.

        Returns:
            None
        """
        conn = self.conectar_bd()

        if conn is not None:
            try:
                cursor = conn.cursor()

            # Gera a string de inserção
                insert_query = f"""
                    INSERT INTO monitor.impactos_seca ({', '.join(df_data.columns)})
                    VALUES %s
                """

                # Gera os valores para inserção
                values = [tuple(row[1]) for row in df_data.iterrows()]

                # Utiliza execute_values para inserção em lote
                execute_values(cursor, insert_query, values, page_size=len(values))

                conn.commit()

                print("Dados inseridos com sucesso!")

            except psycopg2.Error as e:
                print(f"Erro ao inserir dados: {e}")
                raise
                

            finally:

                if conn is not None:
                    self.sucesso = True
                    conn.close()
                    

    def substituir_valores(self, df_data, df_values):
        """
        Substitui valores no DataFrame com base nos mapas de valores.

        Args:
            df_data (pd.DataFrame): DataFrame contendo os dados a serem modificados.
            df_values (pd.DataFrame): DataFrame contendo mapas de valores.

        Returns:
            pd.DataFrame: DataFrame modificado.
        """
        for col in df_data.columns:
            if col in df_values.columns:
                map_dict = df_values[col].to_dict()
                mapeamento_valores = {valor: chave for chave, valor in map_dict.items()}

                if col in ['tipo_cultura', 'problema_restricao']:
                    df_data[col] = df_data[col].apply(lambda x: [mapeamento_valores.get(val, val) for val in x.split(', ')])
                else:               
                    df_data[col] = df_data[col].map(mapeamento_valores)

        # Substituir uf e municipio por cod_mun através de consulta ao banco
        df_mun = self.carregar_cod_mun()

        # Mapear cod_mun a partir das colunas uf e municipio
        df_data = pd.merge(df_data, df_mun, how='left', left_on=['uf', 'municipio'], right_on=['sigla_uf', 'nome_mun'])
        
        # Substituir colunas uf e municipio por cod_mun
        df_data.drop(columns=['uf', 'municipio', 'sigla_uf', 'nome_mun'], inplace=True)
        
        # Remover hífen do ano_mes
        df_data['ano_mes'] = df_data['ano_mes'].str.replace('-', '')
        df_data['ano_mes'] = df_data['ano_mes'].astype(int)

        return df_data



if __name__ == "__main__":
    
    database="monitor"
    user="postgres"
    password="12345"
    host="192.168.10.74"
    port="5432"

    etl = ETL(host=host, database=database, user=user, password=password, port=port)
    atualizar = True
    # Obtém o diretório do arquivo executado
    current_dir = os.path.dirname(__file__)
    root_path = os.path.abspath(current_dir)
    
    # Diretório dos Formulários
    files_path = os.path.join(root_path, 'formularios')

    # Diretório dos Mapas de Valores
    values_id_path = os.path.join(root_path, 'mapa_de_valores')
    
    if atualizar:
        etl.atualizar_mapa_valores(values_id_path)
    
    # Obtém os códigos para correlação id/descrição
    df_values = etl.carregar_mapa_valores(path=values_id_path)
    df_data = etl.carregar_dados_planilhas(path=root_path)
    if not df_data.empty:
        df_data_with_id = etl.substituir_valores(df_data=df_data, df_values=df_values)
        etl.inserir_dados(df_data=df_data_with_id)
        if etl.sucesso:
            etl.armazenar_planilhas(path=files_path, df=df_data)



