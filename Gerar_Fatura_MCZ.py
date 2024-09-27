import streamlit as st
import mysql.connector
import decimal
import pandas as pd

def bd_phoenix(vw_name):
    # Parametros de Login AWS
    config = {
    'user': 'user_automation_jpa',
    'password': 'luck_jpa_2024',
    'host': 'comeia.cixat7j68g0n.us-east-1.rds.amazonaws.com',
    'database': 'test_phoenix_maceio'
    }
    # Conexão as Views
    conexao = mysql.connector.connect(**config)
    cursor = conexao.cursor()

    request_name = f'SELECT * FROM {vw_name}'

    # Script MySql para requests
    cursor.execute(
        request_name
    )
    # Coloca o request em uma variavel
    resultado = cursor.fetchall()
    # Busca apenas o cabecalhos do Banco
    cabecalho = [desc[0] for desc in cursor.description]

    # Fecha a conexão
    cursor.close()
    conexao.close()

    # Coloca em um dataframe e muda o tipo de decimal para float
    df = pd.DataFrame(resultado, columns=cabecalho)
    df = df.applymap(lambda x: float(x) if isinstance(x, decimal.Decimal) else x)
    return df

st.set_page_config(layout='wide')

if not 'df_sales' in st.session_state:

    st.session_state.df_sales = bd_phoenix('vw_sales_partner')

st.title('Gerar Fatura - Maceió')

st.divider()

row0 = st.columns(2)

with row0[0]:

    container_dados = st.container()

    atualizar_dados = container_dados.button('Carregar Dados do Phoenix', use_container_width=True)

    data_inicial = st.date_input('Data Inicial', value=None ,format='DD/MM/YYYY', key='data_inicial')

    data_final = st.date_input('Data Final', value=None ,format='DD/MM/YYYY', key='data_final')

if atualizar_dados:

    st.session_state.df_sales = bd_phoenix('vw_sales_partner')

st.divider()

if data_inicial and data_final:

    df_reservas_data_final = st.session_state.df_sales[~pd.isna(st.session_state.df_sales['Data Execucao'])]\
        [['Cod_Reserva', 'Data Execucao']].drop_duplicates().groupby('Cod_Reserva')['Data Execucao'].max().reset_index()
    
    df_reservas_data_final_filtrado = df_reservas_data_final[(df_reservas_data_final['Data Execucao'] >= data_inicial) & 
                                                             (df_reservas_data_final['Data Execucao'] <= data_final)]\
                                                                .reset_index(drop=True)
    
    lista_reservas = df_reservas_data_final_filtrado['Cod_Reserva'].unique().tolist()

    df_sales_data_final = st.session_state.df_sales[(st.session_state.df_sales['Cod_Reserva'].isin(lista_reservas)) & 
                                                    (st.session_state.df_sales['Status_Financeiro']=='A Faturar')]\
        .reset_index(drop=True) 
    
    lista_operadoras = df_sales_data_final['Nome_Parceiro'].unique().tolist()

    with row0[1]:

        operadora = st.selectbox('Operadoras', sorted(lista_operadoras), index=None)

    if operadora:

        df_sales_operadora = df_sales_data_final[(df_sales_data_final['Nome_Parceiro']==operadora) & 
                                                 ~(pd.isna(df_sales_data_final['Cod_Tarifa']))].reset_index(drop=True)\
        
        df_sales_operadora = pd.merge(df_sales_operadora, df_reservas_data_final_filtrado, on='Cod_Reserva', how='left')

        df_sales_operadora = \
            df_sales_operadora.rename(columns={'Cod_Reserva': 'Reserva', 'voucher': 'Voucher', 'Data Execucao_x': 'Data de Execução', 
                                               'Data Execucao_y': 'Data do Último Serviço', 'Nome_Servico': 'Serviços', 
                                               'Valor_Venda': 'Valor Serviços'})
        
        faturamento_total = df_sales_operadora['Valor Serviços'].sum()

        with row0[1]:

            st.subheader(f'Valor Total à Faturar = R${faturamento_total}')

        container_dataframe = st.container()

        container_dataframe.dataframe(df_sales_operadora[['Reserva', 'Voucher', 'Data de Execução', 'Data do Último Serviço', 
                                                          'Serviços', 'Cliente', 'Valor Serviços']], hide_index=True, 
                                                          use_container_width=True)
        
        

        