#!/bin/bash
set -e

# Si no hay terminal (doble clic en GUI), abrir en Konsole
if [ ! -t 0 ]; then
    if command -v konsole &> /dev/null; then
        konsole --noclose -e "$0" "$@"
        exit 0
    else
        xterm -e "$0" "$@"
        exit 0
    fi
fi

echo "🚀 Iniciando Analizavet V2 (Fase Desarrollo - uv)"

# 1. Verificar/instalar uv
if ! command -v uv &> /dev/null; then
    echo "📦 Instalando uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.cargo/env
fi

# 2. Verificar Python 3.11
if ! uv run python --version | grep -q "3.11"; then
    echo "⚠️  Requiere Python 3.11. Instalando..."
    uv python install 3.11
fi

# 3. Crear entorno virtual si no existe
if [ ! -d ".venv" ]; then
    echo "🔧 Creando entorno virtual..."
    uv venv .venv
fi

# 4. Instalar dependencias (uv.lock se genera automáticamente)
echo "📥 Instalando dependencias..."
uv pip install -r requirements.txt

# 5. Verificar que existe la carpeta static (CRITICAL per skill-santiago Leccion #1)
if [ ! -d "app/static" ]; then
    echo "📁 Creando directorio static/..."
    mkdir -p app/static/css app/static/js app/static/images
fi

# 6. Crear directorio images si no existe
if [ ! -d "images" ]; then
    echo "📁 Creando directorio images/..."
    mkdir -p images
fi

# 7. Verificar Redis para Dramatiq
echo "🔍 Verificando Redis..."
if ! redis-cli ping &> /dev/null; then
    echo "⚠️  Redis no está corriendo. Iniciando Redis..."
    redis-server --daemonize yes
    sleep 2
    if redis-cli ping | grep -q "PONG"; then
        echo "✅ Redis iniciado correctamente"
    else
        echo "❌ No se pudo iniciar Redis. Instálalo con: sudo apt install redis-server"
        exit 1
    fi
else
    echo "✅ Redis ya está corriendo"
fi

# 8. Iniciar Dramatiq workers en segundo plano
echo "🎭 Iniciando workers de Dramatiq..."
uv run dramatiq app.tasks --threads 2 --processes 1 &
DRAMATIQ_PID=$!

# 9. Iniciar servidor FastAPI
echo "🌐 Iniciando servidor FastAPI..."
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
SERVER_PID=$!

# 10. Esperar que el puerto esté listo
echo "⏳ Esperando servidor..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health &> /dev/null; then
        echo "✅ Servidor listo en http://localhost:8000"
        break
    fi
    sleep 0.5
done

# 11. Abrir Firefox (sin bloquear terminal - skill-santiago Regla #4)
echo "🦊 Abriendo navegador..."
nohup firefox --new-tab http://localhost:8000 > /dev/null 2>&1 &

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║  ✅ Analizavet V2 corriendo en http://localhost:8000   ║"
echo "║                                                         ║"
echo "║  Para detener:                                         ║"
echo "║    - Presiona Ctrl+C para detener todo                  ║"
echo "║    - O ejecuta: kill $SERVER_PID $DRAMATIQ_PID          ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Mantener script vivo
trap "echo ''; echo '🛑 Deteniendo servicios...'; kill $SERVER_PID $DRAMATIQ_PID 2>/dev/null || true; exit 0" SIGINT SIGTERM
wait $SERVER_PID
