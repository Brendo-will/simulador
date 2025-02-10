import streamlit as st
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import tempfile
import base64
import os
from loaders import carrega_pdf, carrega_html  

# Função para converter imagem em base64
def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")

# Caminho da logo
logo_path = "logo/chat.png"
logo_base64 = get_base64_image(logo_path)

# Interface da aplicação
st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: white;
    }}
    .stApp header {{
        background-color: #7C4DFF;
        color: white;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        display: flex;
        align-items: center;
        gap: 10px;
    }}
    .logo {{
        height: 80px;
        opacity: 0.5;
    }}
    .title {{
        font-size: 32px;
        font-weight: bold;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    f"""
    <div style='display: flex; align-items: center; gap: 10px;'>
        <img class='logo' src='data:image/png;base64,{logo_base64}' alt='Logo'>
        <span class='title'>Paradabot</span>
    </div>
    """,
    unsafe_allow_html=True
)

# Campo para inserir a chave da OpenAI
st.sidebar.header("Configuração")
esconder_chave = st.sidebar.checkbox("Ocultar chave da OpenAI", value=True)
openai_api_key = st.sidebar.text_input("Digite sua chave da OpenAI:", type="password" if esconder_chave else "text")

# Função para extrair informações do arquivo
def extrair_informacoes(arquivo, tipo_arquivo):
    if tipo_arquivo == 'Pdf':
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp:
            temp.write(arquivo.read())
            nome_temp = temp.name
        documento = carrega_pdf(nome_temp)    
    elif tipo_arquivo == 'Html':
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as temp:
            temp.write(arquivo.read())
            nome_temp = temp.name
        documento = carrega_html(nome_temp)
    else:
        documento = "Tipo de arquivo não suportado."
    return documento

# Função para gerar resposta
def gerar_resposta(prompt, informacoes):
    if not openai_api_key:
        st.error("Por favor, insira a chave da OpenAI na barra lateral.")
        return ""
    
    chat = ChatOpenAI(model="gpt-4o", api_key=openai_api_key)
    
    template = ChatPromptTemplate.from_messages([  
        ("system", "Dado um texto extraído de documento, analise e extraia as informações necessárias..."),
        ("user", "{input}")
    ])
    
    chain = template | chat
    resposta = chain.invoke({"input": f"{prompt}\n\nInformações extraídas:\n{informacoes}"})
    
    return resposta.content

# Interface principal
tipo_arquivo = st.selectbox("Selecione o tipo de arquivo", ["Pdf", "Html"])
arquivo = st.file_uploader("Faça o upload do arquivo", type=["pdf", "html"])

if arquivo is not None:
    informacoes = extrair_informacoes(arquivo, tipo_arquivo)
    st.text_area("Informações extraídas do arquivo:", informacoes, height=200)
    
    # Exibir opções de prompts para o usuário escolher
    prompt_opcoes = {
        "Breve relato": """Você é um advogado sênior. Analise o texto a seguir e forneça um resumo:
        Fatos alegados: [Fatos do caso]
        Fundamentos jurídicos: [Fundamentos legais]
        Matéria discutida: [Questão principal]""",
        
        "Incluir sentença": """Aja como um advogado sênior especialista em análise de sentenças.
        Interprete o texto da sentença conforme as instruções abaixo e classifique os campos solicitados.
        
        ## Sentença:
        {documento}
        
        ## Campos a preencher:
        -Comando para Extrair Informações de uma Sentença Judicial
Breve Relato da Sentença: Gerar um resumo objetivo da sentença, destacando os principais pontos da decisão.

Fundamentação da Sentença: Extrair os principais argumentos jurídicos utilizados pelo juiz para embasar a decisão.

Juiz Responsável: Identificar o nome do magistrado que proferiu a decisão.

Data da Sentença: Extrair a data em que a sentença foi proferida.

Pedidos do Autor e Resultado: Para cada pedido formulado pelo autor, identificar:

Se foi procedente ou improcedente.
Caso procedente, informar o valor determinado na sentença. Se não houver um valor especificado, indicar "valor não encontrado na sentença".
Exemplo de saída:

Dano material: Procedente – Valor: R$ 5.000,00.
Dano moral: Improcedente.
Condenação: Identificar as obrigações impostas às partes (pagamento de valores, cumprimento de obrigação de fazer, etc.).

Multa e Juros: Verificar se há incidência de multa, juros e correção monetária.

Honorários Advocatícios: Identificar se há condenação em honorários advocatícios e seu percentual."""
    }
    
    prompt_escolhido = st.selectbox("Escolha um prompt para gerar a resposta:", list(prompt_opcoes.keys()))

    if st.button("Gerar Resposta"):
        if prompt_escolhido:
            resposta = gerar_resposta(prompt_opcoes[prompt_escolhido], informacoes)
            st.text_area("Resposta gerada:", resposta, height=200)
        else:
            st.warning("Por favor, escolha um prompt.")
else:
    st.warning("Por favor, faça o upload de um arquivo para continuar.")
