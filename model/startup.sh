#!/bin/bash
set -e

echo "🚀 Iniciando el servicio de QuistBuilder..."

# Verificar si la base vectorial existe
if [ ! -d "chroma_db" ] || [ -z "$(ls -A chroma_db)" ]; then
    echo "📚 Base vectorial no encontrada. Reconstruyendo..."
    python md_to_chroma.py
    echo "✅ Base vectorial reconstruida correctamente."
else
    echo "✅ Base vectorial encontrada."
fi

# Iniciar el servidor FastAPI
echo "🌐 Iniciando el servidor FastAPI..."
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}
