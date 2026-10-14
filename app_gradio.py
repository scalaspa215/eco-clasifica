"""
EcoClasifica ♻️ — Versión ALTERNATIVA en Gradio (Hugging Face Spaces)
=====================================================================
La publicación principal del proyecto es app.py (Streamlit Community Cloud), porque desde
mediados de 2026 las cuentas gratuitas nuevas de Hugging Face no pueden crear Spaces de Gradio
en "CPU Basic" sin suscripción PRO. Usa esta versión solo si tienes acceso a un Space de Gradio.

Ejecutar localmente:  pip install gradio==6.30.0  y luego  python app_gradio.py
Comparte toda la lógica con app.py a través de nucleo.py (mismo modelo y mismo preprocesamiento).
"""

import gradio as gr

import nucleo

try:
    CLF = nucleo.cargar_clasificador()
    ERROR_MODELO = None
except Exception as e:
    CLF, ERROR_MODELO = None, str(e)

UMBRAL = nucleo.umbral(CLF) if CLF else 0.60
MET = CLF.metricas if CLF else None
CLASES = CLF.clases if CLF else list(nucleo.INFO_CLASES)


def pct(x):
    return f"{x:.1%}".replace(".", ",")


def tarjeta(r):
    info = nucleo.INFO_CLASES[r["clase"]]
    html = f"""
<div class="tarjeta" style="border-left:8px solid {info['color']}">
  <div class="icono">{info['icono']}</div>
  <div><div class="sub">Material más probable</div><div class="titulo">{r['clase']}</div>
  <div class="sub">Contenedor sugerido: <b>{info['contenedor']}</b></div><div class="sub">{info['nota']}</div>
  <div class="barra"><div style="width:{r['confianza']*100:.1f}%;background:{info['color']}"></div></div>
  <div class="sub">Confianza de <b>esta predicción</b>: <b>{pct(r['confianza'])}</b></div></div>
</div>"""
    if r["confianza"] < UMBRAL:
        html += (f'<div class="alerta">⚠️ <b>Confianza baja ({pct(r["confianza"])} &lt; {UMBRAL:.0%}). Requiere revisión humana.</b> '
                 f'Puede ser {r["clase"]} o {r["segunda"]}, o un objeto que no pertenece a ninguna de las 6 clases.</div>')
    return html


def clasificar(img):
    if ERROR_MODELO:
        return f'<div class="alerta">❌ {ERROR_MODELO}</div>', None, None, gr.update(interactive=False)
    if img is None:
        return "Sube una foto o elige un ejemplo.", None, None, gr.update(interactive=False)
    try:
        r = nucleo.clasificar(CLF, img)
    except Exception as e:
        return f'<div class="alerta">No se pudo procesar la imagen ({type(e).__name__}).</div>', None, None, gr.update(interactive=False)
    return tarjeta(r), r["probabilidades"], r, gr.update(interactive=True)


def recomendar(r):
    if not r:
        return "Primero clasifica una imagen."
    try:
        texto, modelo = nucleo.recomendar_gemini(r, UMBRAL, nucleo.leer_clave_gemini())
        return texto + f"\n\n---\n*Generado por IA ({modelo}). Verifica con tu municipio o punto limpio.*"
    except nucleo.ErrorGemini as e:
        return f"❌ {e}"


def texto_desempeno():
    if not MET:
        return "⚠️ Aún no hay métricas: ejecuta el notebook."
    s, p, u = MET["seleccion"], MET["prueba"], MET["umbral_confianza"]
    d = p["modelo_desplegado"]
    filas = "\n".join(f"| {c} | {pct(d['precision_por_clase'][c])} | {pct(d['recall_por_clase'][c])} |" for c in d["recall_por_clase"])
    return f"""
### Selección del enfoque (validación)
| Enfoque | Accuracy | Balanced accuracy |
|---|---|---|
| EfficientNet-B0 | {pct(s['validacion']['efficientnet_b0']['accuracy'])} | {pct(s['validacion']['efficientnet_b0']['balanced_accuracy'])} |
| CLIP zero-shot | {pct(s['validacion']['clip_zero_shot']['accuracy'])} | {pct(s['validacion']['clip_zero_shot']['balanced_accuracy'])} |

Ganador en validación: **{s['ganador_validacion']}** · Modelo en la app: **{s['modelo_desplegado']}**. {s['motivo']}

### Evaluación final en prueba ({MET['n_imagenes']['test']} imágenes)
| Enfoque | Accuracy | Balanced accuracy |
|---|---|---|
| EfficientNet-B0 | {pct(p['efficientnet_b0']['accuracy'])} | {pct(p['efficientnet_b0']['balanced_accuracy'])} |
| CLIP zero-shot | {pct(p['clip_zero_shot']['accuracy'])} | {pct(p['clip_zero_shot']['balanced_accuracy'])} |

> La **accuracy** es del modelo sobre todo el conjunto de prueba; la **confianza** es de una sola imagen.

| Clase | Precisión | Recall |
|---|---|---|
{filas}

**Umbral de revisión humana: {u['valor']:.0%}** ({u['criterio']}).
"""


CSS = """
.gradio-container {max-width:1150px !important; margin:auto;}
#encabezado {background:linear-gradient(120deg,#1b5e20,#2e7d32 45%,#00897b); color:#fff; padding:22px 28px; border-radius:18px;}
#encabezado h1 {color:#fff; margin:0;} #encabezado p {color:#e8f5e9; margin:6px 0 0;}
.aviso {background:#fff8e1; border:1px solid #ffe082; color:#5d4037; padding:10px 14px; border-radius:12px;}
.tarjeta {display:flex; gap:16px; align-items:center; padding:16px; border-radius:14px; box-shadow:0 2px 10px rgba(0,0,0,.08);}
.icono {font-size:3em;} .titulo {font-size:1.5em; font-weight:800;} .sub {opacity:.85; margin-top:3px;}
.barra {height:10px; background:#e0e0e0; border-radius:6px; margin-top:8px; width:260px; max-width:100%;}
.barra > div {height:10px; border-radius:6px;}
.alerta {margin-top:10px; background:#ffebee; border:1px solid #ef9a9a; color:#b71c1c; padding:10px 14px; border-radius:12px;}
"""
TEMA = gr.themes.Soft(primary_hue="green", secondary_hue="teal")
ejemplos = sorted(str(p) for p in nucleo.CARPETA_EJEMPLOS.glob("*.jpg"))

with gr.Blocks(title="EcoClasifica ♻️") as demo:
    gr.HTML('<div id="encabezado"><h1>♻️ EcoClasifica</h1><p>Sube una foto de un residuo: la IA estima su material, '
            'sugiere el contenedor y explica cómo prepararlo.</p></div>')
    gr.HTML('<div class="aviso">🎓 <b>Prototipo educativo</b> — proyecto académico. Puede equivocarse; no reemplaza las '
            'indicaciones de tu municipio.</div>')
    estado = gr.State(None)
    with gr.Tabs():
        with gr.Tab("🔍 Clasificar residuo"):
            with gr.Row():
                with gr.Column(scale=5):
                    entrada = gr.Image(type="pil", label="Foto del residuo", sources=["upload", "webcam", "clipboard"], height=320)
                    boton = gr.Button("🔍 Clasificar", variant="primary")
                    if ejemplos:
                        gr.Examples(ejemplos, inputs=entrada, label="🧪 Ejemplos (conjunto de prueba)")
                with gr.Column(scale=6):
                    salida = gr.HTML("Sube una foto o elige un ejemplo.")
                    probs = gr.Label(label="📊 Probabilidad de cada clase", num_top_classes=len(CLASES))
                    if MET:
                        d = MET["prueba"]["modelo_desplegado"]
                        gr.Markdown(f"**Accuracy en prueba:** {pct(d['accuracy'])} · **Balanced accuracy:** {pct(d['balanced_accuracy'])} · "
                                    f"**Umbral de revisión:** {UMBRAL:.0%}  \n*La confianza es de esta imagen; la accuracy, del modelo completo.*")
            boton_ia = gr.Button("✨ Obtener recomendación con IA (Gemini)", interactive=False)
            reco = gr.Markdown()
            gr.Markdown(f"⚠️ {nucleo.AVISO_GENERAL}")
        with gr.Tab("📊 Desempeño del modelo"):
            gr.Markdown(texto_desempeno())
            if (nucleo.CARPETA_MODELO / "matriz_confusion.png").exists():
                gr.Image(str(nucleo.CARPETA_MODELO / "matriz_confusion.png"), show_label=False, interactive=False)

    outs = [salida, probs, estado, boton_ia]
    boton.click(clasificar, entrada, outs)
    entrada.change(clasificar, entrada, outs)
    entrada.change(lambda: "", outputs=reco)
    boton_ia.click(lambda: "⏳ Consultando a Gemini…", outputs=reco).then(recomendar, estado, reco)

if __name__ == "__main__":
    demo.launch(theme=TEMA, css=CSS)
