import streamlit as st
import pandas as pd
import nltk
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import PyPDF2
import pygsheets
import tempfile

def open_google_sheet(credentials_file, sheet_title, worksheet_title):
    try:
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(credentials_file.read())
            temp_file_path = temp_file.name

        gc = pygsheets.authorize(service_account_file=temp_file_path)
        sheet = gc.open(sheet_title)
        worksheet = sheet.worksheet_by_title(worksheet_title)
        return worksheet
    except pygsheets.SpreadsheetNotFound:
        st.error(f"No se encontró la hoja de cálculo '{sheet_title}'.")
    except pygsheets.WorksheetNotFound:
        st.error(f"No se encontró la hoja de trabajo '{worksheet_title}'.")
    except Exception as e:
        st.error(f"Error al abrir la hoja de Google: {str(e)}")
        raise

def read_worksheet(worksheet):
    return worksheet.get_as_df()

# Función para leer contenido de un archivo PDF
def leer_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file)
    contenido = ""
    for page in pdf_reader.pages:
        contenido += page.extract_text()
    return contenido

# Función para procesar la candidatura y mostrar las ofertas
def procesar_candidatura(candidatura_texto, empleos_df):
    # Convertir todas las columnas a cadenas
    empleos_df = empleos_df.astype(str)
    
    # Verificar si cada columna existe, si no, asignar un valor vacío
    columnas = ['Formación', 'Conocimientos', 'Experiencia', 'Funciones', 'Localidad', 'Provincia', 'Modalidad', 'Tipo de jornada', 'Tipo de contrato', 'Idiomas', 'Nombre', 'campo_1']
    for columna in columnas:
        if columna not in empleos_df.columns:
            empleos_df[columna] = ''
    
    # Combinar todas las características relevantes en un solo texto por oferta de trabajo
    empleos_df['texto_oferta'] = empleos_df['Formación'] + ' ' + empleos_df['Conocimientos'] + ' ' + empleos_df['Experiencia'] + ' ' + empleos_df['Funciones'] + ' ' + empleos_df['Localidad'] + ' ' + empleos_df['Provincia'] + ' ' + empleos_df['Modalidad'] + ' ' + empleos_df['Tipo de jornada'] + ' ' + empleos_df['Tipo de contrato'] + ' ' + empleos_df['Idiomas'] + ' ' + empleos_df['Nombre'] + ' ' + empleos_df['campo_1']

    # Descargar las stop words en español de NLTK
    nltk.download('stopwords')
    stop_words = stopwords.words('spanish')

    # Crear el objeto TfidfVectorizer con las stop words en español
    tfidf = TfidfVectorizer(stop_words=stop_words)

    # Generar las matrices TF-IDF para los textos de las ofertas y del perfil del candidato
    X_ofertas = tfidf.fit_transform(empleos_df['texto_oferta'])
    X_perfil = tfidf.transform([candidatura_texto])

    # Calcular las similitudes de coseno entre el perfil del candidato y cada oferta de trabajo
    cosine_sims = cosine_similarity(X_perfil, X_ofertas)

    # Ordenar las ofertas de trabajo por similitud de coseno descendente
    empleos_df['similitud'] = cosine_sims.flatten()
    empleos_df = empleos_df.sort_values('similitud', ascending=False)

    # Seleccionar las 5 primeras ofertas
    top_5_ofertas = empleos_df.head(5)

    # Mostrar la tabla con las 5 primeras ofertas ordenadas
    st.table(top_5_ofertas[['Nombre', 'similitud', 'campo_1']])

# Interfaz de usuario
st.title("Candidatura de Trabajo")

opcion = st.selectbox("Seleccione una opción", ["Subir archivo PDF", "Rellenar formulario"])

if opcion == "Subir archivo PDF":
    file = st.file_uploader("Subir archivo PDF", type=["pdf"])
    if file is not None:
        contenido_pdf = leer_pdf(file)
        st.success("El archivo PDF ha sido procesado correctamente.")
        
        # Cargar archivo de credenciales
        credentials_file = st.file_uploader("Subir archivo de credenciales JSON", type=["json"])
        if credentials_file is not None:
            sheet_title = "MyNewSheets"
            worksheet_title = "Hoja1"
            worksheet = open_google_sheet(credentials_file, sheet_title, worksheet_title)
            if worksheet:
                empleos_df = read_worksheet(worksheet)
                procesar_candidatura(contenido_pdf, empleos_df)
else:
    with st.form("Formulario de Candidatura"):
        nombre = st.text_input("Nombre")
        formacion = st.text_input("Formación")
        idiomas = st.text_input("Idiomas")
        conocimientos = st.text_input("Conocimientos")
        experiencia = st.text_input("Experiencia")
        salario = st.number_input("Salario", min_value=0)
        tipo_contrato = st.selectbox("Tipo de Contrato", ["Indefinido", "Temporal", "Prácticas"])
        tipo_jornada = st.selectbox("Tipo de Jornada", ["Completa", "Parcial"])
        modalidad = st.selectbox("Modalidad", ["Presencial", "Remoto", "Híbrido"])
        sector = st.text_input("Sector")
        localidad = st.text_input("Localidad")
        provincia = st.text_input("Provincia")
        
        submit = st.form_submit_button("Enviar")
        
        if submit:
            candidatura_texto = f"{formacion} {conocimientos} {experiencia} {idiomas} {tipo_contrato} {tipo_jornada} {modalidad} {localidad} {provincia}"
            
            # Cargar archivo de credenciales
            credentials_file = st.file_uploader("Subir archivo de credenciales JSON", type=["json"])
            if credentials_file is not None:
                sheet_title = "MyNewSheets"
                worksheet_title = "Hoja 1"
                worksheet = open_google_sheet(credentials_file, sheet_title, worksheet_title)
                if worksheet:
                    empleos_df = read_worksheet(worksheet)
                    procesar_candidatura(candidatura_texto, empleos_df)
