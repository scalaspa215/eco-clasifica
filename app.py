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
st.markdown(r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Fraunces:wght@500;600;700&display=swap');
:root {
  --bosque:#1F3D2B; --hoja:#3E7B4F; --salvia:#A7C4A0;
  --musgo:#E6EFE3; --crema:#F7F5EF; --tierra:#8B6B4A;
  --texto:#22392B; --muted:#4B6251; --linea:#DAE3D6;
  --blanco:#FFFDF8; --ambar:#6F4C17;
}
*, *::before, *::after { box-sizing:border-box; }
html, body, .stApp, [data-testid="stAppViewContainer"] { font-family:'DM Sans',system-ui,sans-serif; }
.stApp {
  color:var(--texto);
  background:
    radial-gradient(ellipse 58% 36% at 94% 6%,rgba(167,196,160,.18),transparent 72%),
    radial-gradient(ellipse 34% 28% at 1% 72%,rgba(230,239,227,.67),transparent 80%),
    var(--crema);
}
[data-testid="stAppViewContainer"] { background:transparent; overflow-x:clip; }
.block-container { max-width:1260px; padding-top:2.1rem; padding-bottom:4rem; }
[data-testid="stVerticalBlock"], [data-testid="stHorizontalBlock"], [data-testid="column"] { min-width:0; }
.stMarkdown, .stMarkdown p { color:var(--texto); }
h1,h2,h3,h4,.eco-titulo,.eco-kpi b { font-family:'Fraunces',Georgia,serif; letter-spacing:-.035em; }
h2,h3,h4 { color:var(--bosque); }
[data-testid="stSidebar"] { background:#EDF2E9; border-right:1px solid #D6E1D3; }
[data-testid="stSidebar"] [data-testid="stSidebarContent"] { padding-top:2rem; }
[data-testid="stSidebar"] h3 { font-family:'Fraunces',serif; color:var(--bosque); font-size:1.16rem; }
[data-testid="stSidebar"] p, [data-testid="stSidebar"] li { color:#344E3B; }
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] { color:#506655; }
.bot-sidebar-title { display:flex; align-items:center; gap:9px; font-family:'Fraunces',Georgia,serif;
  font-size:1.22rem; font-weight:650; color:var(--bosque); margin:.85rem 0 1.1rem; }
.bot-sidebar-title svg { flex-shrink:0; width:21px; height:21px; stroke:var(--hoja); }
.bot-sidebar-label { font-family:'DM Sans',sans-serif;font-size:.72rem;letter-spacing:.11em;
  text-transform:uppercase;font-weight:700;color:var(--bosque);margin:28px 0 10px;display:flex;align-items:center;gap:8px; }
.bot-sidebar-label svg {width:19px;height:19px;stroke:var(--hoja);}
.bot-badges {display:flex;flex-wrap:wrap;gap:7px;margin:0 0 12px;}
.eco-chip { display:inline-flex;align-items:center;padding:8px 11px;border-radius:100px;font-weight:700;
  font-size:.76rem;line-height:1.15;border:1px solid rgba(31,61,43,.12);box-shadow:0 2px 5px rgba(18,45,28,.06); }
.bot-sidebar-note {font-size:.81rem;line-height:1.6;color:#4A6252;margin:12px 0 18px;}
/* Editorial hero with botanical silhouettes and linen grain — self-contained SVG + CSS */
.eco-header {
  isolation:isolate; position:relative; overflow:hidden; min-height:342px;
  border-radius:30px; padding:49px clamp(24px,4vw,58px) 45px;
  margin-bottom:18px; color:#FFFFFF;
  background:linear-gradient(117deg,#142F22 0%,#1F3D2B 52%,#356A46 100%);
  border:1px solid rgba(255,255,255,.13);
  box-shadow:0 24px 55px rgba(32,57,38,.17),0 4px 12px rgba(32,57,38,.08);
}
.eco-header::after {
  content:"";position:absolute;inset:0;z-index:-2;pointer-events:none;
  background-image:repeating-linear-gradient(0deg,transparent 0px,transparent 3px,rgba(249,248,235,.022) 4px),
   repeating-linear-gradient(90deg,transparent 0px,transparent 6px,rgba(249,248,235,.012) 7px);
  opacity:.85;
}
.eco-header::before { content:"";position:absolute;z-index:-1;inset:0;pointer-events:none;
  background:radial-gradient(ellipse 44% 74% at 98% 47%,rgba(167,196,160,.17),transparent 75%); }
.bot-hero-copy {position:relative;z-index:4;max-width:755px;}
.bot-kicker {display:inline-flex;align-items:center;gap:10px;color:#D6E9D5;
  letter-spacing:.17em;text-transform:uppercase;font-size:.7rem;font-weight:700;margin-bottom:18px;}
.bot-kicker::before {content:"";height:1px;width:27px;background:#B8D1B5;}
.bot-wordmark {display:flex;align-items:center;gap:15px;margin:0 0 17px;}
.bot-logo {width:51px;height:51px;flex:none;border:1px solid rgba(231,244,224,.35);border-radius:15px;
  display:flex;align-items:center;justify-content:center;background:rgba(255,255,255,.09);backdrop-filter:blur(7px);}
.bot-logo svg {width:30px;height:30px;stroke:#E6EFE3;fill:none;stroke-width:1.5;stroke-linecap:round;stroke-linejoin:round;}
.eco-header h1 {color:#FEFEF8!important;font-family:'Fraunces',Georgia,serif;
  font-size:clamp(2.65rem,5.7vw,4.45rem);font-weight:600;line-height:1.05;margin:0;
  letter-spacing:-.055em;text-shadow:0 2px 14px rgba(13,29,21,.14);}
.eco-header h1 em {font-style:normal;color:#D2E7C9;}
.eco-header p {color:#F0F5EB;font-size:clamp(.93rem,1.6vw,1.05rem);line-height:1.83;
  margin:0;max-width:620px;text-wrap:pretty;}
.bot-hero-divider {width:48px;height:2px;border-radius:10px;background:#B7D1A9;margin:22px 0 18px;}
.eco-flujo {display:flex;align-items:center;flex-wrap:wrap;gap:7px;
  margin-top:0;max-width:730px;color:#F5FBF0;}
.bot-step {display:inline-flex;align-items:center;gap:7px;background:rgba(254,255,248,.085);
  border:1px solid rgba(244,250,239,.22);padding:8px 11px;border-radius:99px;font-size:.75rem;
  backdrop-filter:blur(8px);font-weight:600;color:#F8FFF5;white-space:nowrap;}
.bot-step svg {width:15px;height:15px;stroke:#E0EED7;stroke-width:1.7;fill:none;stroke-linecap:round;stroke-linejoin:round;}
.bot-step-arrow {color:#D0E6C7;opacity:.9;font-size:.76rem;}
.bot-leaf {position:absolute;pointer-events:none;z-index:1;transform-origin:50% 94%;animation:bot-sway 10s ease-in-out infinite alternate;}
.bot-leaf-monstera {width:365px;height:405px;right:-100px;top:-61px;opacity:.28;transform:rotate(-22deg);}
.bot-leaf-fern {width:290px;height:355px;right:120px;bottom:-183px;opacity:.18;transform:rotate(-16deg);animation-delay:-4s;}
.bot-leaf-eucalyptus {width:220px;height:230px;right:-20px;bottom:-108px;opacity:.21;transform:rotate(5deg);animation-delay:-2s;}
@keyframes bot-sway {0%{rotate:-1.6deg}100%{rotate:1.5deg}}
.eco-aviso {display:flex;align-items:flex-start;gap:12px;background:#FBF1DC;border:1px solid #E8D3AC;
  color:#624714!important;padding:17px 19px;border-radius:17px;font-size:.87rem;
  line-height:1.65;box-shadow:0 4px 16px rgba(85,65,33,.045);margin:0 0 14px;}
.eco-aviso svg,.eco-alerta svg,.eco-ok svg {width:20px;height:20px;min-width:20px;stroke:currentColor;fill:none;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round;margin-top:1px;}
.eco-aviso strong {color:#573D11;}
/* Analysis result & organic cards */
.eco-tarjeta {position:relative;display:flex;gap:19px;align-items:flex-start;padding:27px;
  border-radius:27px;background:rgba(255,253,248,.93);border:1px solid #DCE6D7;
  box-shadow:0 13px 36px rgba(28,59,37,.075),0 1px 3px rgba(28,59,37,.035);
  color:var(--bosque);transition:box-shadow .28s ease,transform .28s ease;}
.eco-tarjeta:hover,.eco-kpi:hover {transform:translateY(-2px);box-shadow:0 18px 42px rgba(28,59,37,.11);}
.eco-icono {width:59px;height:59px;flex:0 0 59px;border-radius:19px;
  display:flex;align-items:center;justify-content:center;background:var(--musgo);}
.eco-icono svg {width:30px;height:30px;stroke:var(--bosque);fill:none;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round;}
.eco-titulo {font-family:'Fraunces',Georgia,serif;font-size:clamp(1.75rem,3vw,2.26rem);
  font-weight:600;color:var(--bosque);line-height:1.2;margin:1px 0 8px;}
.eco-sub {font-family:'DM Sans',sans-serif;color:#435B49;margin:5px 0;font-size:.9rem;line-height:1.65;}
.eco-sub b {color:#1F3D2B;font-weight:700;}
.bot-overline {text-transform:uppercase;letter-spacing:.12em;font-size:.69rem;color:#526958;font-weight:700;}
.bot-result-lead {font-family:'DM Sans',sans-serif;font-size:.94rem;line-height:1.6;color:#344A39;margin:8px 0;}
.eco-barra {height:12px;background:#E4EBDF;border-radius:99px;margin:16px 0 11px;width:100%;overflow:hidden;}
.eco-barra > div {height:100%;border-radius:99px;transition:width .6s ease;}
.eco-alerta,.eco-ok {display:flex;align-items:flex-start;gap:11px;border-radius:18px;
 padding:16px 18px;line-height:1.7;margin-top:14px;font-size:.9rem;}
.eco-alerta {background:#FFF1E6;border:1px solid #E9C5A4;color:#763E21;}
.eco-ok {background:#E6F2E4;border:1px solid #BFDBC2;color:#245A36;}
.eco-alerta b {color:#6A3216;}.eco-ok b {color:#205333;}
.bot-section-heading {display:flex;align-items:center;gap:10px;margin:29px 0 14px;
  font-family:'Fraunces',Georgia,serif;font-weight:600;font-size:1.45rem;color:var(--bosque);}
.bot-section-heading svg {width:20px;height:20px;stroke:var(--hoja);stroke-width:1.6;fill:none;stroke-linecap:round;stroke-linejoin:round;}
.eco-prob {display:grid;grid-template-columns:minmax(118px,160px) minmax(0,1fr) 49px;gap:12px;align-items:center;
 padding:10px 12px;margin:5px 0;border-radius:13px;background:rgba(255,253,248,.72);
 border:1px solid rgba(218,227,214,.58);font-size:.85rem;color:var(--texto);}
.bot-prob-label {display:flex;align-items:center;gap:8px;min-width:0;overflow-wrap:anywhere;line-height:1.35;}
.bot-prob-label svg {width:19px;height:19px;flex:none;stroke:#526B57;fill:none;stroke-width:1.7;stroke-linejoin:round;stroke-linecap:round;}
.eco-prob .pista {height:11px;background:#E8ECE5;border-radius:999px;overflow:hidden;}
.eco-prob .pista > div {height:100%;border-radius:999px;transition:width .65s ease;}
.eco-prob .bot-prob-value {font-weight:700;font-variant-numeric:tabular-nums;text-align:right;}
.eco-kpis {display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:11px;margin-top:23px;}
.eco-kpi {min-width:0;text-align:left;padding:20px 18px;border-radius:19px;
  background:rgba(230,239,227,.7);border:1px solid #D4E0CE;
  box-shadow:0 5px 18px rgba(28,59,37,.035);transition:transform .24s ease,box-shadow .24s ease;}
.eco-kpi b {font-family:'Fraunces',Georgia,serif;display:block;font-size:clamp(1.44rem,2.8vw,2rem);color:#254E34;line-height:1.15;}
.eco-kpi span {font-size:.76rem;color:#3F5947;display:block;line-height:1.5;margin-top:8px;}
/* Native Streamlit widgets */
button[data-baseweb="tab"] {color:var(--bosque)!important;font-family:'DM Sans',sans-serif;font-size:.9rem;
 font-weight:700!important;white-space:normal!important;line-height:1.4;min-height:50px;}
button[data-baseweb="tab"][aria-selected="true"] {color:#285E39!important;}
[data-testid="stTabs"] [data-baseweb="tab-highlight"] {background-color:var(--hoja)!important;height:3px;}
[data-testid="stFileUploader"] {padding:11px;background:rgba(255,253,248,.88);
  border:1px solid #DCE4D7;border-radius:19px;box-shadow:0 7px 21px rgba(27,55,32,.045);}
[data-testid="stBaseButton-primary"], [data-testid="stBaseButton-secondary"] {
  min-height:44px;transition:transform .2s ease,box-shadow .2s ease!important;
  font-family:'DM Sans',sans-serif!important;font-weight:700!important;border-radius:13px!important;}
[data-testid="stBaseButton-primary"] {color:#fff!important;background:#285F3A!important;
  border:1px solid #285F3A!important;box-shadow:0 7px 18px rgba(41,88,53,.16);}
[data-testid="stBaseButton-primary"]:hover {background:#1F4C2F!important;transform:translateY(-1px);}
[data-testid="stBaseButton-secondary"] {color:#254633!important;background:rgba(255,253,248,.88)!important;
  border:1px solid #BACBBA!important;}
[data-testid="stBaseButton-secondary"]:hover {background:#E6EFE3!important;transform:translateY(-1px);}
[data-testid="stSegmentedControl"] button {min-height:44px;font-size:.85rem;}
[data-testid="stExpander"] {border-color:#D4DFD1!important;border-radius:16px!important;}
[data-testid="stVerticalBlockBorderWrapper"] {border-radius:20px!important;}
[data-testid="stAlert"] {border-radius:14px!important;}
[data-testid="stDataFrame"], [data-testid="stTable"] {max-width:100%;}
[data-testid="stTable"] {overflow-x:auto;}
[data-testid="stCaptionContainer"] {color:#516955;}
/* Thin editorial dividers on tab content */
[data-testid="stDivider"] {color:#CCDCC8!important;}
@media (min-width:1024px) {
  .eco-header {padding-right:280px;}
}
@media (max-width:760px) {
  html,body,.stApp,[data-testid="stAppViewContainer"] {width:100%;max-width:100%;overflow-x:clip;}
  .block-container {padding:1rem .75rem 2.5rem;max-width:100%;}
  .eco-header {border-radius:22px;min-height:0;padding:29px 22px 28px;margin-bottom:14px;}
  .bot-wordmark {gap:11px;margin-bottom:16px;}
  .bot-logo {width:42px;height:42px;border-radius:12px;}
  .bot-logo svg {width:25px;height:25px;}
  .eco-header h1 {font-size:clamp(2rem,9.5vw,2.9rem);line-height:1.08;}
  .eco-header p {font-size:.91rem;line-height:1.75;}
  .bot-kicker {font-size:.62rem;letter-spacing:.115em;margin-bottom:14px;}
  .eco-flujo {gap:6px;}
  .bot-step {font-size:.67rem;padding:7px 9px;}
  .bot-step-arrow {display:none;}
  .bot-leaf-monstera {width:174px;height:200px;right:-85px;top:-65px;opacity:.16;}
  .bot-leaf-fern,.bot-leaf-eucalyptus {display:none;}
  .eco-aviso {padding:13px 13px;font-size:.81rem;border-radius:14px;}
  .eco-tarjeta {padding:17px 16px;gap:12px;border-radius:19px;}
  .eco-icono {width:46px;height:46px;flex-basis:46px;border-radius:15px;}
  .eco-icono svg {width:25px;height:25px;}
  .eco-titulo {font-size:1.85rem;}
  .eco-sub {font-size:.82rem;}
  .eco-prob {grid-template-columns:minmax(95px,112px) minmax(0,1fr) 39px;gap:6px;
    padding:10px 8px;font-size:.76rem;}
  .bot-prob-label {gap:5px;}
  .bot-prob-label svg {width:16px;height:16px;}
  .eco-kpis {grid-template-columns:repeat(3,minmax(0,1fr));gap:7px;}
  .eco-kpi {padding:13px 10px;border-radius:14px;}
  .eco-kpi b {font-size:clamp(1.22rem,5vw,1.65rem);}
  .eco-kpi span {font-size:.68rem;overflow-wrap:anywhere;}
  .bot-section-heading {font-size:1.26rem;}
  [data-testid="stHorizontalBlock"] {flex-wrap:wrap!important;gap:.7rem!important;}
  [data-testid="stHorizontalBlock"] > [data-testid="column"] {
    flex:1 1 100%!important;width:100%!important;min-width:0!important;max-width:100%!important;}
  [data-testid="stTabs"] [data-baseweb="tab-list"] {display:flex;flex-wrap:wrap;gap:0;}
  button[data-baseweb="tab"] {flex:1 1 30%;min-width:0!important;font-size:.74rem;line-height:1.25;
    padding:.55rem .33rem;min-height:54px;}
  [data-testid="stSegmentedControl"] {max-width:100%;}
  [data-testid="stSegmentedControl"] button {min-height:44px!important;}
  [data-testid="stBaseButton-primary"],[data-testid="stBaseButton-secondary"] {min-height:44px!important;}
  [data-testid="stImage"] img {max-width:100%;height:auto;object-fit:contain;}
}
@media(max-width:390px) {
  .block-container {padding-left:.55rem;padding-right:.55rem;}
  .eco-header {padding-left:17px;padding-right:17px;}
  .eco-prob {grid-template-columns:98px minmax(0,1fr) 35px;}
  .eco-tarjeta {gap:10px;padding:14px 12px;}
  .eco-kpi {padding:12px 8px;}
}
@media (prefers-reduced-motion:reduce) {
  *,*::before,*::after {animation-duration:.01ms!important;transition-duration:.01ms!important;scroll-behavior:auto!important;}
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



# SVG decorativos y pictogramas de trazo fino; no dependen de archivos ni imágenes externas.
ICONO_TRAZO = {
    "hoja": '<path d="M20 4C12 5 6 9 5 17c-.5 2 1 3.5 3 3 8-1 12-8 12-16Z"/><path d="M4 21c3-7 7-10 12-12"/>',
    "camara": '<rect x="3" y="6" width="18" height="14" rx="3"/><path d="M8 6l1.5-2h5L16 6"/><circle cx="12" cy="13" r="3.2"/>',
    "analizar": '<path d="M5 8V5h3M16 5h3v3M19 16v3h-3M8 19H5v-3"/><circle cx="12" cy="12" r="4"/><path d="m10.3 12 1.2 1.2 2.3-2.5"/>',
    "barras": '<path d="M5 20v-6M10 20V9M15 20V4M20 20v-9"/>',
    "sparkle": '<path d="m12 2 1.9 6.1L20 10l-6.1 1.9L12 18l-1.9-6.1L4 10l6.1-1.9L12 2Z"/><path d="m20 17 .5 1.5L22 19l-1.5.5L20 21l-.5-1.5L18 19l1.5-.5L20 17Z"/>',
    "shield": '<path d="m12 2 8 4v5c0 5-3.2 8.8-8 11-4.8-2.2-8-6-8-11V6l8-4Z"/><path d="m8.5 12 2.2 2.2 4.7-4.7"/>',
    "alerta": '<path d="M11 3.5 2.5 18c-.5.9.1 2 1.1 2h16.8c1 0 1.6-1.1 1.1-2L13 3.5c-.4-.8-1.6-.8-2 0Z"/><path d="M12 9v4M12 16.5v.5"/>',
    "check": '<circle cx="12" cy="12" r="9"/><path d="m8 12 2.7 2.8L16 9"/>',
    "papel": '<path d="M6 2h9l4 4v16H6V2Z"/><path d="M15 2v5h4M9 12h7M9 16h7"/>',
    "carton": '<path d="m3 7 9-5 9 5v10l-9 5-9-5V7Z"/><path d="m3 7 9 5 9-5M12 12v10M8 4.6l9 5"/>',
    "plastico": '<path d="M9 3h6M10 3v3l-2 2v12a2 2 0 0 0 2 2h4a2 2 0 0 0 2-2V8l-2-2V3M8 11h8M8 16h8"/>',
    "vidrio": '<path d="M6 3h12v5c0 4-2.6 6.5-6 6.5S6 12 6 8V3Z"/><path d="M12 14.5V21M8 21h8M8 6h8"/>',
    "metal": '<path d="M6 4h12l1.2 3v13H4.8V7L6 4Z"/><path d="M5 7h14M6 20h12M8 11h8M8 15h8"/>',
    "basura": '<path d="M4 7h16M9 7V4h6v3M6 7l1 14h10l1-14M10 11v7M14 11v7"/>',
}

def icono_lineal(nombre: str, tam: int = 20) -> str:
    """Pictograma decorativo para la interfaz. No interviene en la inferencia."""
    paths = ICONO_TRAZO.get(nombre, ICONO_TRAZO["hoja"])
    return (f'<svg aria-hidden="true" width="{tam}" height="{tam}" viewBox="0 0 24 24" '
            f'fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" '
            f'stroke-linejoin="round" xmlns="http://www.w3.org/2000/svg">{paths}</svg>')

ICONO_MATERIAL = {"Cartón": "carton", "Papel": "papel", "Plástico": "plastico",
                 "Vidrio": "vidrio", "Metal": "metal", "Basura (no reciclable)": "basura"}

# La correspondencia con colores de contenedores NCh3322 es únicamente visual.
COLORES_UI = {"Cartón": "#235FAD", "Papel": "#235FAD", "Plástico": "#DAA51D",
              "Vidrio": "#3E7B4F", "Metal": "#969B98", "Basura (no reciclable)": "#454D47"}

# Hojas botánicas SVG: monstera con recortes, helecho y eucalipto, todo local.
HOJAS_HERO = r'''<svg class="bot-leaf bot-leaf-monstera" viewBox="0 0 320 370" aria-hidden="true" xmlns="http://www.w3.org/2000/svg">
<defs><mask id="botMonsteraMask"><rect width="320" height="370" fill="black"/>
<path d="M160 343C90 318 41 274 30 193 18 93 86 19 166 19c81 0 141 69 130 159-10 78-60 131-136 165Z" fill="white"/>
<ellipse cx="109" cy="119" rx="9" ry="29" transform="rotate(-35 109 119)" fill="black"/>
<ellipse cx="211" cy="124" rx="9" ry="31" transform="rotate(34 211 124)" fill="black"/>
<ellipse cx="91" cy="200" rx="10" ry="30" transform="rotate(-66 91 200)" fill="black"/>
<ellipse cx="231" cy="202" rx="11" ry="31" transform="rotate(63 231 202)" fill="black"/>
<path d="M23 129 98 168 21 155Z M299 127 220 166 301 155Z M37 238 118 245 58 270Z M281 236 205 245 265 271Z" fill="black"/></mask></defs>
<path d="M160 343C90 318 41 274 30 193 18 93 86 19 166 19c81 0 141 69 130 159-10 78-60 131-136 165Z" fill="#B6D4A8" mask="url(#botMonsteraMask)"/>
<g fill="none" stroke="#E9F7D9" stroke-width="2.2" opacity=".9"><path d="M160 342Q166 205 163 43"/><path d="M163 108Q129 76 95 60M164 143Q201 93 237 79M161 190Q110 142 57 132M162 214Q214 161 264 147M160 265Q106 224 60 222M159 278Q216 224 267 216"/></g></svg>
<svg class="bot-leaf bot-leaf-fern" viewBox="0 0 270 350" aria-hidden="true" xmlns="http://www.w3.org/2000/svg">
<path d="M124 340Q154 207 167 25" fill="none" stroke="#DAEDD4" stroke-width="3" stroke-linecap="round"/>
<g fill="#B6D4A8"><path d="M162 66Q117 44 87 73q44 5 77 16ZM170 67q35-36 68-25-20 28-68 48Z"/>
<path d="M159 107q-55-35-97-8 44 6 96 31ZM167 110q53-43 88-27-39 36-90 48Z"/>
<path d="M155 153q-65-41-110-10 48 11 108 34ZM164 157q51-52 95-33-37 45-98 54Z"/>
<path d="M149 205q-73-39-112-10 56 11 109 31ZM158 205q64-54 107-31-41 41-111 51Z"/>
<path d="M139 260q-69-34-102 1 60 7 99 17ZM150 258q54-42 101-20-42 35-105 41Z"/></g></svg>
<svg class="bot-leaf bot-leaf-eucalyptus" viewBox="0 0 240 270" aria-hidden="true" xmlns="http://www.w3.org/2000/svg">
<path d="M30 250Q115 157 161 18" fill="none" stroke="#D2E6C7" stroke-width="3"/>
<g fill="#B7D1A9"><ellipse cx="124" cy="73" rx="18" ry="40" transform="rotate(-56 124 73)"/>
<ellipse cx="188" cy="75" rx="17" ry="37" transform="rotate(33 188 75)"/>
<ellipse cx="89" cy="130" rx="19" ry="42" transform="rotate(-51 89 130)"/>
<ellipse cx="165" cy="138" rx="18" ry="38" transform="rotate(35 165 138)"/>
<ellipse cx="56" cy="184" rx="18" ry="38" transform="rotate(-45 56 184)"/>
<ellipse cx="121" cy="195" rx="18" ry="41" transform="rotate(40 121 195)"/></g></svg>'''

# ---------------------------------------------------------------------------
# Encabezado
# ---------------------------------------------------------------------------
st.markdown(f"""
<section class="eco-header" aria-label="EcoClasifica, asistente de reciclaje">
  <div class="bot-hero-copy">
    <div class="bot-kicker">NATURALEZA · TECNOLOGÍA · FUTURO</div>
    <div class="bot-wordmark"><span class="bot-logo">{icono_lineal('hoja', 30)}</span>
      <h1>Eco<em>Clasifica</em></h1></div>
    <p>Una forma más consciente de separar nuestros residuos. Descubre qué material tienes entre manos, comprende la confianza del modelo y recibe orientación creada con inteligencia artificial.</p>
    <div class="bot-hero-divider"></div>
    <div class="eco-flujo" aria-label="Flujo de la aplicación">
      <span class="bot-step">{icono_lineal('camara', 15)} Tu imagen</span><span class="bot-step-arrow">→</span>
      <span class="bot-step">{icono_lineal('analizar', 15)} Clasificación</span><span class="bot-step-arrow">→</span>
      <span class="bot-step">{icono_lineal('barras', 15)} Probabilidades</span><span class="bot-step-arrow">→</span>
      <span class="bot-step">{icono_lineal('sparkle', 15)} Guía con Gemini</span>
    </div>
  </div>
  {HOJAS_HERO}
</section>""", unsafe_allow_html=True)
st.markdown(
    f'<div class="eco-aviso">{icono_lineal("shield")}<div><strong>Prototipo educativo.</strong> '
    'Las predicciones pueden equivocarse y no reemplazan las indicaciones de tu municipio o punto limpio.</div></div>',
    unsafe_allow_html=True)

if ERROR_MODELO:
    st.error(f"❌ No se pudo cargar el modelo. {ERROR_MODELO}")
    st.stop()

# ---------------------------------------------------------------------------
# Barra lateral: guía de contenedores y desempeño resumido
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(f'<div class="bot-sidebar-title">{icono_lineal("hoja")} Contenedores NCh3322</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="bot-badges">' + "".join(
            f'<span class="eco-chip" style="background:{c};color:{t}">{html.escape(n)}</span>' for n, c, t in [
            ("Azul · papel y cartón", "#1456A3", "#FFFFFF"),
            ("Amarillo · plásticos", "#E9BF4E", "#27331D"),
            ("Verde · vidrios", "#376B44", "#FFFFFF"),
            ("Gris claro · metales", "#CFD3CD", "#27332B"),
            ("Beige · cartón bebidas", "#D6BCA2", "#30281F"),
            ("Rojo · peligrosos", "#B73D3C", "#FFFFFF"),
            ("Gris oscuro · resto", "#3E4742", "#FFFFFF")]) + '</div>', unsafe_allow_html=True)
    st.caption("Cada comuna puede aceptar materiales distintos. Confirma con tu municipio.")
    if MET:
        e = MET["prueba"]["modelo_desplegado"]
        onnx_acc = MET["prueba"].get("inferencia_onnx_app", {}).get("accuracy")
        st.markdown(f'<div class="bot-sidebar-label">{icono_lineal("barras")} Desempeño en prueba</div>', unsafe_allow_html=True)
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

tab_clasificar, tab_desempeno, tab_acerca = st.tabs(["Clasificar residuo", "Desempeño del modelo", "Acerca del proyecto"])

# ---------------------------------------------------------------------------
# Pestaña 1: clasificar
# ---------------------------------------------------------------------------
with tab_clasificar:
    if "ejemplo" not in st.session_state:
        st.session_state.ejemplo = None

    col_izq, col_der = st.columns([5, 6], gap="large")

    with col_izq:
        origen = st.segmented_control("¿Cómo quieres ingresar la imagen?", ["Subir foto", "Cámara", "Ejemplos"],
                                      default="Subir foto", key="origen")
        imagen, nombre_imagen = None, None

        if origen == "Subir foto":
            archivo = st.file_uploader("Foto del residuo (JPG, PNG o WEBP)", type=["jpg", "jpeg", "png", "webp"])
            if archivo is not None:
                try:
                    imagen, nombre_imagen = Image.open(archivo), archivo.name
                except UnidentifiedImageError:
                    st.error("El archivo no es una imagen válida. Prueba con otra foto (JPG o PNG).")
        elif origen == "Cámara":
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
        st.caption("Para mejores resultados: un solo objeto, centrado, con fondo claro y buena luz.")

    with col_der:
        if imagen is None:
            st.info("Sube una foto, usa la cámara o elige un ejemplo para comenzar.")
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
<div class="eco-tarjeta" style="border-top:4px solid {COLORES_UI[r['clase']]}">
  <div class="eco-icono">{icono_lineal(ICONO_MATERIAL[r['clase']], 30)}</div>
  <div style="flex:1;min-width:0">
    <div class="bot-overline">Material más probable</div>
    <div class="eco-titulo">{html.escape(r['clase'])}</div>
    <div class="bot-result-lead">Contenedor sugerido: <strong>{html.escape(info['contenedor'])}</strong></div>
    <div class="eco-sub">{html.escape(info['nota'])}</div>
    <div class="eco-barra" role="progressbar" aria-label="Confianza de la predicción" aria-valuemin="0" aria-valuemax="100" aria-valuenow="{r['confianza']*100:.1f}">
      <div style="width:{r['confianza']*100:.1f}%;background:{COLORES_UI[r['clase']]}"></div>
    </div>
    <div class="eco-sub">Confianza de <strong>esta imagen</strong>: <strong>{pct(r['confianza'])}</strong></div>
  </div>
</div>""", unsafe_allow_html=True)

            if baja:
                st.markdown(f"""<div class="eco-alerta">{icono_lineal('alerta')}
                <div><b>Confianza baja ({pct(r['confianza'])} &lt; {UMBRAL:.0%}). Requiere revisión humana.</b><br>
                Puede ser <b>{html.escape(r['clase'])}</b> o <b>{html.escape(r['segunda'])}</b>, o un objeto que
                <b>no pertenece</b> a ninguna de las 6 clases (el modelo siempre elige una).
                Revisa el material tú mismo antes de depositarlo.</div></div>""", unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="eco-ok">{icono_lineal("check")}<div>Confianza sobre el umbral de revisión ({UMBRAL:.0%}). '
                            'Aun así, verifica que el residuo esté limpio y que no sea una mezcla de materiales.</div></div>',
                            unsafe_allow_html=True)

            st.markdown(f'<div class="bot-section-heading">{icono_lineal("barras")} Probabilidad de cada clase</div>',
                        unsafe_allow_html=True)
            filas = ""
            for clase, p in sorted(r["probabilidades"].items(), key=lambda kv: -kv[1]):
                c = COLORES_UI[clase]
                filas += (f'<div class="eco-prob"><div class="bot-prob-label">'
                          f'{icono_lineal(ICONO_MATERIAL[clase])}<span>{html.escape(clase)}</span></div>'
                          f'<div class="pista" role="progressbar" aria-label="Probabilidad {html.escape(clase)}" '
                          f'aria-valuenow="{p*100:.1f}" aria-valuemin="0" aria-valuemax="100">'
                          f'<div style="width:{p*100:.1f}%;background:{c}"></div></div>'
                          f'<div class="bot-prob-value">{p:.0%}</div></div>')
            st.markdown(filas, unsafe_allow_html=True)

            if MET:
                e = MET["prueba"]["modelo_desplegado"]
                onnx_acc = MET["prueba"].get("inferencia_onnx_app", {}).get("accuracy", e["accuracy"])
                st.markdown(f"""<div class="eco-kpis">
<div class="eco-kpi"><b>{pct(onnx_acc)}</b><span>Accuracy ONNX (app) en prueba</span></div>
<div class="eco-kpi"><b>{pct(e['balanced_accuracy'])}</b><span>Balanced accuracy PyTorch en prueba</span></div>
<div class="eco-kpi"><b>{UMBRAL:.0%}</b><span>Umbral de revisión (elegido en validación)</span></div></div>""",
                            unsafe_allow_html=True)
                st.caption("La **confianza** es de esta imagen; la **accuracy** es del modelo sobre todo el conjunto de prueba. "
                           "Son cosas distintas: una predicción con confianza alta también puede estar equivocada.")

            st.divider()
            st.markdown(f'<div class="bot-section-heading">{icono_lineal("sparkle")} Recomendación de reciclaje con IA</div>', unsafe_allow_html=True)
            st.caption("Se envía a Gemini solo texto: la clase, la confianza y la segunda opción. La foto no se envía.")
            if st.button("Obtener recomendación con IA (Gemini)", type="primary", width="stretch"):
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

    with st.expander("Límites del modelo (léelo antes de usar la app)"):
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
