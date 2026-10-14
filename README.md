# ♻️ EcoClasifica — Clasificación inteligente de residuos para reciclaje

Aplicación web que recibe la foto de un residuo, estima su material (**cartón, papel, plástico, vidrio, metal o basura no reciclable**) con un modelo preentrenado ajustado por *transfer learning* y genera con **Google Gemini** una recomendación para separarlo y prepararlo correctamente.

📷 Imagen → 🧠 EfficientNet-B0 (clase + confianza) → 📊 Resultado visual → 💬 Gemini → ✅ Recomendación

| | Enlace |
|---|---|
| 🌐 App publicada | ⏳ *PENDIENTE: `https://<nombre>.streamlit.app`* |
| 💻 Repositorio | ⏳ *PENDIENTE: `https://github.com/<usuario>/eco-clasifica`* |
| 📊 Dataset | https://github.com/garythung/trashnet |

## 👥 Integrantes
- ⏳ *(Nombre 1)*
- ⏳ *(Nombre 2)*
- ⏳ *(Nombre 3)*

---

## 1. Problema y motivación
Separar mal los residuos contamina los contenedores: un envase sucio o un material no reciclable puede inutilizar un lote completo. Muchas personas dudan sobre en qué contenedor va cada cosa. **EcoClasifica** orienta a hogares, colegios y oficinas: estima el material a partir de una foto, sugiere el contenedor según la norma chilena **NCh3322** y explica cómo prepararlo. La app **no afirma que algo sea reciclable**: eso depende de que esté limpio, no sea una mezcla de materiales y de lo que acepte cada municipio.

## 2. Datos — ficha del dataset
| Campo | Detalle |
|---|---|
| Nombre | **TrashNet** |
| Autores | Gary Thung y Mindy Yang (Stanford University, curso CS229, 2016) |
| Cómo se obtuvo | Fotografías de residuos sobre cartulina blanca, con luz solar o de interior; iPhone 7 Plus, 5S y SE. Reducidas a 512 × 384 px |
| Licencia | **MIT** — © 2017 Gary Thung (ver [`LICENSE`](LICENSE)) |
| Enlace | https://github.com/garythung/trashnet · https://huggingface.co/datasets/garythung/trashnet |
| Total | 2.527 imágenes, 6 clases |

| Clase | Imágenes |
|---|---|
| Papel | 594 |
| Vidrio | 501 |
| Plástico | 482 |
| Metal | 410 |
| Cartón | 403 |
| Basura (no reciclable) | 137 |

- **Desbalance:** *Basura* tiene 4,3 veces menos imágenes que *Papel*. Lo compensamos con división estratificada, pesos por clase en la pérdida y *balanced accuracy* como métrica principal.
- **División:** 70 % entrenamiento / 15 % validación / 15 % prueba, estratificada (semilla 42). El conteo por clase y por conjunto está en el notebook (sección 2).
- **Limitaciones:** fondo blanco y un objeto por foto (en la vida real hay fondos variados y varios objetos); pocas imágenes de *Basura*; envases de EE. UU.; solo 6 clases cerradas (el modelo no reconoce pilas, tetrapak, orgánicos, etc.).
- El dataset **no** está en este repositorio: el notebook lo descarga desde su fuente original.

## 3. Modelo y metodología
| Paso | Decisión |
|---|---|
| Modelo principal | **EfficientNet-B0** (`timm`), preentrenado en ImageNet, ajustado completo durante 12 épocas (AdamW, *cosine schedule*, pérdida con pesos por clase y *label smoothing*, aumento de datos) |
| Línea base | **CLIP ViT-B/32 zero-shot** (sin entrenar), con 3 descripciones por clase |
| Selección del enfoque | Mayor *balanced accuracy* en **validación** |
| Selección de la época | Mejor *balanced accuracy* en validación |
| Umbral de revisión humana | Elegido en **validación**: el menor umbral con el que las predicciones aceptadas logran ≥95 % de accuracy |
| Evaluación final | **Prueba**, usada una sola vez: accuracy, balanced accuracy, precisión y recall por clase, matriz de confusión, errores costosos |
| Exportación | `.pt` (PyTorch) + `.onnx` (lo usa la app). El notebook compara ONNX y PyTorch: 379 de 380 predicciones iguales y accuracy ONNX de 88,42 % |

### Resultados
| Enfoque | Accuracy (val) | Balanced acc. (val) | Accuracy (prueba) | Balanced acc. (prueba) |
|---|---|---|---|---|
| CLIP zero-shot | 80,47 % | 80,79 % | 77,11 % | 73,10 % |
| EfficientNet-B0 (PyTorch) | 86,81 % | 85,93 % | 88,68 % | 88,84 % |

- **Enfoque elegido en validación:** EfficientNet-B0, por superar a CLIP en 5,14 puntos porcentuales de balanced accuracy en validación.
- **Prueba PyTorch:** 337 de 380 imágenes correctas (88,68 % de accuracy).
- **Prueba de la app ONNX:** 336 de 380 imágenes correctas (88,42 % de accuracy). Sus predicciones coinciden con PyTorch en **379 de 380 imágenes (99,74 %)**. La diferencia se debe a la exportación/inferencia, que puede producir variaciones numéricas. La matriz de confusión y la balanced accuracy de la tabla son las calculadas con PyTorch. No se calculó una balanced accuracy separada para ONNX.
- **Umbral de revisión humana:** 60 %, elegido en validación. Con PyTorch, 95,49 % de aciertos para las predicciones aceptadas en validación (75,99 % de cobertura), y 96 % en prueba (78,95 % de cobertura).
- **Fotos reales del grupo:** todavía no se realizó esta prueba complementaria.

### Error más costoso
**Basura clasificada como reciclable**, porque contamina el contenedor; y **vidrio clasificado como papel, cartón o plástico**, por el riesgo de cortes y daño a la maquinaria. La sección 8 del notebook cuenta cuántas veces ocurren en prueba.

## 4. La aplicación
- Entrada por **archivo, cámara o ejemplos clicables** (imágenes del conjunto de prueba).
- **Clase**, **confianza de la predicción** y **probabilidades de las 6 clases**.
- **Accuracy y balanced accuracy en prueba**, separadas explícitamente de la confianza.
- **Advertencias:** prototipo educativo; revisión humana cuando la confianza está bajo el umbral; aviso de que el modelo no reconoce objetos fuera de las 6 clases; el material identificado **no** se presenta como automáticamente reciclable.
- Colores de contenedor según **NCh3322**: azul (papel y cartón), amarillo (plásticos), verde (vidrio), **gris claro (metales)**, beige (cartón para bebidas), rojo (peligrosos) y gris oscuro (resto).
- Botón de **recomendación con Gemini**.
- Manejo de errores: modelo faltante, imagen inválida, clave ausente o inválida, cuota agotada y modelo de Gemini no disponible (prueba modelos alternativos).

### Prompt responsable (en `nucleo.py`)
El prompt limita a Gemini a temas de reciclaje y le indica que el clasificador puede equivocarse y solo conoce 6 clases. Con confianza baja, debe advertir y dar opciones para las dos clases más probables. Además le pide no afirmar "es reciclable" sin condiciones, advertir sobre residuos sucios, mezclados y peligrosos, usar los colores NCh3322 y recordar que cada municipio tiene reglas propias. A Gemini solo se envía **texto**: la clase, la confianza y la segunda opción, nunca la foto. La temperatura es 0,3.

### Seguridad de la clave
La clave **no está en el código ni en el repositorio**. Se lee del secreto `GEMINI_API_KEY` (Streamlit Cloud: *Settings → Secrets*). El archivo `.streamlit/secrets.toml` está en `.gitignore`.

### Publicación
- **Principal: Streamlit Community Cloud** (gratis) → `app.py`.
- **Alternativa: Hugging Face Spaces (Gradio)** → `app_gradio.py`. Desde mediados de 2026 la comunidad reporta que las cuentas gratuitas nuevas no pueden crear Spaces de Gradio en *CPU Basic* sin PRO, por eso no es la opción principal.

## 5. Estructura del repositorio
```
eco-clasifica/
├── app.py                     ← app principal (Streamlit)
├── app_gradio.py              ← versión alternativa (Gradio)
├── nucleo.py                  ← lógica compartida: modelo ONNX, preprocesamiento, Gemini
├── requirements.txt
├── README.md
├── LICENSE                    ← MIT (código) + licencia del dataset TrashNet
├── .gitignore
├── .streamlit/
│   ├── config.toml            ← tema visual
│   └── secrets.toml.example   ← ejemplo (la clave real va en Secrets, nunca aquí)
├── notebooks/
│   └── entrenamiento.ipynb    ← ejecutado en Google Colab, con métricas y resultados
├── modelo/                    ← artefactos de entrenamiento incluidos
│   ├── modelo_residuos.onnx
│   ├── modelo_residuos.pt
│   ├── clases.json
│   ├── metricas.json
│   └── matriz_confusion.png
└── ejemplos/                  ← 6 imágenes de prueba incluidas
```

## 6. Cómo ejecutarlo
**Entrenar:** abrir `notebooks/entrenamiento.ipynb` en Google Colab con GPU T4 → *Ejecutar todas* → se descarga `entrega_modelo.zip` con `modelo/` y `ejemplos/`.

**App en tu computador (opcional):**
```bash
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # y pega tu clave dentro
streamlit run app.py
```

## 7. Declaración de uso de IA
- **Claude (Anthropic):** generó la primera versión y las correcciones del notebook, `app.py`, `app_gradio.py`, `nucleo.py`, el README, la guía y la presentación a partir de la pauta del certamen.
- **ChatGPT (OpenAI):** revisó la entrega y ayudó a integrar los pesos, las métricas reales y el notebook ejecutado; documentó la diferencia PyTorch/ONNX y completó la presentación.
- **Google Colab:** entorno utilizado por el grupo para ejecutar el entrenamiento y obtener las métricas.
- **Google Gemini:** integrado para generar recomendaciones de reciclaje; la llamada real y la publicación aún deben probarse.
- **Pendiente del grupo:** describir qué modificaciones propias realizaron, además de ejecutar y validar el proyecto.

## 8. Consideraciones éticas
- Prototipo **educativo**: no reemplaza las indicaciones de cada municipio.
- Privacidad: no se usan fotos de personas; la foto se procesa en el servidor y no se guarda, y a Gemini solo se envía texto.
- Sesgos: el dataset tiene un solo tipo de fondo, luz controlada y envases de otro país. La prueba con fotos reales propias quedó pendiente (sección 11 del notebook); la limitación está advertida en la app.

## Créditos
Dataset TrashNet © 2017 Gary Thung, licencia MIT. EfficientNet (Tan & Le, 2019) vía `timm`. CLIP (Radford et al., 2021) vía Hugging Face `transformers`. Colores de contenedores: norma chilena NCh3322 (Ministerio del Medio Ambiente).
