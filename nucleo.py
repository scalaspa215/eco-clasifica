"""
nucleo.py — Lógica compartida de EcoClasifica (sin interfaz).

La usan las dos interfaces:
  - app.py         → Streamlit (publicación principal, Streamlit Community Cloud, gratis)
  - app_gradio.py  → Gradio (alternativa, Hugging Face Spaces)

Contiene: carga del modelo ONNX, preprocesamiento (idéntico al del notebook),
predicción, información de contenedores (NCh3322) y la llamada a Gemini.
No usa PyTorch: el modelo se exporta a ONNX en Colab y aquí se ejecuta con onnxruntime,
lo que hace la app más liviana y rápida de instalar en servidores gratuitos.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

BASE = Path(__file__).parent
CARPETA_MODELO = BASE / "modelo"
CARPETA_EJEMPLOS = BASE / "ejemplos"

# ---------------------------------------------------------------------------
# Contenedores según la norma chilena NCh3322 (colores publicados por el
# Ministerio del Medio Ambiente). La aceptación final depende de cada comuna.
# ---------------------------------------------------------------------------
INFO_CLASES = {
    "Cartón": {"icono": "📦", "contenedor": "Azul — papeles y cartones", "color": "#1565c0",
               "nota": "Potencialmente reciclable si está limpio, seco y sin grasa."},
    "Papel": {"icono": "📄", "contenedor": "Azul — papeles y cartones", "color": "#1565c0",
              "nota": "Potencialmente reciclable si está limpio y seco (no servilletas ni papel higiénico usados)."},
    "Plástico": {"icono": "🧴", "contenedor": "Amarillo — plásticos", "color": "#f9a825",
                 "nota": "Potencialmente reciclable si está limpio y vacío; revisa qué tipos de plástico acepta tu comuna."},
    "Vidrio": {"icono": "🍾", "contenedor": "Verde — vidrios", "color": "#2e7d32",
               "nota": "Potencialmente reciclable (botellas y frascos). No incluye cerámica, cristalería, espejos ni ampolletas."},
    "Metal": {"icono": "🥫", "contenedor": "Gris claro — metales", "color": "#9e9e9e",
              "nota": "Potencialmente reciclable si está limpio y vacío. Aerosoles y envases de químicos requieren cuidado especial."},
    "Basura (no reciclable)": {"icono": "🗑️", "contenedor": "Gris oscuro — resto de residuos", "color": "#424242",
                               "nota": "Probablemente no reciclable: va a la basura domiciliaria."},
}

AVISO_GENERAL = ("El modelo solo conoce 6 materiales (cartón, papel, plástico, vidrio, metal y basura). "
                 "Siempre elige uno de ellos, incluso si el objeto no corresponde a ninguno, así que **no puede "
                 "identificar de forma confiable objetos ajenos** (pilas, electrónicos, orgánicos, tetrapak, ropa, etc.). "
                 "El resultado **no garantiza** que el residuo sea reciclable: depende de si está limpio, si es una mezcla "
                 "de materiales y de lo que acepte tu municipio o punto limpio.")


# ---------------------------------------------------------------------------
# Carga del modelo y de los archivos generados por el notebook
# ---------------------------------------------------------------------------
@dataclass
class Clasificador:
    sesion: object
    clases: list
    img_size: int
    media: np.ndarray
    desv: np.ndarray
    metricas: dict | None


def cargar_json(ruta: Path):
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def cargar_clasificador() -> Clasificador:
    """Carga modelo/modelo_residuos.onnx + clases.json (+ metricas.json si existe).
    Lanza FileNotFoundError con un mensaje claro si falta algo."""
    import onnxruntime as ort

    faltan = [n for n in ("modelo_residuos.onnx", "clases.json") if not (CARPETA_MODELO / n).exists()]
    if faltan:
        raise FileNotFoundError(
            f"Faltan archivos en la carpeta modelo/: {', '.join(faltan)}. "
            "Se generan al ejecutar notebooks/entrenamiento.ipynb en Colab (descargar entrega_modelo.zip)."
        )
    cfg = cargar_json(CARPETA_MODELO / "clases.json")
    sesion = ort.InferenceSession(str(CARPETA_MODELO / "modelo_residuos.onnx"),
                                  providers=["CPUExecutionProvider"])
    metricas = cargar_json(CARPETA_MODELO / "metricas.json") if (CARPETA_MODELO / "metricas.json").exists() else None
    return Clasificador(sesion, cfg["clases"], cfg["img_size"],
                        np.array(cfg["media"], dtype=np.float32), np.array(cfg["desv"], dtype=np.float32), metricas)


# ---------------------------------------------------------------------------
# Preprocesamiento — DEBE ser idéntico a `preprocesar_np` del notebook
# ---------------------------------------------------------------------------
def preprocesar(img: Image.Image, img_size: int, media: np.ndarray, desv: np.ndarray) -> np.ndarray:
    """Corrige la rotación EXIF del celular → RGB → 224x224 (bilineal) → [0,1] → normaliza (ImageNet).
    Devuelve un arreglo (1, 3, 224, 224) float32."""
    img = ImageOps.exif_transpose(img).convert("RGB")
    img = img.resize((img_size, img_size), Image.BILINEAR)
    x = np.asarray(img, dtype=np.float32) / 255.0
    x = (x - media) / desv
    return x.transpose(2, 0, 1)[np.newaxis].astype(np.float32)


def softmax(z: np.ndarray) -> np.ndarray:
    z = z - z.max(axis=-1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=-1, keepdims=True)


def clasificar(clf: Clasificador, img: Image.Image) -> dict:
    """Devuelve un diccionario con la clase, la confianza, la segunda opción y las 6 probabilidades."""
    x = preprocesar(img, clf.img_size, clf.media, clf.desv)
    logits = clf.sesion.run(None, {clf.sesion.get_inputs()[0].name: x})[0]
    probs = softmax(logits)[0]
    orden = probs.argsort()[::-1]
    return {
        "clase": clf.clases[orden[0]],
        "confianza": float(probs[orden[0]]),
        "segunda": clf.clases[orden[1]],
        "confianza_segunda": float(probs[orden[1]]),
        "probabilidades": {clf.clases[i]: float(probs[i]) for i in range(len(clf.clases))},
    }


def umbral(clf: Clasificador) -> float:
    """Umbral de revisión humana elegido con el conjunto de VALIDACIÓN en el notebook."""
    if clf.metricas and "umbral_confianza" in clf.metricas:
        return float(clf.metricas["umbral_confianza"]["valor"])
    return 0.60  # solo se usa si aún no existe metricas.json


# ---------------------------------------------------------------------------
# Recomendación con Gemini (IA generativa)
# ---------------------------------------------------------------------------
# Modelo configurable con la variable/secreto GEMINI_MODEL. Si no responde, se prueban los siguientes.
MODELOS_RESPALDO = ["gemini-3.5-flash-lite", "gemini-3.6-flash", "gemini-flash-lite-latest", "gemini-flash-latest"]


def modelos_gemini() -> list[str]:
    preferido = leer_secreto("GEMINI_MODEL")
    return ([preferido] if preferido else []) + [m for m in MODELOS_RESPALDO if m != preferido]

INSTRUCCIONES_SISTEMA = """Eres EcoGuía, asistente de reciclaje domiciliario en Chile.
Reglas obligatorias:
- Responde SOLO sobre separación, preparación y disposición de residuos. Si te piden otra cosa, dilo amablemente y vuelve al tema.
- Recibes el resultado de un clasificador automático de imágenes que solo conoce 6 clases (cartón, papel, plástico, vidrio, metal, basura) y puede equivocarse. No inventes características del objeto que no conoces.
- Nunca afirmes que el residuo "es reciclable" sin condiciones: depende de que esté limpio, seco, vacío, no mezclado con otros materiales y de lo que acepte el municipio o punto limpio.
- Si la confianza es BAJA: empieza advirtiendo que la clasificación es incierta y que el objeto podría no pertenecer a ninguna de las 6 clases; pide que una persona lo verifique y da indicaciones para las dos opciones más probables.
- Advierte sobre residuos sucios (restos de comida o grasa), mezclados (envases de varios materiales, como tetrapak o envases con etiquetas metalizadas) y peligrosos o especiales (vidrio roto, pilas, aerosoles, envases de químicos o aceites, electrónicos), que NO van al reciclaje común. Prioriza la seguridad.
- Usa los colores de la norma chilena NCh3322: azul (papeles y cartones), amarillo (plásticos), verde (vidrios), gris claro (metales), beige (cartón para bebidas), rojo (residuos peligrosos), gris oscuro (resto de residuos). Recuerda que cada comuna puede tener reglas distintas.
- Español de Chile, claro y breve (máximo 180 palabras). Formato Markdown con estas secciones:
  **¿Dónde va?**, **Cómo prepararlo**, **Ojo con…** y **Dato útil**."""


def construir_prompt(r: dict, umbral_conf: float) -> str:
    nivel = "BAJA" if r["confianza"] < umbral_conf else "ALTA"
    return (
        "Resultado del clasificador de residuos (texto; no se envía la imagen):\n"
        f"- Clase más probable: {r['clase']} (confianza {r['confianza']:.0%})\n"
        f"- Segunda opción: {r['segunda']} (confianza {r['confianza_segunda']:.0%})\n"
        f"- Nivel de confianza: {nivel} (umbral de revisión humana: {umbral_conf:.0%})\n\n"
        "Genera la recomendación de reciclaje para este residuo."
    )


class ErrorGemini(Exception):
    """Error con un mensaje apto para mostrar al usuario (nunca incluye la clave)."""


def recomendar_gemini(r: dict, umbral_conf: float, clave: str | None) -> tuple[str, str]:
    """Devuelve (texto_markdown, modelo_usado). Lanza ErrorGemini con un mensaje claro si falla."""
    if not clave:
        raise ErrorGemini("Falta configurar el secreto GEMINI_API_KEY en la plataforma donde está publicada la app.")
    from google import genai
    from google.genai import errors, types

    cliente = genai.Client(api_key=clave)
    config = types.GenerateContentConfig(system_instruction=INSTRUCCIONES_SISTEMA, temperature=0.3,
                                         max_output_tokens=700)
    ultimo_error = None
    for modelo in modelos_gemini():
        try:
            resp = cliente.models.generate_content(model=modelo, contents=construir_prompt(r, umbral_conf), config=config)
            texto = (resp.text or "").strip()
            if texto:
                return texto, modelo
            ultimo_error = "respuesta vacía"
        except errors.ClientError as e:  # 4xx
            codigo = getattr(e, "code", None)
            if codigo in (401, 403) or "API key" in str(e) or "API_KEY" in str(e):
                raise ErrorGemini("La clave GEMINI_API_KEY no es válida o no tiene permisos.") from None
            if codigo == 429:
                raise ErrorGemini("Se alcanzó el límite gratuito de Gemini por minuto. Espera unos segundos e intenta de nuevo.") from None
            ultimo_error = f"{modelo}: error {codigo}"  # 404 u otro → probar el siguiente modelo
        except errors.ServerError as e:  # 5xx
            ultimo_error = f"{modelo}: servidor no disponible ({getattr(e, 'code', '')})"
        except Exception as e:  # sin conexión, etc.
            ultimo_error = f"{type(e).__name__}"
    raise ErrorGemini(f"No se pudo obtener la recomendación ({ultimo_error}). Intenta nuevamente en unos segundos.")


def leer_secreto(nombre: str) -> str | None:
    """Lee un secreto desde variables de entorno (Hugging Face, Colab, local)
    o desde los Secrets de Streamlit Cloud. Nunca lo muestra en pantalla."""
    valor = os.environ.get(nombre)
    if valor:
        return valor.strip()
    try:
        import streamlit as st
        valor = st.secrets.get(nombre)
        return str(valor).strip() if valor else None
    except Exception:
        return None


def leer_clave_gemini() -> str | None:
    return leer_secreto("GEMINI_API_KEY")
