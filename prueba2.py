import pandas as pd          # Manejo y análisis de datos en estructuras tipo tabla (DataFrames)
import matplotlib.pyplot as plt  # Creación de gráficos estáticos (barras, pasteles, boxplots, etc.)
import seaborn as sns        # Visualización estadística avanzada y gráfica más estética sobre matplotlib
import numpy as np           # Cálculos numéricos y operaciones con arreglos, estadística básica
import streamlit as st       # Framework para crear aplicaciones web interactivas fácilmente
from scipy import stats      # Funciones estadísticas avanzadas como moda, pruebas, etc.
from fpdf import FPDF        # Generar documentos PDF desde Python, agregar texto e imágenes
import tempfile              # Crear archivos temporales para guardar imágenes o datos temporales
import os                    # Manejo de sistema de archivos (eliminar archivos temporales, rutas, etc.)
import re                    # Expresiones regulares para manipular y limpiar texto (ej. quitar emojis)
from PIL import Image        # Biblioteca Pillow para abrir y manejar imágenes (dimensiones, formatos)
from scipy.interpolate import make_interp_spline
import time

def burbuja_bot_animada(texto, contenedor, velocidad=0.04):
    espacio = contenedor
    respuesta = ""
    
    # Mientras escribe: solo texto plano con ▌
    for c in texto:
        respuesta += c
        espacio.markdown(f"""
        <div style='background-color:#2b2b2b; padding: 12px 15px; border-radius: 12px 12px 12px 0px;
                        margin-bottom:10px; border-left: 4px solid #00ffc8; color:#f1f1f1;
                        font-family: "Segoe UI", sans-serif; font-size: 14px; white-space: pre-wrap;'>
            🤖 <b>EduBot:</b><br>{respuesta}▌
        </div>
        """, unsafe_allow_html=True)
        time.sleep(velocidad)

    # Al finalizar: reemplazamos saltos de línea correctamente
    respuesta_final = texto.replace("\n", "<br>")
    espacio.markdown(f"""
    <div style='background-color:#2b2b2b; padding: 12px 15px; border-radius: 12px 12px 12px 0px;
                    margin-bottom:10px; border-left: 4px solid #00ffc8; color:#f1f1f1;
                    font-family: "Segoe UI", sans-serif; font-size: 14px;'>
        🤖 <b>EduBot:</b><br>{respuesta_final}
    </div>
    """, unsafe_allow_html=True)

# Cargar archivo Excel
df = pd.read_excel("Calificaciones 1 y 2 parcial Plantel Xonacatlán.xlsx")

# Configurar Streamlit
st.set_page_config(layout="wide", page_title="Análisis de Calificaciones")
st.markdown("""
<h1 style='font-family:Segoe UI, sans-serif; color:#00ffc8; font-weight:600;'>
📊 Análisis de Calificaciones por Asignatura
</h1>
<h4 style='color:#cccccc; font-family:Segoe UI, sans-serif; font-weight:400; margin-top:-10px;'>
Visualización y comparación de resultados por parcial
</h4>
""", unsafe_allow_html=True)

# Filtro de semestre
semestres = df["Semestre"].dropna().unique()
semestre_seleccionado = st.sidebar.selectbox("Selecciona un semestre", sorted(semestres))

# Filtro de carrera dinámico según semestre
carreras_filtradas = df[df["Semestre"] == semestre_seleccionado]["Carrera"].dropna().unique()
carrera_seleccionada = st.sidebar.selectbox("Selecciona una carrera", sorted(carreras_filtradas))

# Filtro de grupo dinámico según semestre y carrera
grupos_filtrados = df[
    (df["Semestre"] == semestre_seleccionado) &
    (df["Carrera"] == carrera_seleccionada)
]["Grupo"].dropna().unique()
grupo_seleccionado = st.sidebar.selectbox("Selecciona un grupo", sorted(grupos_filtrados))

# Filtrar el DataFrame base según todos los filtros
df_filtrado = df[
    (df["Semestre"] == semestre_seleccionado) &
    (df["Carrera"] == carrera_seleccionada) &
    (df["Grupo"] == grupo_seleccionado)
]

# Filtro de asignatura
todas_asignaturas = df_filtrado["Asignatura"].dropna().unique()
asignatura_seleccionada = st.sidebar.selectbox("Selecciona una asignatura", sorted(todas_asignaturas))

# Filtrado final
grupo_df = df_filtrado[df_filtrado["Asignatura"] == asignatura_seleccionada]

# Encabezado personalizado con estilo moderno
st.markdown(f"""
<style>
.encabezado-box {{
    background: linear-gradient(90deg, #1f1f1f, #2c2c2c);
    border-left: 5px solid #00ffd5;
    padding: 20px;
    border-radius: 10px;
    margin-bottom: 25px;
}}
.encabezado-box h4 {{
    color: #00ffd5;
    margin: 0;
    font-size: 20px;
}}

</style>

<div class="encabezado-box">
    <h4>🎓 Carrera: <span style='color:white'>{carrera_seleccionada}</span></h4>
    <h4>📘 Asignatura: <span style='color:white'>{asignatura_seleccionada}</span></h4>
    <h4>👥 Grupo: <span style='color:white'>{grupo_seleccionado}</span> | 🗓️ Semestre: <span style='color:white'>{semestre_seleccionado}</span></h4>
</div>
""", unsafe_allow_html=True)

# Colores para rangos (tonos suaves y agradables)
rango_colores = {
    '5-6': '#e74c3c',    # rojo suave (✅ excelente para calificaciones bajas)
    '6-7': '#e67e22',    # naranja quemado (✅ buen intermedio)
    '7-8': '#f1c40f',    # amarillo mostaza (🟡 un poco brillante, pero aceptable)
    '8-9': "#58a8d6",   # verde jade suave (más natural)
    '9-10': "#09ff6fcf"   # verde profesional profundo
}


rango_bins = [5, 6, 7, 8, 9, 10.1]
rango_labels = ['5-6', '6-7', '7-8', '8-9', '9-10']

calificaciones_dict = {}
estadisticas_dict = {}

cols = st.columns(2)  # Dividimos en 2 columnas horizontales

for idx, parcial in enumerate(['P1', 'P2']):
    calificaciones = grupo_df[parcial].dropna()
    calificaciones_dict[parcial] = calificaciones
    

    if calificaciones.empty:
        cols[idx].warning(f"⚠️ Estadísticas de {parcial}: No disponibles")
        continue   

    # Cálculos principales
    media = calificaciones.mean()
    mediana = calificaciones.median()
    moda = stats.mode(calificaciones, nan_policy='omit', keepdims=True)[0][0]
    varianza = calificaciones.var()
    q1 = calificaciones.quantile(0.25)
    q2 = calificaciones.quantile(0.50)
    q3 = calificaciones.quantile(0.75)

    # Cálculos adicionales por que yo lo digo jaja xd 
    maximo = calificaciones.max()
    minimo = calificaciones.min()
    rango = maximo - minimo
    total = calificaciones.count()

     # ✅ Luego de lso calculos los guardamos en el diccionario
    estadisticas_dict[parcial] = {
        "media": media,
        "mediana": mediana,
        "moda": moda,
        "varianza": varianza,
        "q1": q1,
        "q2": q2,
        "q3": q3,
        "max": maximo,
        "min": minimo,
        "rango": rango,
        "total": total
    }
    # HTML con estilos para las tablas
    tabla_html = f"""
    <style>
        .tabla-estadisticas {{
            border-collapse: separate;
            border-spacing: 0;
            width: 100%;
            margin-top: 15px;
            font-family: 'Segoe UI', sans-serif;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,255,200,0.1);
        }}
        .tabla-estadisticas th {{
            background-color: #1f1f1f;
            color: #00ffd5;
            text-align: left;
            padding: 12px 16px;
            font-size: 14px;
            border-bottom: 2px solid #00ffd5;
        }}
        .tabla-estadisticas td {{
            background-color: #121212;
            color: #f1f1f1;
            padding: 12px 16px;
            font-size: 13.5px;
            border-bottom: 1px solid #2a2a2a;
        }}
        .tabla-estadisticas tr:hover td {{
            background-color: #1c1c1c;
        }}
    </style>

    <h4 style='color:#00ffd5; font-family:Segoe UI;'>📘 Estadísticas del {parcial}</h4>

    <table class="tabla-estadisticas">
        <thead>
            <tr>
                <th>📌 Medida</th>
                <th>🔢 Valor</th>
            </tr>
        </thead>
        <tbody>
            <tr><td>Total de Alumnos</td><td>{total}</td></tr>
            <tr><td>Media</td><td>{media:.2f}</td></tr>
            <tr><td>Mediana</td><td>{mediana:.2f}</td></tr>
            <tr><td>Moda</td><td>{moda:.2f}</td></tr>
            <tr><td>Varianza</td><td>{varianza:.2f}</td></tr>
            <tr><td>Rango</td><td>{rango:.2f}</td></tr>
            <tr><td>Q1 (25%)</td><td>{q1:.2f}</td></tr>
            <tr><td>Q2 (50%)</td><td>{q2:.2f}</td></tr>
            <tr><td>Q3 (75%)</td><td>{q3:.2f}</td></tr>
        </tbody>
    </table>
    """

    # Mostrar la tabla en su columna correspondiente
    cols[idx].markdown(tabla_html, unsafe_allow_html=True)
    
# INICIO DEL BOT CON SESSION STATE
if 'bot_activado' not in st.session_state:
    st.session_state.bot_activado = False
if 'pregunta' not in st.session_state:
    st.session_state.pregunta = ""
if 'bienvenida_mostrada' not in st.session_state:
    st.session_state.bienvenida_mostrada = False
if 'sugerencia' not in st.session_state:
    st.session_state.sugerencia = ""
if 'mostrar_bienvenida_texto' not in st.session_state:
    st.session_state.mostrar_bienvenida_texto = True  # 👈 NUEVO CONTROL

# ACTIVAR BOT
st.session_state.bot_activado = st.sidebar.checkbox("💬 Mostrar EduBot", value=st.session_state.bot_activado)

if st.session_state.bot_activado:

    # Mostrar bienvenida con efecto de carga solo UNA vez
    if not st.session_state.bienvenida_mostrada:
        st.sidebar.markdown("""
        <div style='background: linear-gradient(to right, #1a1a1a, #212121); padding: 20px; border-radius: 14px; 
                    box-shadow: 0 4px 12px rgba(0,0,0,0.3); border-left: 6px solid #00ffc8; margin-bottom: 15px;'>
            <h3 style='color:#00ffc8; font-family:Segoe UI;'>🤖 EduBot</h3>
            <p style='color:#f1f1f1; font-size:14px; line-height:1.5; font-family:Segoe UI;'>
                Iniciando sesión segura...<br>Preparando respuestas inteligentes...
            </p>
        </div>
        """, unsafe_allow_html=True)
        time.sleep(2)
        st.session_state.bienvenida_mostrada = True
        st.experimental_rerun()

    with st.sidebar:
        if st.session_state.mostrar_bienvenida_texto:
            contenedor = st.empty()
            burbuja_bot_animada("Bienvenido/a al sistema de análisis 📊. Estoy listo para ayudarte con estadísticas. Te dejo algunas sugerencias:", contenedor)
            st.session_state.mostrar_bienvenida_texto = False  # 👈 Se muestra una sola vez
        st.markdown("---")

    # Botones de sugerencia
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("📊 Media"):
            st.session_state.sugerencia = "¿Cuál es la media?"
            st.session_state.pregunta = st.session_state.sugerencia
        if st.button("📈 Mediana"):
            st.session_state.sugerencia = "¿Cuál es la mediana?"
            st.session_state.pregunta = st.session_state.sugerencia
        if st.button("📦 Boxplot"):
            st.session_state.sugerencia = "¿Qué es un boxplot?"
            st.session_state.pregunta = st.session_state.sugerencia
    with col2:
        if st.button("📌 Moda"):
            st.session_state.sugerencia = "¿Cuál es la moda?"
            st.session_state.pregunta = st.session_state.sugerencia
        if st.button("📉 Varianza"):
            st.session_state.sugerencia = "¿Qué es la varianza?"
            st.session_state.pregunta = st.session_state.sugerencia
        if st.button("📐 Rango IQR"):
            st.session_state.sugerencia = "¿Qué es el rango intercuartil (IQR)?"
            st.session_state.pregunta = st.session_state.sugerencia

        entrada_usuario = st.sidebar.text_input("✏️ Escribe tu pregunta:", value=st.session_state.pregunta, key="input_pregunta")

    if entrada_usuario != st.session_state.pregunta:
        st.session_state.pregunta = entrada_usuario

    # Mostrar respuesta si hay pregunta
    if st.session_state.pregunta.strip():
        pregunta = st.session_state.pregunta.lower()

        # 🧠 Spinner de EduBot dentro del sidebar
        with st.sidebar:
            with st.spinner("EduBot está escribiendo... ✍️"):
                time.sleep(1.2)

        if "media" in pregunta:
            p1 = estadisticas_dict['P1']['media']
            p2 = estadisticas_dict['P2']['media']

            # Armar el mensaje completo como un solo string
            respuesta = (
                "📊 Media\n"
                "La media es el promedio de todas las calificaciones.\n"
                f"🟢 P1: {p1:.2f}\n"
                f"🔵 P2: {p2:.2f}\n"
            )

            if p2 > p1:
                respuesta += "📈 Conclusión: La media subió."
            elif p2 < p1:
                respuesta += "📉 Conclusión: La media bajó."
            else:
                respuesta += "➖ Conclusión: La media se mantuvo igual."

            # Mostrar todo como una sola burbuja
            with st.sidebar:
                contenedor = st.empty()
                burbuja_bot_animada(respuesta, contenedor)

        elif "moda" in pregunta:
            p1 = estadisticas_dict['P1']['moda']
            p2 = estadisticas_dict['P2']['moda']

            respuesta = (
                "📌 Moda\n"
                "La moda es el valor que más se repite. Si cambia entre parciales, indica un cambio en las calificaciones más comunes.\n"
                f"🟢 P1: {p1:.2f}\n"
                f"🔵 P2: {p2:.2f}\n"
            )

            if p2 > p1:
                respuesta += "📈 Conclusión: La moda subió, los valores más frecuentes fueron más altos en P2."
            elif p2 < p1:
                respuesta += "📉 Conclusión: La moda bajó, los valores más repetidos fueron más bajos en P2."
            else:
                respuesta += "➖ Conclusión: La moda se mantuvo igual en ambos parciales."

            with st.sidebar:
                burbuja_bot_animada(respuesta, st.empty())

        elif "mediana" in pregunta:
            p1 = estadisticas_dict['P1']['mediana']
            p2 = estadisticas_dict['P2']['mediana']

            respuesta = (
                "📈 Mediana\n"
                "Divide los datos ordenados por la mitad. Menos sensible a extremos que la media.\n"
                f"🟢 P1: {p1:.2f}\n"
                f"🔵 P2: {p2:.2f}\n"
            )

            if p2 > p1:
                respuesta += "📈 Conclusión: La mediana subió, los valores más frecuentes fueron más altos en P2."
            elif p2 < p1:
                respuesta += "📉 Conclusión: La mediana bajó, los valores más repetidos fueron más bajos en P2."
            else:
                respuesta += "➖ Conclusión: La mediana se mantuvo igual en ambos parciales."

            with st.sidebar:
                burbuja_bot_animada(respuesta, st.empty())

        elif "rango" in pregunta:
            p1 = estadisticas_dict['P1']['rango']
            p2 = estadisticas_dict['P2']['rango']

            respuesta = (
                "📏 Rango (Máx - Mín)\n"
                "El rango muestra qué tan dispersas están las calificaciones, comparando la más alta con la más baja.\n"
                f"🟢 P1: {p1:.2f}\n"
                f"🔵 P2: {p2:.2f}\n"
            )

            if p2 > p1:
                respuesta += "📈 Conclusión: Aumentó el rango en P2, hay mayor variabilidad entre los alumnos."
            elif p2 < p1:
                respuesta += "📉 Conclusión: Disminuyó el rango en P2, las calificaciones fueron más homogéneas."
            else:
                respuesta += "➖ Conclusión: El rango se mantuvo igual, la dispersión fue la misma."

            with st.sidebar:
                burbuja_bot_animada(respuesta, st.empty())

        elif "q1" in pregunta or "cuartil 1" in pregunta:
            p1 = estadisticas_dict['P1']['q1']
            p2 = estadisticas_dict['P2']['q1']

            respuesta = (
                "🟪 Q1 (Primer Cuartil - 25%)\n"
                "El 25% de las calificaciones están por debajo de este valor. Útil para ver el rendimiento más bajo.\n"
                f"🟢 P1: {p1:.2f}\n"
                f"🔵 P2: {p2:.2f}\n"
            )

            if p2 > p1:
                respuesta += "📈 Conclusión: El Q1 subió en P2, los alumnos con menor rendimiento mejoraron."
            elif p2 < p1:
                respuesta += "📉 Conclusión: El Q1 bajó, hubo menor rendimiento en el 25% inferior."
            else:
                respuesta += "➖ Conclusión: El Q1 se mantuvo igual, sin cambios en el grupo de menor rendimiento."

            with st.sidebar:
                burbuja_bot_animada(respuesta, st.empty())

        elif "q2" in pregunta or "cuartil 2" in pregunta:
            p1 = estadisticas_dict['P1']['q2']
            p2 = estadisticas_dict['P2']['q2']

            respuesta = (
                "🔵 Q2 (Mediana - 50%)\n"
                "Mitad de alumnos sacó menos y mitad más que este valor. Es menos sensible a valores extremos.\n"
                f"🟢 P1: {p1:.2f}\n"
                f"🔵 P2: {p2:.2f}\n"
            )

            if p2 > p1:
                respuesta += "📈 Conclusión: El Q2 subió, mejoró el rendimiento medio."
            elif p2 < p1:
                respuesta += "📉 Conclusión: El Q2 bajó, el rendimiento medio fue más bajo."
            else:
                respuesta += "➖ Conclusión: El Q2 se mantuvo igual, sin cambios en la mediana."

            with st.sidebar:
                burbuja_bot_animada(respuesta, st.empty())

        elif "q3" in pregunta or "cuartil 3" in pregunta:
            p1 = estadisticas_dict['P1']['q3']
            p2 = estadisticas_dict['P2']['q3']

            respuesta = (
                "🟥 Q3 (Tercer Cuartil - 75%)\n"
                "El 75% de los alumnos sacó menos o igual que este valor. Mide el rendimiento del grupo superior.\n"
                f"🟢 P1: {p1:.2f}\n"
                f"🔵 P2: {p2:.2f}\n"
            )

            if p2 > p1:
                respuesta += "📈 Conclusión: El Q3 subió, el grupo alto mejoró aún más."
            elif p2 < p1:
                respuesta += "📉 Conclusión: El Q3 bajó, el grupo alto tuvo menor rendimiento."
            else:
                respuesta += "➖ Conclusión: El Q3 se mantuvo igual, sin cambios en el grupo con mejores notas."

            with st.sidebar:
                burbuja_bot_animada(respuesta, st.empty())
                
        elif "iqr" in pregunta or "rango intercuartilico" in pregunta or "rango intercuartílico" in pregunta:
            p1_q1 = estadisticas_dict['P1']['q1']
            p1_q3 = estadisticas_dict['P1']['q3']
            p2_q1 = estadisticas_dict['P2']['q1']
            p2_q3 = estadisticas_dict['P2']['q3']

            iqr_p1 = p1_q3 - p1_q1
            iqr_p2 = p2_q3 - p2_q1

            respuesta = (
                "📏 IQR - Rango Intercuartílico\n"
                "Es la diferencia entre el tercer cuartil (Q3) y el primero (Q1). Representa la dispersión del 50% central de los datos.\n"
                f"🟩 P1: {iqr_p1:.2f}\n"
                f"🟦 P2: {iqr_p2:.2f}\n"
            )

            if iqr_p2 < iqr_p1:
                respuesta += "✅ Conclusión: La dispersión disminuyó en P2. Las calificaciones están más concentradas."
            elif iqr_p2 > iqr_p1:
                respuesta += "⚠️ Conclusión: La dispersión aumentó en P2. Hubo más variación entre los alumnos."
            else:
                respuesta += "➖ Conclusión: El IQR se mantuvo igual. La concentración de calificaciones no cambió."

            with st.sidebar:
                burbuja_bot_animada(respuesta, st.empty())
                
        elif "total" in pregunta or "alumnos" in pregunta:
            p1 = estadisticas_dict['P1']['total']
            p2 = estadisticas_dict['P2']['total']

            respuesta = (
                "👥 Total de alumnos con calificación registrada\n"
                "Refleja cuántos estudiantes fueron evaluados en cada parcial. Las diferencias pueden deberse a inasistencias, faltas de entrega o errores en la captura de datos.\n"
                f"🟢 P1: {p1}\n"
                f"🔵 P2: {p2}\n"
            )

            if p2 > p1:
                respuesta += "📈 Conclusión: Más alumnos fueron evaluados en el segundo parcial."
            elif p2 < p1:
                respuesta += "📉 Conclusión: Menos alumnos tienen calificación en P2. Puede indicar ausencias o datos faltantes."
            else:
                respuesta += "➖ Conclusión: El número de alumnos evaluados se mantuvo igual en ambos parciales."

            with st.sidebar:
                burbuja_bot_animada(respuesta, st.empty())
                
        elif "varianza" in pregunta:
            p1 = estadisticas_dict['P1']['varianza']
            p2 = estadisticas_dict['P2']['varianza']

            respuesta = (
                "📉 Varianza\n"
                "Mide la dispersión de las calificaciones con respecto a la media. Valores altos indican más variabilidad.\n"
                f"🟢 P1: {p1:.2f}\n"
                f"🔵 P2: {p2:.2f}\n"
            )

            if p2 > p1:
                respuesta += "⚠️ Conclusión: La varianza aumentó en P2, mayor dispersión entre los alumnos."
            elif p2 < p1:
                respuesta += "✅ Conclusión: La varianza disminuyó en P2, las calificaciones están más concentradas."
            else:
                respuesta += "➖ Conclusión: La varianza se mantuvo igual en ambos parciales."

            with st.sidebar:
                burbuja_bot_animada(respuesta, st.empty())

        elif "boxplot" in pregunta:
            respuesta = (
                "📦 Boxplot\n"
                "Gráfico que muestra la distribución de calificaciones, destacando mediana, cuartiles y posibles valores atípicos.\n"
                "Es útil para visualizar la dispersión y detectar datos extremos.\n"
                "Para más detalles, revisa las gráficas generadas en el panel principal."
            )
            with st.sidebar:
                burbuja_bot_animada(respuesta, st.empty())

        elif "pdf" in pregunta or "descargar" in pregunta:
            with st.sidebar:
                burbuja_bot_animada("📄 Puedes generar un PDF con las gráficas y estadísticas actuales usando el botón que aparece al final del análisis.", st.empty())
        else:
            with st.sidebar:
                burbuja_bot_animada("❓ No entendí la pregunta. Puedes intentar con: media, moda, varianza, IQR, PDF, etc.", st.empty())

# ----------- Histograma  ------------------
st.markdown(f"## 📘 <b>Análisis de {asignatura_seleccionada}</b>", unsafe_allow_html=True)

fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.patch.set_facecolor('#121212')  # fondo oscuro

for idx, parcial in enumerate(['P1', 'P2']):
    calificaciones = calificaciones_dict[parcial]
    if calificaciones.empty:
        axes[idx].set_title(f'{parcial} - Sin datos', color='white')
        axes[idx].axis('off')
        continue

    conteo, _ = np.histogram(calificaciones, bins=rango_bins)
    total = len(calificaciones)
    porcentajes = (conteo / total) * 100

    axes[idx].set_facecolor('#121212')  # fondo oscuro subplot
    #solo si es recta la linea 
    #axes[idx].plot(x_vals, conteo, color='cyan', linewidth=2, marker='o', linestyle='-', label='Tendencia')
    #comienza la linea curva
    barras = axes[idx].bar(rango_labels, conteo, color=[rango_colores[label] for label in rango_labels])
    x_vals = np.arange(len(rango_labels))
    x_new = np.linspace(x_vals.min(), x_vals.max(), 300) 
    spl = make_interp_spline(x_vals, conteo, k=3)  # k=3 es spline cúbica
    conteo_smooth = spl(x_new)
    # Dibujar la curva suave
    # Capa inferior como "sombra"
    axes[idx].plot(x_new, conteo_smooth, color='deepskyblue', linewidth=3)

    # Capa superior real
    axes[idx].plot(x_new, conteo_smooth, color="#7230c9", linewidth=3, label='tendencia')
    #termina la de la curva xd 
    
    # Porcentajes encima de cada barra
    for bar, pct in zip(barras, porcentajes):
        height = bar.get_height()
        axes[idx].text(bar.get_x() + bar.get_width()/2, height + 0.3,
                       f'{pct:.1f}%', ha='center', color='white', fontsize=10, fontweight='bold')

    axes[idx].set_title(f'Histograma {parcial}', color='white', fontsize=16, fontweight='bold')
    axes[idx].set_xlabel('Rango', color='white', fontsize=12)
    axes[idx].set_ylabel('Frecuencia', color='white', fontsize=12)
    axes[idx].tick_params(colors='white')  # ticks blancos
    #la esa barrita de tendencia xd 
    axes[idx].legend(facecolor='#121212', edgecolor='white', labelcolor='white')


plt.tight_layout()
st.pyplot(fig)

# Aquí agregas la explicación/comparativa abajo de la gráfica
with st.expander("📋 Ver análisis del histograma ⬇️"):
    st.markdown("""
    - El histograma nos muestra la frecuencia de calificaciones por rango para ambos parciales.
    - Puedes observar cómo se distribuyen las calificaciones en P1 y P2, y si hubo cambios en la concentración o dispersión.
    """)

    # Ejemplo conclusión simple con media para agregar info extra:
    p1_media = estadisticas_dict['P1']['media']
    p2_media = estadisticas_dict['P2']['media']

    if p2_media > p1_media:
        st.success("✅ La media en P2 aumentó, lo que indica una mejora general en las calificaciones.")
    elif p2_media < p1_media:
        st.warning("⚠️ La media en P2 disminuyó, lo que podría indicar un rendimiento más bajo.")
    else:
        st.info("➖ La media se mantuvo estable entre ambos parciales.")

# ------------------ Gráfica de pastel -------------------
st.markdown(f"## 📘 <b>Análisis de {asignatura_seleccionada}</b>", unsafe_allow_html=True)

# Contenedor de dos columnas paralelas (una para cada parcial)
col1, col2 = st.columns(2)

for idx, parcial in enumerate(['P1', 'P2']):
    col = col1 if idx == 0 else col2  # Selecciona columna actual
    calificaciones = calificaciones_dict[parcial]
    
    if calificaciones.empty:
        col.markdown(f"### {parcial} - Sin datos")
        continue

    # -------- Prepara datos --------
    ranges = pd.cut(calificaciones, bins=rango_bins, labels=rango_labels, right=False)
    conteo = ranges.value_counts(sort=False)
    valores = conteo.values
    etiquetas = conteo.index.tolist()
    colores = [rango_colores[label] for label in etiquetas]
    total = valores.sum()
    porcentajes = valores / total * 100

    # -------- Crear figura para este parcial --------
    fig, ax = plt.subplots(figsize=(6, 6), facecolor='#121212')
    ax.set_facecolor('#121212')

    ax.pie(
        valores,
        labels=None,           # sin etiquetas
        autopct=None,          # sin porcentaje
        startangle=90,
        colors=colores,
        wedgeprops={'edgecolor': '#121212', 'linewidth': 1.5}
    )

    ax.set_title(f"Distribución - {parcial}", color='white', fontsize=15, fontweight='bold')

    # Mostrar gráfica
    col.pyplot(fig)

    # -------- Tabla debajo de gráfica --------
    tabla = "<table style='color:white; font-size:13px; font-weight:normal;'>"
    tabla += "<tr><th style='text-align:left;'>🎨</th><th style='text-align:left;'>Rango</th><th style='text-align:right;'>%</th></tr>"
    for c, r, p in zip(colores, etiquetas, porcentajes):
        tabla += f"<tr>" \
                 f"<td><div style='width:18px; height:18px; background:{c}; border-radius:4px; box-shadow: 0 0 3px {c};'></div></td>" \
                 f"<td style='padding-left:10px;'>{r}</td>" \
                 f"<td style='text-align:right;'>{p:.1f}%</td>" \
                 f"</tr>"
    tabla += "</table>"

    col.markdown(tabla, unsafe_allow_html=True)

# Guardar las variables para el PDF
colores_pie1 = [rango_colores[label] for label in pd.cut(calificaciones_dict['P1'], bins=rango_bins, labels=rango_labels, right=False).value_counts(sort=False).index.tolist()]
etiquetas_pie1 = rango_labels
valores1 = pd.cut(calificaciones_dict['P1'], bins=rango_bins, labels=rango_labels, right=False).value_counts(sort=False).values
porcentajes_pie1 = valores1 / valores1.sum() * 100

colores_pie2 = [rango_colores[label] for label in pd.cut(calificaciones_dict['P2'], bins=rango_bins, labels=rango_labels, right=False).value_counts(sort=False).index.tolist()]
etiquetas_pie2 = rango_labels
valores2 = pd.cut(calificaciones_dict['P2'], bins=rango_bins, labels=rango_labels, right=False).value_counts(sort=False).values
porcentajes_pie2 = valores2 / valores2.sum() * 100

with st.expander("🥧 Análisis de la Gráfica de Distribución ⬇️"):
    st.markdown("""
    - Las gráficas de pastel muestran la proporción de alumnos en cada rango de calificación para P1 y P2.
    - Permiten visualizar fácilmente qué porcentaje de alumnos está en rangos altos, medios o bajos.
    - Sirven para comparar la distribución de calificaciones entre ambos parciales y detectar mejoras o retrocesos.
    """)

    # Ejemplo conclusión simple basada en la proporción de aprobados (>= 60)
    p1_aprobados = calificaciones_dict['P1'][calificaciones_dict['P1'] >= 60].count()
    p2_aprobados = calificaciones_dict['P2'][calificaciones_dict['P2'] >= 60].count()
    total_p1 = estadisticas_dict['P1']['total']
    total_p2 = estadisticas_dict['P2']['total']

    porc_aprobados_p1 = (p1_aprobados / total_p1)*100 if total_p1 > 0 else 0
    porc_aprobados_p2 = (p2_aprobados / total_p2)*100 if total_p2 > 0 else 0

    if porc_aprobados_p2 > porc_aprobados_p1:
        st.success(f"✅ La proporción de alumnos aprobados aumentó de {porc_aprobados_p1:.1f}% en P1 a {porc_aprobados_p2:.1f}% en P2.")
    elif porc_aprobados_p2 < porc_aprobados_p1:
        st.warning(f"⚠️ La proporción de alumnos aprobados disminuyó de {porc_aprobados_p1:.1f}% en P1 a {porc_aprobados_p2:.1f}% en P2.")
    else:
        st.info(f"➖ La proporción de alumnos aprobados se mantuvo estable en {porc_aprobados_p1:.1f}%.")

# ----------- Boxplot ------------------
st.markdown(f"## 📘 <b>Análisis de {asignatura_seleccionada}</b>", unsafe_allow_html=True)

if not grupo_df[['P1', 'P2']].dropna(how='all').empty:
    fig, ax = plt.subplots(figsize=(7.5, 5.5), facecolor='#121212')
    fig.patch.set_facecolor('#121212')  # Fondo global oscuro

    # --- BOXPLOT ---
    sns.boxplot(
        data=grupo_df[['P1', 'P2']],
        palette=['#e63946', '#06d6a0'],  # Rojo coral y verde menta
        width=0.4,
        linewidth=2.2,
        fliersize=0,
        ax=ax
    )

    # --- STRIP PLOT para puntos individuales ---
    sns.stripplot(
        data=grupo_df[['P1', 'P2']],
        jitter=0.25,
        dodge=True,
        size=6,
        color='white',
        alpha=0.5,
        ax=ax
    )

    # --- Ejes y fondo ---
    ax.set_facecolor('#121212')
    ax.tick_params(colors='white', labelsize=12)
    ax.set_ylabel('Calificación', color='#f1f1f1', fontsize=13)
    ax.set_xlabel('', color='white')

    # --- Borde blanco ---
    for spine in ax.spines.values():
        spine.set_color('white')
        spine.set_linewidth(1.3)

    # --- Grid sutil en Y ---
    ax.yaxis.grid(True, linestyle='--', linewidth=0.6, color='gray', alpha=0.3)
    ax.set_axisbelow(True)

    st.pyplot(fig)
else:
    st.warning("⚠️ No hay suficientes datos para mostrar el análisis boxplot.")

# Explicación principal resumida
with st.expander("📦 Análisis del Diagrama de Caja (Boxplot) ⬇️"):
    st.markdown("""
    ### 🧠 Interpretación del boxplot
    - 📏 La **línea central** representa la mediana (valor medio de las calificaciones).
    - 📦 El **cuerpo de la caja** abarca el rango intercuartílico (del primer al tercer cuartil, Q1 a Q3).
    - 📉 Los **bigotes** muestran el rango típico de los datos, excluyendo valores atípicos.
    - 🔹 Los **puntos individuales** representan calificaciones atípicas o muy alejadas de la media.

    ---

    ### 📈 Aplicación en el análisis académico
    - 📊 El boxplot permite observar la **distribución y variabilidad** de las calificaciones por parcial.
    - 🔍 Comparar los boxplots de P1 y P2 permite identificar **cambios en el rendimiento**.
    - ✅ Una **caja más compacta** o **menores bigotes en P2** sugiere una mejora en la **consistencia académica** del grupo.
    """)

    # Comparación de IQR
    p1_q1 = estadisticas_dict['P1']['q1']
    p1_q3 = estadisticas_dict['P1']['q3']
    p2_q1 = estadisticas_dict['P2']['q1']
    p2_q3 = estadisticas_dict['P2']['q3']

    iqr_p1 = p1_q3 - p1_q1
    iqr_p2 = p2_q3 - p2_q1

    if iqr_p2 < iqr_p1:
        st.success("✅ La dispersión (IQR) disminuyó en P2, indicando mayor concentración de calificaciones.")
    elif iqr_p2 > iqr_p1:
        st.warning("⚠️ La dispersión (IQR) aumentó en P2, lo que indica más variabilidad en el grupo.")
    else:
        st.info("➖ La dispersión (IQR) se mantuvo estable entre ambos parciales.")

    # Comparación de medianas
    p1_mediana = estadisticas_dict['P1']['mediana']
    p2_mediana = estadisticas_dict['P2']['mediana']

    if p2_mediana > p1_mediana:
        st.success("✅ La mediana aumentó en P2, lo cual sugiere una mejora general en el rendimiento.")
    elif p2_mediana < p1_mediana:
        st.warning("⚠️ La mediana disminuyó en P2, lo que podría reflejar un menor rendimiento.")
    else:
        st.info("➖ La mediana se mantuvo igual entre ambos parciales.")

with st.expander("👨‍💻 Créditos del Proyecto — Equipo 603"):
    st.markdown("""
    <style>
    .footer-container {
        background: #1f1f1f;
        padding: 20px;
        border-radius: 12px;
        color: #f1f1f1;
        font-family: 'Segoe UI', sans-serif;
        font-size: 14px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    .footer-title {
        font-size: 18px;
        font-weight: bold;
        margin-bottom: 10px;
        color: #00ffc8;
    }
    .footer-list {
        list-style: none;
        padding-left: 0;
        margin: 0 0 10px 0;
    }
    .footer-list li {
        padding: 4px 0;
        border-bottom: 1px dashed #333;
    }
    .footer-links a {
        color: #00ffc8;
        text-decoration: none;
        margin-right: 10px;
        transition: color 0.3s ease;
    }
    .footer-links a:hover {
        color: #fff;
    }
    </style>
    
    <div class='footer-container'>
        <div class='footer-title'>Equipo 603 - Desarrolladores</div>
        <ul class='footer-list'>
            <li>Axel Morales</li>
            <li>Itzel Taneli Hernández Salinas</li>
            <li>Thalia Ramos García</li>
            <li>Brizza Lizeht Gómez Gracia</li>
        </ul>
        <div class='footer-links'>
            🌐 <a href='https://github.com/equipo603' target='_blank'>GitHub</a>
            💼 <a href='https://linkedin.com/in/equipo603' target='_blank'>LinkedIn</a>
            🖼️ <a href='https://portafolio603.com' target='_blank'>Portafolio</a>
        </div>
        <div style='margin-top:12px;'>📅 Proyecto 2 — <i>Análisis de Calificaciones</i>, 2025</div>
    </div>
    """, unsafe_allow_html=True)
            
# Función para quitar emojis (¡clave para evitar errores!)
def quitar_emojis(texto):
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticonos
        u"\U0001F300-\U0001F5FF"  # símbolos y pictogramas
        u"\U0001F680-\U0001F6FF"  # transporte y mapas
        u"\U0001F1E0-\U0001F1FF"  # banderas
        u"\U00002700-\U000027BF"
        u"\U0001F900-\U0001F9FF"
        u"\U0001FA70-\U0001FAFF"
        "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', texto)

#--------------Creación del PDF sin errores de emoji----------------
def generar_pdf(calificaciones_dict, carrera, grupo, asignatura, semestre,
                colores_pies=None, etiquetas_pies=None, porcentajes_pies=None):

    pdf = FPDF(orientation='P', unit='mm', format='A4')
    
    def poner_fondo_negro():
        pdf.set_fill_color(0, 0, 0)
        pdf.rect(0, 0, 210, 297, 'F')

    def quitar_emojis(texto):
        return texto.encode('ascii', 'ignore').decode('ascii')

    # Primera página - encabezado y estadísticas
    pdf.add_page()
    poner_fondo_negro()
    pdf.set_text_color(0, 255, 213)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, quitar_emojis("Reporte de Calificaciones"), ln=True, align='C')

    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", '', 12)
    pdf.ln(5)
    encabezado = f"Carrera: {carrera} | Asignatura: {asignatura} | Grupo: {grupo} | Semestre: {semestre}"
    pdf.cell(0, 10, quitar_emojis(encabezado), ln=True)

    for parcial, calificaciones in calificaciones_dict.items():
        if calificaciones.empty:
            continue
        pdf.set_text_color(0, 255, 213)
        pdf.set_font("Arial", 'B', 12)
        pdf.ln(8)
        pdf.cell(0, 10, quitar_emojis(f"Estadísticas de {parcial}"), ln=True)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Arial", '', 11)

        moda_resultado = stats.mode(calificaciones, nan_policy='omit', keepdims=True)
        moda_valor = moda_resultado.mode[0] if len(moda_resultado.mode) > 0 else np.nan

        pdf.cell(0, 8, f"Media: {calificaciones.mean():.2f}", ln=True)
        pdf.cell(0, 8, f"Mediana: {calificaciones.median():.2f}", ln=True)
        pdf.cell(0, 8, f"Moda: {moda_valor:.2f}", ln=True)
        pdf.cell(0, 8, f"Varianza: {calificaciones.var():.2f}", ln=True)
        pdf.cell(0, 8, f"Rango: {calificaciones.max() - calificaciones.min():.2f}", ln=True)

    # Guardar gráficas como imágenes temporales
    img_paths = []
    for fig_num in plt.get_fignums():
        fig = plt.figure(fig_num)
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        fig.savefig(temp_file.name, bbox_inches='tight')
        img_paths.append(temp_file.name)

    # Intentar poner las primeras 2 gráficas juntas en una sola página, verticalmente
    if len(img_paths) >= 2:
        pdf.add_page()
        poner_fondo_negro()
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "Gráficas 1 y 2", ln=True, align='C')

        max_width = 180  # casi el ancho total con margen
        max_height = 120  # la mitad aprox. de la página menos márgenes

        y_positions = [25, 25 + max_height + 10]  # arriba y abajo con separación de 10mm
        x_position = 15  # margen lateral fijo

        for i in range(2):
            img_path = img_paths[i]
            im = Image.open(img_path)
            width_px, height_px = im.size
            dpi = im.info.get('dpi', (72, 72))[0]

            width_mm = (width_px / dpi) * 25.4
            height_mm = (height_px / dpi) * 25.4

            scale = min(max_width / width_mm, max_height / height_mm, 1)

            final_width = width_mm * scale
            final_height = height_mm * scale

            pdf.image(img_path, x=x_position, y=y_positions[i], w=final_width, h=final_height)

    # Ahora la gráfica 3 (boxplot) en página nueva
    if len(img_paths) >= 3:
        pdf.add_page()
        poner_fondo_negro()
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "Gráfica 3 - Boxplot", ln=True, align='C')

        img_path = img_paths[2]
        im = Image.open(img_path)
        width_px, height_px = im.size
        dpi = im.info.get('dpi', (72, 72))[0]

        width_mm = (width_px / dpi) * 25.4
        height_mm = (height_px / dpi) * 25.4

        # Escalar para que quepa casi toda la página con margen
        max_width = 180
        max_height = 250

        scale = min(max_width / width_mm, max_height / height_mm, 1)

        final_width = width_mm * scale
        final_height = height_mm * scale

        pdf.image(img_path, x=15, y=25, w=final_width, h=final_height)
        
        # Luego de las gráficas, pon leyendas si existen
        if colores_pies and etiquetas_pies and porcentajes_pies:
            pdf.set_xy(10, y_positions[1] + max_height + 5)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, "Leyendas:", ln=True)
            pdf.set_font("Arial", '', 11)
            poner_fondo_negro()

            y_leyenda = pdf.get_y()
            ancho_cuadro = 8
            alto_cuadro = 8

            # Leyendas para las 2 gráficas
            for i in range(2):
                colores = list(colores_pies[i])
                etiquetas = list(etiquetas_pies[i])
                porcentajes = list(porcentajes_pies[i])

                pdf.set_text_color(255, 255, 255)
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(0, 10, f"Datos Grafica {i + 1}", ln=True)
                pdf.set_font("Arial", '', 11)

                for idx, (c, etiqueta, porcentaje) in enumerate(zip(colores, etiquetas, porcentajes)):
                    x = 10
                    y = pdf.get_y() + 2

                    r, g, b = tuple(int(c.strip('#')[j:j+2], 16) for j in (0, 2, 4))
                    pdf.set_fill_color(r, g, b)
                    pdf.rect(x, y, ancho_cuadro, alto_cuadro, 'F')
                    pdf.set_xy(x + ancho_cuadro + 2, y - 2)
                    pdf.set_text_color(255, 255, 255)
                    pdf.cell(60, 10, etiqueta, ln=0)
                    pdf.cell(20, 10, f"{porcentaje:.1f}%", ln=1)

                pdf.ln(5)
    else:
        # Si hay menos de 2 gráficas o no caben juntas, cada una en página individual
        for i, img in enumerate(img_paths):
            pdf.add_page()
            poner_fondo_negro()
            pdf.set_text_color(255, 255, 255)
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(0, 10, quitar_emojis(f"Grafica {i + 1}"), ln=True, align='C')
            pdf.image(img, x=10, y=25, w=190)

    # Guardar y limpiar imágenes temporales
    pdf_path = os.path.join(tempfile.gettempdir(), "reporte_calificaciones.pdf")
    pdf.output(pdf_path)

    for img in img_paths:
        try:
            os.remove(img)
        except PermissionError:
            pass

    return pdf_path
# ------------------ Extraer datos pastel para PDF -------------------
colores1, etiquetas1, porcentajes1 = [], [], []
colores2, etiquetas2, porcentajes2 = [], [], []

for idx, parcial in enumerate(['P1', 'P2']):
    calificaciones = calificaciones_dict[parcial]
    if calificaciones.empty:
        continue

    ranges = pd.cut(calificaciones, bins=rango_bins, labels=rango_labels, right=False)
    conteo = ranges.value_counts(sort=False)
    valores = conteo.values
    etiquetas = conteo.index.tolist()
    colores = [rango_colores[label] for label in etiquetas]
    total = valores.sum()
    porcentajes = valores / total * 100

    if parcial == 'P1':
        colores1, etiquetas1, porcentajes1 = colores, etiquetas, porcentajes
    else:
        colores2, etiquetas2, porcentajes2 = colores, etiquetas, porcentajes

# ------------ Botón que se encarga de generar y descargar el PDF -----------------
if st.button("📥 Generar reporte PDF"):
    pdf_file = generar_pdf(
        calificaciones_dict=calificaciones_dict,
        carrera=carrera_seleccionada,
        grupo=grupo_seleccionado,
        asignatura=asignatura_seleccionada,
        semestre=semestre_seleccionado,
        colores_pies=[colores1, colores2],         # ✅ Correcto
        etiquetas_pies=[etiquetas1, etiquetas2],   # ✅ Correcto
        porcentajes_pies=[porcentajes1, porcentajes2]  # ✅ Correcto
    )

    with open(pdf_file, "rb") as f:
        st.download_button(
            label="📄 Descargar PDF",
            data=f,
            file_name="Reporte_Calificaciones.pdf",
            mime="application/pdf"
        )
