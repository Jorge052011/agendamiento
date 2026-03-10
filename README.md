# RepartoTrack — Django

## Setup en GitHub Codespaces

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Crear archivo .env
cp .env.example .env
# Editar .env y poner tu GOOGLE_MAPS_API_KEY

# 3. Correr el servidor
python manage.py runserver 0.0.0.0:8000
```

## Estructura
```
repartotrack_django/
├── manage.py
├── requirements.txt
├── .env.example
├── repartotrack/        ← configuración Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── entregas/            ← app principal
│   ├── views.py         ← todos los endpoints API
│   ├── urls.py
│   └── utils.py         ← helpers (json, geo, teléfono)
├── templates/
│   └── index.html       ← frontend completo
├── deliveries.json      ← datos (se crea automáticamente)
├── clients.json
└── config.json
```

## API Endpoints
| Método | URL | Descripción |
|--------|-----|-------------|
| GET | `/` | Frontend |
| GET/POST | `/api/clients` | Listar / crear clientes |
| PATCH/DELETE | `/api/clients/<phone>` | Actualizar / eliminar cliente |
| GET/POST | `/api/deliveries` | Listar / crear entregas |
| PATCH/DELETE | `/api/deliveries/<id>` | Actualizar / eliminar entrega |
| GET | `/api/calendar` | Resumen por día |
| POST | `/api/optimize` | Calcular ruta óptima TSP |
| GET/POST | `/api/config` | Configuración (API Key, puntos de partida) |

## Diferencias con Flask
- Mismo frontend (`index.html`) sin cambios
- Mismos archivos de datos JSON (`deliveries.json`, `clients.json`, `config.json`)
- Puerto por defecto: **8000** (en vez de 5000)
- No necesita `host="0.0.0.0"` explícito — ya va en el comando `runserver`
