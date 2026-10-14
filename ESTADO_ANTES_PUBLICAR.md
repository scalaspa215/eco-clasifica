# EcoClasifica — estado de integración

Versión integrada a partir de la entrega de Claude (V2) y de los resultados reales descargados de Google Colab.

## Confirmado por los archivos
- 2.527 imágenes TrashNet; división 1.768 entrenamiento / 379 validación / 380 prueba.
- EfficientNet-B0 supera a CLIP en balanced accuracy de validación (85,93 % vs. 80,79 %).
- PyTorch: accuracy 337/380 = 88,68 %, balanced accuracy 88,84 %.
- ONNX (versión de la app): accuracy 336/380 = 88,42 %. Coincidencia ONNX/PyTorch: 379/380.
- El notebook ejecutado está incluido en `notebooks/entrenamiento.ipynb`.
- Archivos de modelo, ejemplos y matriz están incluidos.

## Por hacer antes de entregar
1. Completar nombres de integrantes en README y portada de la presentación.
2. Publicar código en GitHub y app en Streamlit; completar enlaces.
3. Configurar `GEMINI_API_KEY` en Secrets de Streamlit, probar el botón con la app pública (no subir la clave).
4. Probar desde celular y tomar capturas/grabar un video de respaldo.
5. Descargar PDF final una vez añadidos nombres y link; ensayar 10 minutos.
6. Recomendada: evaluación con fotos reales del grupo (actualmente no se ejecutó).

**Importante**: la matriz de confusión, precisión/recall por clase y balanced accuracy provienen de PyTorch; la app usa ONNX (una predicción diferente). Se aclara en la interfaz y en README.
