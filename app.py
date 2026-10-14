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
.block-container {padding-top: 1.6rem; max-width: 1180px;}
.eco-header {background: linear-gradient(120deg,#1b5e20 0%,#2e7d32 45%,#00897b 100%); color:#fff;
  padding: 22px 28px; border-radius: 18px; margin-bottom: 12px;}
.eco-header h1 {color:#fff; margin:0; font-size:2.1rem; line-height:1.2;}
.eco-header p {color:#e8f5e9; margin:6px 0 0 0;}
.eco-flujo {font-size:.88rem; color:#c8e6c9; margin-top:8px;}
.eco-aviso {background:#fff8e1; border:1px solid #ffe082; color:#5d4037; padding:10px 14px; border-radius:12px; font-size:.9rem;}
.eco-tarjeta {display:flex; gap:16px; align-items:center; padding:16px 18px; border-radius:14px; background:#ffffff;
  box-shadow:0 2px 12px rgba(0,0,0,.08); color:#1f2937;}
.eco-icono {font-size:3rem;}
.eco-titulo {font-size:1.55rem; font-weight:800;}
.eco-sub {color:#4b5563; margin-top:3px; font-size:.95rem;}
.eco-barra {height:10px; background:#e5e7eb; border-radius:6px; margin-top:8px; width:100%; max-width:300px;}
.eco-barra > div {height:10px; border-radius:6px;}
.eco-alerta {margin-top:10px; background:#ffebee; border:1px solid #ef9a9a; color:#b71c1c; padding:10px 14px; border-radius:12px;}
.eco-ok {margin-top:10px; background:#e8f5e9; border:1px solid #a5d6a7; color:#1b5e20; padding:10px 14px; border-radius:12px;}
.eco-prob {display:grid; grid-template-columns: 170px 1fr 52px; gap:8px; align-items:center; margin:5px 0; font-size:.93rem; color:#1f2937;}
.eco-prob .pista {height:12px; background:#eef2f1; border-radius:6px; overflow:hidden;}
.eco-prob .pista > div {height:12px; border-radius:6px;}
.eco-kpis {display:flex; gap:10px; flex-wrap:wrap; margin-top:8px;}
.eco-kpi {flex:1; min-width:130px; text-align:center; padding:10px; border-radius:12px; background:#e8f5e9; color:#1b5e20;}
.eco-kpi b {display:block; font-size:1.45rem;}
.eco-kpi span {font-size:.8rem;}
.eco-chip {display:inline-block; padding:3px 10px; border-radius:999px; color:#fff; font-size:.82rem; margin:2px 4px 2px 0;}
@media (max-width: 640px){ .eco-prob {grid-template-columns: 120px 1fr 46px;} .eco-header h1{font-size:1.6rem;} }
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
  <h1>♻️ EcoClasifica</h1>
  <p>Toma o sube una foto de un residuo: la IA estima su material, te sugiere el contenedor y te explica cómo prepararlo.</p>
  <div class="eco-flujo">📷 Imagen → 🧠 Modelo (clase + confianza) → 📊 Resultado → 💬 Gemini → ✅ Recomendación</div>
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
