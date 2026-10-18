"""
EcoClasifica ♻️ — App web (Streamlit)  ·  versión principal para Streamlit Community Cloud
==========================================================================================
Flujo: 📷 Imagen → 🧠 EfficientNet-B0 (clase + confianza) → 📊 Resultado → 💬 Gemini → ✅ Recomendación

Ejecutar localmente:   streamlit run app.py
Publicar gratis:       share.streamlit.io → Create app → este repositorio → archivo app.py
Clave de Gemini:       Secrets de Streamlit Cloud →  GEMINI_API_KEY = "..."   (nunca en el código)

La lógica (modelo, preprocesamiento, Gemini) está en nucleo.py y es la misma que usa app_gradio.py.
"""

import html
from pathlib import Path

import streamlit as st
from PIL import Image, UnidentifiedImageError

import nucleo

st.set_page_config(page_title="EcoClasifica ♻️", page_icon="♻️", layout="wide")

# ---------------------------------------------------------------------------
# Estilos (identidad visual de reciclaje)
# ---------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Manrope:wght@400;500;600;700;800&display=swap');
:root { color-scheme: light; }
html, body, [data-testid="stAppViewContainer"], [data-testid="stSidebar"] {
  font-family: 'DM Sans', sans-serif;
}
.stApp {
  background: radial-gradient(ellipse 65% 32% at 85% -6%,rgba(65,211,176,.15),transparent 75%),
              linear-gradient(180deg,#f8fbfa 0%,#f1f7f5 100%);
  color:#16342f;
}
.block-container {padding-top:2.2rem; padding-bottom:3.2rem; max-width:1250px;}
h1,h2,h3,h4 {font-family:'Manrope','DM Sans',sans-serif;letter-spacing:-.035em;}
[data-testid="stSidebar"] {
  background:linear-gradient(180deg,#e9f5f1 0%,#f3f9f7 100%);
  border-right:1px solid #d7e9e3;
}
[data-testid="stSidebar"] h3 {font-weight:800;color:#183f37;}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {color:#617b74;}
.eco-header {
  position:relative;overflow:hidden;isolation:isolate;
  background: radial-gradient(circle at 94% 8%,rgba(106,255,195,.18),transparent 35%),
              linear-gradient(116deg,#073b35 0%,#07594d 53%,#088575 100%);
  color:#fff; padding:40px 44px 36px; border-radius:26px; margin-bottom:16px;
  border:1px solid rgba(255,255,255,.13);
  box-shadow:0 20px 45px rgba(6,73,61,.20);
}
.eco-header:after {
  content:''; position:absolute; z-index:-1; right:-70px; top:-125px;
  width:370px;height:370px; border:1px solid rgba(255,255,255,.18);border-radius:50%;
  box-shadow:0 0 0 45px rgba(255,255,255,.045),0 0 0 105px rgba(255,255,255,.025);
}
.eco-eyebrow {color:#a6f0d6;font-size:.74rem;font-weight:800;letter-spacing:.14em;text-transform:uppercase;margin-bottom:12px;}
.eco-header h1 {color:#fff;font-size:clamp(2.1rem,4vw,3.25rem);font-weight:800;line-height:1.16;margin:0 0 12px;letter-spacing:-.045em;}
.eco-header p {color:#e5faf3;font-size:1rem;line-height:1.7;max-width:780px;margin:0;}
.eco-flujo {display:inline-block;background:rgba(255,255,255,.10);border:1px solid rgba(255,255,255,.16);
  color:#ecfff6; padding:9px 14px; border-radius:12px;font-size:.82rem;margin-top:20px;line-height:1.5;}
.eco-aviso {background:#fffdf5;border:1px solid #f4e8be;color:#755827;padding:14px 18px;
  border-radius:14px;font-size:.9rem;box-shadow:0 3px 12px rgba(116,82,24,.035);margin-bottom:5px;}
.eco-tarjeta {display:flex;gap:20px;align-items:center;padding:24px 26px;border-radius:22px;background:#fff;
  border:1px solid #e5eeea;box-shadow:0 12px 32px rgba(29,64,58,.09);color:#18342e;}
.eco-icono {font-size:3rem;filter:drop-shadow(0 5px 6px rgba(0,0,0,.05));}
.eco-titulo {font-family:'Manrope',sans-serif;font-size:1.8rem;font-weight:800;letter-spacing:-.05em;}
.eco-sub {color:#56746b;margin-top:6px;font-size:.93rem;line-height:1.55;}
.eco-barra {height:11px;background:#e9f1ee;border-radius:999px;margin-top:14px;width:100%;max-width:360px;overflow:hidden;}
.eco-barra > div {height:11px;border-radius:999px;}
.eco-alerta {margin-top:14px;background:#fff2f0;border:1px solid #f7cbc5;color:#8a3533;padding:17px 19px;border-radius:16px;line-height:1.65;}
.eco-ok {margin-top:14px;background:#eaf8f2;border:1px solid #c6e9d8;color:#21644e;padding:15px 19px;border-radius:16px;line-height:1.6;}
.eco-prob {display:grid;grid-template-columns:170px 1fr 50px;gap:11px;align-items:center;margin:12px 0;font-size:.9rem;color:#24483f;}
.eco-prob .pista {height:11px;background:#edf3f1;border-radius:999px;overflow:hidden;}
.eco-prob .pista > div {height:11px;border-radius:999px;}
.eco-kpis {display:flex;gap:12px;flex-wrap:wrap;margin-top:20px;}
.eco-kpi {flex:1;min-width:140px;text-align:center;padding:20px 15px;border-radius:18px;background:#fff;
  border:1px solid #e0ede7;box-shadow:0 6px 20px rgba(17,74,62,.055);color:#155f52;}
.eco-kpi b {font-family:'Manrope',sans-serif;display:block;font-size:1.65rem;letter-spacing:-.045em;}
.eco-kpi span {font-size:.78rem;color:#698178;line-height:1.5;}
.eco-chip {display:inline-block;padding:5px 11px;border-radius:999px;color:#fff;font-size:.78rem;
  font-weight:700;margin:3px 4px 3px 0;box-shadow:0 3px 8px rgba(0,0,0,.06);}
/* Componentes nativos de Streamlit: pestañas, carga y botones */
button[data-baseweb="tab"] {font-family:'DM Sans',sans-serif;font-weight:700;border-radius:10px 10px 0 0;}
button[data-baseweb="tab"][aria-selected="true"] {color:#087d69;}
[data-testid="stFileUploader"] {border:1px solid #e0eae6;border-radius:18px;background:rgba(255,255,255,.8);padding:12px;}
[data-testid="stBaseButton-primary"] {background:linear-gradient(115deg,#007d69,#0aaa8e)!important;
  border:0!important;border-radius:12px!important;font-weight:700!important;color:#fff!important;
  box-shadow:0 7px 19px rgba(0,126,102,.18);transition:transform .15s ease,box-shadow .15s ease;}
[data-testid="stBaseButton-primary"]:hover {transform:translateY(-1px);box-shadow:0 10px 24px rgba(0,126,102,.24);}
[data-testid="stBaseButton-secondary"] {border-radius:12px!important;border-color:#d8e5df!important;font-weight:600;}
[data-testid="stBaseButton-secondary"]:hover {border-color:#007e69!important;color:#007e69!important;}
[data-testid="stExpander"], [data-testid="stVerticalBlockBorderWrapper"] {border-radius:16px;}
@media(max-width:760px){
  .block-container {padding:1.1rem .8rem 2rem;}
  .eco-header {padding:26px 22px;border-radius:19px;}
  .eco-header h1 {font-size:2rem;}
  .eco-header p {font-size:.91rem;}
  .eco-flujo {font-size:.74rem;}
  .eco-prob {grid-template-columns:116px 1fr 42px;gap:7px;}
  .eco-tarjeta {padding:16px;gap:11px;}
  .eco-kpi {min-width:100px;padding:14px 8px;}
}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Carga del modelo (una sola vez gracias a cache_resource)
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner="Cargando el modelo…")
def obtener_clasificador():
    return nucleo.cargar_clasificador()


try:
    CLF = obtener_clasificador()
    ERROR_MODELO = None
except Exception as e:  # falta la carpeta modelo/ o un archivo dañado
    CLF, ERROR_MODELO = None, str(e)

UMBRAL = nucleo.umbral(CLF) if CLF else 0.60
# Nombre en español de cada imagen de ejemplo (los archivos usan los nombres de carpeta de TrashNet)
NOMBRE_EJEMPLO = {"cardboard": "Cartón", "glass": "Vidrio", "metal": "Metal", "paper": "Papel",
                  "plastic": "Plástico", "trash": "Basura"}
MET = CLF.metricas if CLF else None


def pct(x):
    return f"{x:.1%}".replace(".", ",")


# ---------------------------------------------------------------------------
# Encabezado
# ---------------------------------------------------------------------------
st.markdown("""
<div class="eco-header">
  <div class="eco-eyebrow">ECO INTELLIGENCE &nbsp; / &nbsp; VISIÓN ARTIFICIAL</div>
  <h1>♻️ EcoClasifica</h1>
  <p>Reciclar mejor comienza con identificar bien. Sube una fotografía y descubre el material más probable, su nivel de confianza y cómo prepararlo con ayuda de IA.</p>
  <div class="eco-flujo">📷 Tu imagen &nbsp; → &nbsp; 🧠 Clasificación inteligente &nbsp; → &nbsp; 📊 Probabilidades &nbsp; → &nbsp; ✨ Recomendación Gemini</div>
</div>""", unsafe_allow_html=True)
st.markdown('<div class="eco-aviso">🎓 <b>Prototipo educativo</b> — proyecto académico. Las predicciones pueden equivocarse; '
            'no reemplaza las indicaciones de tu municipio o punto limpio.</div>', unsafe_allow_html=True)

if ERROR_MODELO:
    st.error(f"❌ No se pudo cargar el modelo. {ERROR_MODELO}")
    st.stop()

# ---------------------------------------------------------------------------
# Barra lateral: guía de contenedores y desempeño resumido
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🎨 Contenedores NCh3322")
    st.markdown(
        "".join(f'<span class="eco-chip" style="background:{c}">{n}</span>' for n, c in [
            ("Azul · papel y cartón", "#1565c0"), ("Amarillo · plásticos", "#c79100"), ("Verde · vidrios", "#2e7d32"),
            ("Gris claro · metales", "#8d8d8d"), ("Beige · cartón bebidas", "#a1887f"), ("Rojo · peligrosos", "#c62828"),
            ("Gris oscuro · resto", "#424242")]), unsafe_allow_html=True)
    st.caption("Cada comuna puede aceptar materiales distintos. Confirma con tu municipio.")
    if MET:
        e = MET["prueba"]["modelo_desplegado"]
        onnx_acc = MET["prueba"].get("inferencia_onnx_app", {}).get("accuracy")
        st.markdown("### 📏 Desempeño en prueba")
        if onnx_acc is not None:
            st.markdown(f"- **Accuracy ONNX (app):** {pct(onnx_acc)}\n"
                        f"- **Balanced accuracy PyTorch:** {pct(e['balanced_accuracy'])}\n"
                        f"- **Umbral de revisión:** {UMBRAL:.0%}")
            st.caption("Las métricas por clase y la matriz corresponden a PyTorch; ONNX difiere en una predicción de 380.")
        else:
            st.markdown(f"- **Accuracy PyTorch:** {pct(e['accuracy'])}\n"
                        f"- **Balanced accuracy PyTorch:** {pct(e['balanced_accuracy'])}\n"
                        f"- **Umbral de revisión:** {UMBRAL:.0%}")
        st.caption(f"{MET['n_imagenes']['test']} imágenes de prueba nunca vistas en el entrenamiento.")
    else:
        st.warning("Aún no existe modelo/metricas.json: ejecuta el notebook.")

tab_clasificar, tab_desempeno, tab_acerca = st.tabs(["🔍 Clasificar residuo", "📊 Desempeño del modelo", "ℹ️ Acerca del proyecto"])

# ---------------------------------------------------------------------------
# Pestaña 1: clasificar
# ---------------------------------------------------------------------------
with tab_clasificar:
    if "ejemplo" not in st.session_state:
        st.session_state.ejemplo = None

    col_izq, col_der = st.columns([5, 6], gap="large")

    with col_izq:
        origen = st.segmented_control("¿Cómo quieres ingresar la imagen?", ["📁 Subir foto", "📸 Cámara", "🧪 Ejemplos"],
                                      default="📁 Subir foto", key="origen")
        imagen, nombre_imagen = None, None

        if origen == "📁 Subir foto":
            archivo = st.file_uploader("Foto del residuo (JPG, PNG o WEBP)", type=["jpg", "jpeg", "png", "webp"])
            if archivo is not None:
                try:
                    imagen, nombre_imagen = Image.open(archivo), archivo.name
                except UnidentifiedImageError:
                    st.error("El archivo no es una imagen válida. Prueba con otra foto (JPG o PNG).")
        elif origen == "📸 Cámara":
            foto = st.camera_input("Toma una foto del residuo")
            if foto is not None:
                imagen, nombre_imagen = Image.open(foto), "foto de cámara"
        else:
            ejemplos = sorted(nucleo.CARPETA_EJEMPLOS.glob("*.jpg"))
            if not ejemplos:
                st.info("No hay imágenes en la carpeta ejemplos/ (se generan con el notebook).")
            st.caption("Imágenes del conjunto de **prueba** de TrashNet (el modelo no las vio al entrenar). Haz clic en una:")
            cols = st.columns(3)
            for i, ruta in enumerate(ejemplos):
                with cols[i % 3]:
                    st.image(str(ruta), width="stretch")
                    etiqueta = NOMBRE_EJEMPLO.get(ruta.stem, ruta.stem)
                    if st.button(f"Usar: {etiqueta}", key=f"ej_{ruta.stem}", width="stretch"):
                        st.session_state.ejemplo = str(ruta)
            if st.session_state.ejemplo:
                imagen = Image.open(st.session_state.ejemplo)
                nombre_imagen = "ejemplo de " + NOMBRE_EJEMPLO.get(Path(st.session_state.ejemplo).stem, "prueba")

        if imagen is not None:
            st.image(imagen, caption=f"Imagen analizada: {nombre_imagen}", width="stretch")
        st.caption("💡 Para mejores resultados: un solo objeto, centrado, con fondo claro y buena luz.")

    with col_der:
        if imagen is None:
            st.info("👈 Sube una foto, usa la cámara o elige un ejemplo para comenzar.")
        else:
            try:
                r = nucleo.clasificar(CLF, imagen)
            except Exception as e:
                st.error(f"No se pudo procesar la imagen ({type(e).__name__}). Prueba con otra foto.")
                st.stop()

            # Si cambió la imagen, se borra la recomendación anterior
            firma = (nombre_imagen, round(r["confianza"], 6), r["clase"])
            if st.session_state.get("firma") != firma:
                st.session_state.firma, st.session_state.recomendacion = firma, None

            info = nucleo.INFO_CLASES[r["clase"]]
            baja = r["confianza"] < UMBRAL
            st.markdown(f"""
<div class="eco-tarjeta" style="border-left:8px solid {info['color']}">
  <div class="eco-icono">{info['icono']}</div>
  <div style="flex:1">
    <div class="eco-sub">Material más probable</div>
    <div class="eco-titulo">{html.escape(r['clase'])}</div>
    <div class="eco-sub">Contenedor sugerido: <b>{info['contenedor']}</b></div>
    <div class="eco-sub">{info['nota']}</div>
    <div class="eco-barra"><div style="width:{r['confianza']*100:.1f}%; background:{info['color']}"></div></div>
    <div class="eco-sub">Confianza de <b>esta predicción</b>: <b>{pct(r['confianza'])}</b></div>
  </div>
</div>""", unsafe_allow_html=True)

            if baja:
                st.markdown(f"""<div class="eco-alerta">⚠️ <b>Confianza baja ({pct(r['confianza'])} &lt; {UMBRAL:.0%}). Requiere revisión humana.</b><br>
Puede ser <b>{html.escape(r['clase'])}</b> o <b>{html.escape(r['segunda'])}</b>, o un objeto que <b>no pertenece</b> a ninguna de las 6 clases
(el modelo siempre elige una). Revisa el material tú mismo antes de depositarlo.</div>""", unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="eco-ok">✅ Confianza sobre el umbral de revisión ({UMBRAL:.0%}). Aun así, verifica que '
                            'el residuo esté limpio y que no sea una mezcla de materiales.</div>', unsafe_allow_html=True)

            st.markdown("#### 📊 Probabilidad de cada clase")
            filas = ""
            for clase, p in sorted(r["probabilidades"].items(), key=lambda kv: -kv[1]):
                c = nucleo.INFO_CLASES[clase]["color"]
                filas += (f'<div class="eco-prob"><div>{nucleo.INFO_CLASES[clase]["icono"]} {html.escape(clase)}</div>'
                          f'<div class="pista"><div style="width:{p*100:.1f}%; background:{c}"></div></div><div>{p:.0%}</div></div>')
            st.markdown(filas, unsafe_allow_html=True)

            if MET:
                e = MET["prueba"]["modelo_desplegado"]
                onnx_acc = MET["prueba"].get("inferencia_onnx_app", {}).get("accuracy", e["accuracy"])
                st.markdown(f"""<div class="eco-kpis">
<div class="eco-kpi"><b>{pct(onnx_acc)}</b><span>Accuracy ONNX (app) en prueba</span></div>
<div class="eco-kpi"><b>{pct(e['balanced_accuracy'])}</b><span>Balanced accuracy PyTorch en prueba</span></div>
<div class="eco-kpi"><b>{UMBRAL:.0%}</b><span>Umbral de revisión (elegido en validación)</span></div></div>""",
                            unsafe_allow_html=True)
                st.caption("ℹ️ La **confianza** es de esta imagen; la **accuracy** es del modelo sobre todo el conjunto de prueba. "
                           "Son cosas distintas: una predicción con confianza alta también puede estar equivocada.")

            st.divider()
            st.markdown("#### 💬 Recomendación de reciclaje generada por IA")
            st.caption("Se envía a Gemini solo texto: la clase, la confianza y la segunda opción. La foto no se envía.")
            if st.button("✨ Obtener recomendación con IA (Gemini)", type="primary", width="stretch"):
                with st.spinner("Consultando a Gemini…"):
                    try:
                        texto, modelo = nucleo.recomendar_gemini(r, UMBRAL, nucleo.leer_clave_gemini())
                        st.session_state.recomendacion = (texto, modelo)
                    except nucleo.ErrorGemini as err:
                        st.session_state.recomendacion = None
                        st.error(f"❌ {err}")
            if st.session_state.get("recomendacion"):
                texto, modelo = st.session_state.recomendacion
                with st.container(border=True):
                    st.markdown(texto)
                    st.caption(f"Recomendación generada por IA ({modelo}). Puede contener errores: verifica con tu municipio o punto limpio.")

    with st.expander("⚠️ Límites del modelo (léelo antes de usar la app)"):
        st.markdown(nucleo.AVISO_GENERAL)

# ---------------------------------------------------------------------------
# Pestaña 2: desempeño
# ---------------------------------------------------------------------------
with tab_desempeno:
    if not MET:
        st.warning("Aún no hay métricas: ejecuta el notebook y copia `modelo/metricas.json`.")
    else:
        sel, pr, um = MET["seleccion"], MET["prueba"], MET["umbral_confianza"]
        st.markdown(f"### 1. Selección del enfoque (conjunto de **validación**, {MET['n_imagenes']['val']} imágenes)")
        st.table({
            "Enfoque": ["EfficientNet-B0 (transfer learning)", "CLIP zero-shot (sin entrenar)"],
            "Accuracy": [pct(sel["validacion"]["efficientnet_b0"]["accuracy"]), pct(sel["validacion"]["clip_zero_shot"]["accuracy"])],
            "Balanced accuracy": [pct(sel["validacion"]["efficientnet_b0"]["balanced_accuracy"]),
                                  pct(sel["validacion"]["clip_zero_shot"]["balanced_accuracy"])],
        })
        st.markdown(f"**Criterio:** {sel['criterio']}. **Ganador en validación:** {sel['ganador_validacion']}. "
                    f"**Modelo usado en la app:** {sel['modelo_desplegado']}. {sel['motivo']}")

        st.markdown(f"### 2. Evaluación final en **prueba** ({MET['n_imagenes']['test']} imágenes, usadas una sola vez)")
        st.table({
            "Enfoque": ["EfficientNet-B0 (transfer learning)", "CLIP zero-shot (sin entrenar)"],
            "Accuracy": [pct(pr["efficientnet_b0"]["accuracy"]), pct(pr["clip_zero_shot"]["accuracy"])],
            "Balanced accuracy": [pct(pr["efficientnet_b0"]["balanced_accuracy"]), pct(pr["clip_zero_shot"]["balanced_accuracy"])],
        })
        onnx_info = pr.get("inferencia_onnx_app")
        if onnx_info:
            st.info(f"**Accuracy de la aplicación ONNX: {pct(onnx_info['accuracy'])}** "
                    f"({onnx_info['aciertos']}/{onnx_info['n']} imágenes correctas). "
                    "La versión ONNX cambió 1 de las 380 predicciones respecto a PyTorch. "
                    "La balanced accuracy y el desglose que aparece debajo corresponden a PyTorch.")
        st.markdown("#### Precisión y recall por clase (evaluación PyTorch, prueba)")
        d = pr["modelo_desplegado"]
        st.table({"Clase": list(d["recall_por_clase"]),
                  "Precisión": [pct(d["precision_por_clase"][c]) for c in d["recall_por_clase"]],
                  "Recall": [pct(d["recall_por_clase"][c]) for c in d["recall_por_clase"]]})
        if (nucleo.CARPETA_MODELO / "matriz_confusion.png").exists():
            st.image(str(nucleo.CARPETA_MODELO / "matriz_confusion.png"), caption="Matriz de confusión de EfficientNet-B0 en PyTorch — conjunto de prueba (ONNX difiere en una predicción)")

        ec = MET["errores_costosos"]
        st.markdown(f"""### 3. Errores más costosos (evaluación PyTorch en prueba)
- 🔴 **Basura clasificada como reciclable** (contamina el contenedor): **{ec['basura_como_reciclable']} de {ec['n_basura']}**.
- 🔴 **Vidrio clasificado como papel, cartón o plástico** (riesgo de corte y contaminación): **{ec['vidrio_como_fibra_o_plastico']} de {ec['n_vidrio']}**.
- 🟡 Reciclable clasificado como basura (se pierde material): **{ec['reciclable_como_basura']} de {ec['n_reciclables']}**.""")

        st.markdown(f"""### 4. Umbral de revisión humana: {um['valor']:.0%}
**Cómo se eligió (validación, PyTorch):** {um['criterio']}.
- En **validación**, las predicciones con confianza ≥ {um['valor']:.0%} cubren el {pct(um['validacion']['cobertura'])} de las imágenes, con accuracy de {pct(um['validacion']['accuracy_aceptadas'])}.
- En **prueba PyTorch** (comprobación final): cobertura de {pct(um['prueba']['cobertura'])}, con accuracy de {pct(um['prueba']['accuracy_aceptadas'])} sobre el umbral y de {um['prueba']['accuracy_bajo_umbral_txt']} bajo el umbral.""")

        fr = MET.get("fotos_reales")
        st.markdown("### 5. Prueba con fotografías reales del grupo")
        if fr:
            st.markdown(f"Se probaron **{fr['n']} fotos propias** (fondos y luces reales, fuera de TrashNet): accuracy de **{pct(fr['accuracy'])}** "
                        f"y {pct(fr['fraccion_bajo_umbral'])} de las fotos con confianza bajo el umbral.")
        else:
            st.info("Pendiente: aún no se agregan resultados con fotos reales (sección 11 del notebook).")
        st.caption(f"Entrenado el {MET['fecha']} · División estratificada 70/15/15 (semilla 42) · "
                   f"{MET['n_imagenes']['train']} entrenamiento, {MET['n_imagenes']['val']} validación, {MET['n_imagenes']['test']} prueba.")

# ---------------------------------------------------------------------------
# Pestaña 3: acerca de
# ---------------------------------------------------------------------------
with tab_acerca:
    st.markdown(f"""
### ¿Qué resuelve?
Muchas personas dudan sobre en qué contenedor va cada residuo, y un error puede contaminar un lote completo de material reciclable.
EcoClasifica orienta a hogares, colegios y oficinas: estima el material a partir de una foto y explica cómo prepararlo.

### ¿Cómo funciona?
1. **Modelo de visión:** EfficientNet-B0 preentrenado en ImageNet y ajustado (*transfer learning*) con TrashNet. Se comparó con CLIP sin entrenar (*zero-shot*) usando validación.
2. **Resultado:** clase más probable, confianza y probabilidades de las 6 clases.
3. **IA generativa:** Google Gemini redacta la recomendación a partir de la clase y la confianza (solo texto), con reglas de seguridad y de prudencia.

### Datos
[TrashNet](https://github.com/garythung/trashnet) — Gary Thung y Mindy Yang (Stanford, 2016), **licencia MIT**. Tiene 2.527 fotos en 6 clases, tomadas sobre fondo blanco.

### Limitaciones
{nucleo.AVISO_GENERAL}
- Las fotos de entrenamiento tienen fondo blanco y un solo objeto, y son envases de EE. UU.: con fotos reales el desempeño puede bajar.
- La clase *Basura* tiene pocas imágenes (137).

### Privacidad
La foto se procesa en el servidor de la app y no se guarda. A Gemini solo se envía texto.
""")
