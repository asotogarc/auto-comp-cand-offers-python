import streamlit as st
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import PyPDF2
import pygsheets
import tempfile

# Predefined list of Spanish stopwords
SPANISH_STOPWORDS = [
    "a", "al", "algo", "algunas", "algunos", "ante", "antes", "como", "con", "contra",
    "cual", "cuando", "de", "del", "desde", "donde", "durante", "e", "el", "ella",
    "ellas", "ellos", "en", "entre", "era", "erais", "eran", "eras", "eres", "es",
    "esa", "esas", "ese", "eso", "esos", "esta", "estaba", "estabais", "estaban",
    "estabas", "estad", "estada", "estadas", "estado", "estados", "estamos", "estando",
    "estar", "estaremos", "estará", "estarán", "estarás", "estaré", "estaréis",
    "estaría", "estaríais", "estaríamos", "estarían", "estarías", "estas", "este",
    "estemos", "esto", "estos", "estoy", "estuve", "estuviera", "estuvierais",
    "estuvieran", "estuvieras", "estuvieron", "estuviese", "estuvieseis", "estuviesen",
    "estuvieses", "estuvimos", "estuviste", "estuvisteis", "estuviéramos",
    "estuviésemos", "estuvo", "está", "estábamos", "estáis", "están", "estás", "esté",
    "estéis", "estén", "estés", "fue", "fuera", "fuerais", "fueran", "fueras",
    "fueron", "fuese", "fueseis", "fuesen", "fueses", "fui", "fuimos", "fuiste",
    "fuisteis", "fuéramos", "fuésemos", "ha", "habida", "habidas", "habido", "habidos",
    "habiendo", "habremos", "habrá", "habrán", "habrás", "habré", "habréis", "habría",
    "habríais", "habríamos", "habrían", "habrías", "habéis", "había", "habíais",
    "habíamos", "habían", "habías", "han", "has", "hasta", "hay", "haya", "hayamos",
    "hayan", "hayas", "hayáis", "he", "hemos", "hube", "hubiera", "hubierais",
    "hubieran", "hubieras", "hubieron", "hubiese", "hubieseis", "hubiesen", "hubieses",
    "hubimos", "hubiste", "hubisteis", "hubiéramos", "hubiésemos", "hubo", "la", "las",
    "le", "les", "lo", "los", "me", "mi", "mis", "mucho", "muchos", "muy", "más",
    "mí", "mía", "mías", "mío", "míos", "nada", "ni", "no", "nos", "nosotras",
    "nosotros", "nuestra", "nuestras", "nuestro", "nuestros", "o", "os", "otra",
    "otras", "otro", "otros", "para", "pero", "poco", "por", "porque", "que", "quien",
    "quienes", "qué", "se", "sea", "seamos", "sean", "seas", "seremos", "será",
    "serán", "serás", "seré", "seréis", "sería", "seríais", "seríamos", "serían",
    "serías", "seáis", "sido", "siendo", "sin", "sobre", "sois", "somos", "son", "soy",
    "su", "sus", "suya", "suyas", "suyo", "suyos", "sí", "también", "tanto", "te",
    "tendremos", "tendrá", "tendrán", "tendrás", "tendré", "tendréis", "tendría",
    "tendríais", "tendríamos", "tendrían", "tendrías", "tened", "tenemos", "tenga",
    "tengamos", "tengan", "tengas", "tengo", "tengáis", "tenida", "tenidas", "tenido",
    "tenidos", "teniendo", "tenéis", "tenía", "teníais", "teníamos", "tenían",
    "tenías", "ti", "tiene", "tienen", "tienes", "todo", "todos", "tu", "tus", "tuve",
    "tuviera", "tuvierais", "tuvieran", "tuvieras", "tuvieron", "tuviese", "tuvieseis",
    "tuviesen", "tuvieses", "tuvimos", "tuviste", "tuvisteis", "tuviéramos",
    "tuviésemos", "tuvo", "tuya", "tuyas", "tuyo", "tuyos", "tú", "un", "una", "uno",
    "unos", "vosotras", "vosotros", "vuestra", "vuestras", "vuestro", "vuestros", "y",
    "ya", "yo", "él", "éramos"
]

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

def leer_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file)
    contenido = ""
    for page in pdf_reader.pages:
        contenido += page.extract_text()
    return contenido

def procesar_candidatura(candidatura_texto, empleos_df):
    empleos_df = empleos_df.astype(str)
    
    columnas = ['Formación', 'Conocimientos', 'Experiencia', 'Funciones', 'Localidad', 'Provincia', 'Modalidad', 'Tipo de jornada', 'Tipo de contrato', 'Idiomas', 'Nombre', 'campo_1']
    for columna in columnas:
        if columna not in empleos_df.columns:
            empleos_df[columna] = ''
    
    empleos_df['texto_oferta'] = empleos_df['Formación'] + ' ' + empleos_df['Conocimientos'] + ' ' + empleos_df['Experiencia'] + ' ' + empleos_df['Funciones'] + ' ' + empleos_df['Localidad'] + ' ' + empleos_df['Provincia'] + ' ' + empleos_df['Modalidad'] + ' ' + empleos_df['Tipo de jornada'] + ' ' + empleos_df['Tipo de contrato'] + ' ' + empleos_df['Idiomas'] + ' ' + empleos_df['Nombre'] + ' ' + empleos_df['campo_1']

    tfidf = TfidfVectorizer(stop_words=SPANISH_STOPWORDS)

    X_ofertas = tfidf.fit_transform(empleos_df['texto_oferta'])
    X_perfil = tfidf.transform([candidatura_texto])

    cosine_sims = cosine_similarity(X_perfil, X_ofertas)

    empleos_df['similitud'] = cosine_sims.flatten()
    empleos_df = empleos_df.sort_values('similitud', ascending=False)

    top_5_ofertas = empleos_df.head(5)

    st.table(top_5_ofertas[['Nombre', 'similitud', 'campo_1']])

# Autenticación
def check_password():
    def password_entered():
        if st.session_state["username"] == "einnova_python_development" and st.session_state["password"] == "scripts_python-ID274":
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Usuario", key="username")
        st.text_input("Contraseña", type="password", key="password")
        st.button("Iniciar sesión", on_click=password_entered)
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Usuario", key="username")
        st.text_input("Contraseña", type="password", key="password")
        st.button("Iniciar sesión", on_click=password_entered)
        st.error("😕 Usuario o contraseña incorrectos")
        return False
    else:
        return True

if check_password():
    st.title("Candidatura de Trabajo")

    opcion = st.selectbox("Seleccione una opción", ["Subir archivo PDF", "Rellenar formulario"])

    if opcion == "Subir archivo PDF":
        file = st.file_uploader("Subir archivo PDF", type=["pdf"])
        if file is not None:
            contenido_pdf = leer_pdf(file)
            st.success("El archivo PDF ha sido procesado correctamente.")
            
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
                
                credentials_file = st.file_uploader("Subir archivo de credenciales JSON", type=["json"])
                if credentials_file is not None:
                    sheet_title = "MyNewSheets"
                    worksheet_title = "Hoja 1"
                    worksheet = open_google_sheet(credentials_file, sheet_title, worksheet_title)
                    if worksheet:
                        empleos_df = read_worksheet(worksheet)
                        procesar_candidatura(candidatura_texto, empleos_df)
