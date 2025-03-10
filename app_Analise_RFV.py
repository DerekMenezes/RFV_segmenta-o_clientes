import numpy as np 
import pandas as pd
from datetime import datetime
import streamlit as st
from PIL import Image
from io import BytesIO
from xlsxwriter import Workbook


# Configuração inicial da página da aplicação
st.set_page_config(page_title = 'Analise RFV', \
        page_icon = 'laptop.png',
        layout="wide",
        initial_sidebar_state='expanded'
    )

    # Título principal da aplicação
st.write(""""# Análise RFV
**RFV** significa recência, frequência, valor e é utilizado para segmentação
 de clientes baseado no comportamento de compras dos clientes e agrupa eles em 
clusters parecidos. Utilizando esse tipo de agrupamento podemos realizar ações
 de marketing e CRM melhores direcionadas, ajudando assim na personalização do conteúdo e até a retenção de clientes.
Para cada cliente é preciso calcular cada uma das componentes abaixo:

- Recência (R): Quantidade de dias desde a última compra.
- Frequência (F): Quantidade total de compras no período.
- Valor (V): Total de dinheiro gasto nas compras do período.

E é isso que iremos fazer abaixo.
         """)
st.markdown("---")



# Função para ler os dados
@st.cache_data(show_spinner= True)
def load_data(file_data):
    try:
        return pd.read_csv(file_data, sep=',')
    except:
        return pd.read_excel(file_data)


# Função para converter o df para csv
@st.cache_data
def convert_df(df):
    return df.to_csv(index=False).encode('utf-8')


# Função para converter o df para excel
@st.cache_data
def to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Sheet1')
    writer.close()
    processed_data = output.getvalue()
    return processed_data


# Função principal da aplicação
def main():



    # Apresenta a imagem na barra lateral da aplicação
    image = Image.open("owl.png")
    st.sidebar.image(image)

    # Botão para carregar arquivo na aplicação
    st.sidebar.write("## Suba o arquivo")
    df_compras = st.sidebar.file_uploader("RFV data", type = ['csv','xlsx'])

    # Verifica se há conteúdo carregado na aplicação
    if (df_compras is not None):
        compras_raw = load_data(df_compras)
        compras = compras_raw.copy()

        st.table(compras_raw.head(20))


        
            # DATAS
        max_data = compras_raw.DiaCompra.max()
        min_data = compras_raw.DiaCompra.min()
        dia_atual = datetime(2021, 12, 9)
        
            
            # RECÊNCIA
        df_recencia = compras.groupby(by='ID_cliente',as_index=False)['DiaCompra'].max()
        df_recencia.columns = ['ID_cliente', 'DiaUltimaCompra']
        st.write(df_recencia.head())
            
        df_recencia['DiaUltimaCompra'] = pd.to_datetime(df_recencia['DiaUltimaCompra'])
        df_recencia['Recencia'] = df_recencia['DiaUltimaCompra'].apply(lambda x: (dia_atual - x).days)
        compras['DiaCompra'].max()
        dia_atual = datetime(2021,12,9)

        st.write(df_recencia.head())
        df_recencia.drop('DiaUltimaCompra', axis=1, inplace=True)

        # FREQUÊNCIA

        df_frequencia = compras[['ID_cliente', 'CodigoCompra']].groupby('ID_cliente').count().reset_index()
        df_frequencia.columns = ['ID_cliente', 'Frequencia']
        st.write(df_frequencia.head())

        # VALOR

        df_valor = compras[['ID_cliente', 'ValorTotal']].groupby('ID_cliente').sum().reset_index()
        df_valor.columns = ['ID_cliente', 'Valor']
        df_valor.head()

        #RF

        df_RF = df_recencia.merge(df_frequencia, on='ID_cliente')
        st.write(df_RF.head())

        # RFV

        df_RFV = df_RF.merge(df_valor, on='ID_cliente')
        df_RFV.set_index('ID_cliente', inplace=True)
        st.write(df_RFV.head())

        # QUARTIS

        quartis = df_RFV.quantile(q=[0.25, 0.5, 0.75])
        quartis.to_dict()

        def recencia_class(x, r, q_dict):
            """Classifica como melhor o menor quartil 
            x = valor da linha,
            r = recencia,
            q_dict = quartil dicionario   
                """
            if x <= q_dict[r][0.25]:
                return 'A'
            elif x <= q_dict[r][0.50]:
                return 'B'
            elif x <= q_dict[r][0.75]:
                return 'C'
            else:
                return 'D'


        def freq_val_class(x, fv, q_dict):
            """Classifica como melhor o maior quartil 
            x = valor da linha,
            fv = frequencia ou valor,
            q_dict = quartil dicionario   
            """
            if x <= q_dict[fv][0.25]:
                return 'D'
            elif x <= q_dict[fv][0.50]:
                return 'C'
            elif x <= q_dict[fv][0.75]:
                return 'B'
            else:
                return 'A'
            
        df_RFV['R_quartil'] = df_RFV['Recencia'].apply(recencia_class, args=('Recencia', quartis))
        df_RFV['F_quartil'] = df_RFV['Frequencia'].apply(freq_val_class,args=('Frequencia', quartis))
        df_RFV['V_quartil'] = df_RFV['Valor'].apply(freq_val_class,args=('Valor', quartis))

        df_RFV['RFV_Score'] = (df_RFV.R_quartil + df_RFV.F_quartil + df_RFV.V_quartil)
        st.write(df_RFV.head())

        # ações

        dict_acoes = {
            'AAA':
            'Enviar cupons de desconto, Pedir para indicar nosso produto pra algum amigo, Ao lançar um novo produto enviar amostras grátis pra esses.',
            'DDD':
            'Churn! clientes que gastaram bem pouco e fizeram poucas compras, fazer nada',
            'DAA':
            'Churn! clientes que gastaram bastante e fizeram muitas compras, enviar cupons de desconto para tentar recuperar',
            'CAA':
            'Churn! clientes que gastaram bastante e fizeram muitas compras, enviar cupons de desconto para tentar recuperar'
            }
            
        df_RFV['acoes de marketing/crm'] = df_RFV['RFV_Score'].map(dict_acoes)

        st.write(df_RFV.head())

        
        df_xlsx = to_excel(df_RFV)
        st.download_button(label='📥 Download tabela filtrada em EXCEL',
                           data=df_xlsx ,file_name= 'RFV.xlsx')
        
        with st.sidebar.form("formulario_rfv"):
            recencia = st.number_input("Recência (dias)")
            frequencia = st.number_input("Frequência")
            valor = st.number_input("Valor (R$)")
    
            # Botão de submit
            submitted = st.form_submit_button("Calcular RFV")

        # Processar dados apenas se o botão for pressionado
            if submitted:
                dados_cliente = {
            'Recencia': [recencia],
            'Frequencia': [frequencia],
            'Valor': [valor]
        }
        df = pd.DataFrame(dados_cliente)
        
        # Aplicar classificações
        df['R_quartil'] = df['Recencia'].apply(recencia_class, args=('Recencia', quartis))
        df['F_quartil'] = df['Frequencia'].apply(freq_val_class, args=('Frequencia', quartis))
        df['V_quartil'] = df['Valor'].apply(freq_val_class, args=('Valor', quartis))
        
        df['RFV_Score'] = df['R_quartil'] + df['F_quartil'] + df['V_quartil']
        df['Acoes'] = df['RFV_Score'].map(dict_acoes)
        
        st.success("## Resultado da Análise RFV")
        st.metric(label="Score RFV", value=df['RFV_Score'].iloc[0])
        st.write(f"Ação Recomendada: **{df['Acoes'].iloc[0]}**")

        with st.expander("Ver detalhes das classificações"):
            st.write(f"**Recência ({df['Recencia'].iloc[0]} dias):** {df['R_quartil'].iloc[0]}")
            st.write(f"**Frequência ({df['Frequencia'].iloc[0]}):** {df['F_quartil'].iloc[0]}")
            st.write(f"**Valor (R$ {df['Valor'].iloc[0]:.2f}):** {df['V_quartil'].iloc[0]}")
    st.markdown("---")



if __name__ == '__main__':
	main()