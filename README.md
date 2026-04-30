# Analizavet V2

Sistema veterinario de análisis de laboratorio - Versión 2.0

## Estado Actual (2026-04-30)

### ✅ Funcional
- Upload de archivos HL7 .txt - batch splitting funciona
- Filtrado de heartbeats ZHB
- Extracción de pacientes (PID), valores de laboratorio (OBX), imágenes (Base64)
- Base de datos limpia (analizavet.db eliminada para pruebas)
- Dramatiq worker con manejo automático de conflictos de puerto Prometheus

### 🔧 En Desarrollo (Pendiente)
- Dashboard avanzado de gestión de pacientes
- Exportación masiva de PDFs
- Integración con dispositivos Fujifilm (emulación)

### 🛠️ Solución de Problemas

#### Issue: "Worker no arranca / Error puerto 9191 o 9200"
**Causa**: El proceso anterior de Dramatiq no se cerró correctamente, dejando los puertos Prometheus (9191/9200) ocupados.
Dramatiq 1.15.0 incluye el middleware Prometheus por defecto que requiere estos puertos.
**Solución**: Ejecutar `./iniciar.sh` nuevamente. El script limpiará automáticamente cualquier proceso usando puertos 9191/9200 antes de iniciar el worker.

#### Issue: "Redis no responde"
**Causa**: El servicio Redis no está corriendo.
**Solución**: `./iniciar.sh` inicia Redis automáticamente. Verificar con `redis-cli ping`.

#### Issue: "Mensajes en cola pero no se procesan"
**Causa**: El worker de Dramatiq está caído.
**Solución**: Reiniciar con `./iniciar.sh` o verificar logs del worker.

#### Comandos útiles para diagnóstico:
```bash
# Ver procesos dramatiq activos
ps aux | grep dramatiq

# Matar procesos colgados
pkill -f dramatiq

# Ver puertos en uso
lsof -ti:9191,9200

# Ver colas Redis
redis-cli LLEN dramatiq:default
redis-cli LRANGE dramatiq:default.DLQ 0 -1  # Mensajes fallidos
```

### Archivos de Prueba
- `log_prueba.txt` - 1 paciente (ichiro, canino, 5 años)
- `log_laboratorio_17 de abril.txt` - 12 pacientes

## Inicio Rápido

```bash
# Limpiar procesos anteriores si hay conflictos de puerto
pkill -f dramatiq

# Iniciar todo
./iniciar.sh
```

## Stack Tecnológico

- **Python 3.11** + **uv** (gestor de dependencias)
- **FastAPI** + **HTMX** (server-side rendering)
- **SQLModel** + **SQLite** (desarrollo) / PostgreSQL (producción)
- **Dramatiq** + **Redis** (tareas en background)
- **WeasyPrint** (generación de PDFs)
- **CSS Grid Areas** (layout flexible y desacoplado)

## Comandos Útiles

```bash
# Ver procesos dramatiq activos
ps aux | grep dramatiq

# Matar procesos colgados
pkill -f dramatiq

# Ver colas Redis
redis-cli LLEN dramatiq:default

# Ver mensajes en cola (dead letter si fallaron)
redis-cli LRANGE dramatiq:default.DLQ 0 -1

# Iniciar solo servidor (sin dramatiq)
uv run uvicorn app.main:app --reload

# Iniciar solo workers dramatiq (para debugging)
uv run dramatiq app.tasks:broker --threads 2
```

## Estructura del Proyecto

```
Analizavet-v2/
├── app/
│   ├── core/           # Lógica de negocio (el "cerebro")
│   │   ├── reception/  # Normalización de pacientes
│   │   └── taller/    # Engine, flagging, imágenes
│   ├── satellites/    # Adaptadores (los "sentidos")
│   │   ├── ozelle/    # Parser HL7, MLLP server
│   │   └── fujifilm/  # Stub para Fujifilm
│   ├── routers/       # Endpoints HTTP
│   ├── tasks/         # Tareas Dramatiq (broker.py, hl7_processor.py)
│   ├── templates/      # Jinja2 templates
│   └── static/         # CSS, JS
├── tests/
├── iniciar.sh          # Script de inicio (corregido 2026-04-30)
└── log_prueba.txt      # Archivo de prueba (1 paciente)
```

## Formato HL7 de Ozelle

```
MSH|^~\&|HEARTBEAT|...|ZHB^H00|...  ← IGNORAR (heartbeat)
MSH|^~\&|EHVT-50|...|ORU^R01|...     ← PACIENTE (inicio)
PID|...|nombre especie edad dueño|   ← Datos paciente
OBR|...|CBC^Complete Blood Count|    ← Tipo análisis
OBX|1|ST|WBC^||14.26|...             ← Parámetros
OBX|43|ED|RBC_Histo||Base64^/9j/...  ← Imágenes (hasta = antes de |||||F)
```

## Licencia

MIT - Huellas Lab

