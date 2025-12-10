# Checklist de Verificación - Docker, Alembic & Poetry

Usa este checklist para verificar que todo está configurado correctamente.

---

## ANTES DE COMMITEAR

- [ ] `pyproject.toml` tiene sección `[tool.alembic]` completa
- [ ] `alembic.ini` solo contiene config de runtime (DB URL + logging)
- [ ] `.dockerignore` existe y tiene patrones correctos
- [ ] `Dockerfile` usa multi-stage build
- [ ] `scripts/migrate_gcp.py` existe y tiene permisos de ejecución
- [ ] `DEPLOYMENT.md` creado con instrucciones completas
- [ ] `.env.gcp.template` creado
- [ ] `README.md` actualizado con sección de Docker

---

## 🐳 VERIFICACIÓN LOCAL (DOCKER)

### 1. Build de Imagen

```bash
cd backend
docker build -t restomap-test -f Dockerfile .
```

**Esperado:**

- Build exitoso sin errores
- Tamaño de imagen ~400-500 MB (verificar con `docker images`)

### 2. Variables de Entorno

```bash
cp .env.example .env
# Editar .env con valores locales
cat .env
```

**Verificar que existen:**

- [ ] `DB_USER`
- [ ] `DB_PASSWORD`
- [ ] `DB_HOST=db`
- [ ] `DB_NAME`
- [ ] `JWT_SECRET_KEY`

### 3. Docker Compose

```bash
# Iniciar solo base de datos
docker-compose up -d db

# Verificar que está healthy
docker-compose ps
```

**Esperado:**

- PostgreSQL corriendo
- Estado: `healthy` (después de ~5 segundos)

### 4. Inicialización de Base de Datos

```bash
docker-compose --profile init up init-db
```

**Esperado:**

- Migraciones aplicadas exitosamente
- Seeds ejecutados sin errores
- Mensaje: "Base de datos inicializada correctamente!"

### 5. Backend

```bash
docker-compose up -d backend

# Ver logs
docker-compose logs -f backend
```

**Esperado:**

- Backend inicia sin errores
- Logs muestran: "Running on http://0.0.0.0:5000"
- Health check pasa (después de 40s)

### 6. Pruebas de Endpoints

```bash
# Health check
curl http://localhost:5000/health

# Endpoint principal (esperado: info del proyecto)
curl http://localhost:5000/
```

**Esperado:**

- Respuesta 200 OK
- JSON válido

---

## VERIFICACIÓN DE ALEMBIC

### 1. Configuración en pyproject.toml

```bash
cat pyproject.toml | grep -A 10 "\[tool.alembic\]"
```

**Verificar que existe:**

- [ ] `script_location = "alembic"`
- [ ] `prepend_sys_path = [".", "src"]`
- [ ] `file_template` con formato de fecha
- [ ] `timezone = "America/Santiago"`

### 2. Estado de Migraciones

```bash
docker-compose --profile tools run app alembic current
```

**Esperado:**

- Muestra revisión actual
- Marca como `(head)` si está actualizado

### 3. Historial

```bash
docker-compose --profile tools run app alembic history
```

**Esperado:**

- Lista todas las migraciones
- Nombres de archivo con formato: `YYYY_MM_DD_HHMM-{rev}_{slug}.py`

### 4. Crear Nueva Migración (Prueba)

```bash
docker-compose --profile tools run app alembic revision -m "test"
```

**Verificar:**

- [ ] Archivo creado en `alembic/versions/`
- [ ] Nombre incluye fecha/hora
- [ ] Archivo formateado con ruff (sin errores de lint)

**ELIMINAR** el archivo de prueba después:

```bash
rm alembic/versions/YYYY_MM_DD_*.py
```

---

## VERIFICACIÓN DE DOCKERFILE

### 1. Multi-Stage Build

```bash
docker history restomap-test | head -20
```

**Verificar:**

- [ ] Aparecen dos stages: builder y runtime
- [ ] Runtime no incluye gcc ni build tools

### 2. Usuario No-Root

```bash
docker run --rm restomap-test whoami
```

**Esperado:**

- Output: `appuser` (NO `root`)

### 3. Health Check

```bash
docker inspect restomap-test | grep -A 10 Healthcheck
```

**Verificar:**

- [ ] Intervalo: 30s
- [ ] Timeout: 3s
- [ ] Start period: 40s

### 4. Variables de Entorno

```bash
docker run --rm restomap-test env | grep -E "PYTHON|PORT|ENV"
```

**Esperado:**

- `PYTHONPATH=/app/src`
- `PYTHONUNBUFFERED=1`
- `PORT=5000`

---

## ☁PREPARACIÓN PARA GCP

### 1. Variables GCP Template

```bash
cat .env.gcp.template
```

**Verificar que tiene:**

- [ ] `DB_HOST=/cloudsql/...` (formato Unix socket)
- [ ] Instrucciones de Secret Manager
- [ ] Comandos gcloud completos

### 2. Script de Migración

```bash
python scripts/migrate_gcp.py --help 2>&1 || echo "OK - script existe"
```

**Verificar:**

- [ ] Archivo existe
- [ ] Es ejecutable (`chmod +x` en Linux/Mac)
- [ ] Importa correctamente (no errors de sintaxis)

### 3. Documentación

```bash
ls -la | grep -E "DEPLOYMENT|CONFIGURACION"
```

**Verificar que existen:**

- [ ] `DEPLOYMENT.md`
- [ ] `CONFIGURACION.md`

---

## TESTS DE INTEGRACIÓN

### 1. Flujo Completo Local

```bash
# Limpiar todo
docker-compose down -v

# Flujo completo desde cero
docker-compose up -d db && \
  sleep 5 && \
  docker-compose --profile init up init-db && \
  docker-compose up -d backend && \
  sleep 10 && \
  curl http://localhost:5000/health
```

**Esperado:**

- Todo ejecuta sin errores
- Health check retorna 200

### 2. Persistencia de Datos

```bash
# Reiniciar backend (NO db)
docker-compose restart backend

# Verificar que datos persisten
curl http://localhost:5000/api/locales
```

**Esperado:**

- Backend reinicia correctamente
- Datos siguen disponibles

### 3. Logs Sin Errores

```bash
docker-compose logs backend | grep -i error
```

**Esperado:**

- Sin errores críticos
- Solo warnings esperados (si los hay)

---

## MÉTRICAS DE ÉXITO

### Tamaño de Imagen

```bash
docker images restomap-test --format "{{.Size}}"
```

**Target:** < 500 MB

### Tiempo de Build

```bash
time docker build -t restomap-test .
```

**Target:** < 5 minutos (con cache)

### Tiempo de Inicio

```bash
docker-compose up -d backend && \
  time docker-compose logs -f backend | grep -m 1 "Running on"
```

**Target:** < 10 segundos

---

## 🚨 TROUBLESHOOTING

### Problema: Build falla

```bash
# Build sin cache
docker build --no-cache -t restomap-test .

# Ver logs detallados
docker build --progress=plain -t restomap-test .
```

### Problema: Migraciones fallan

```bash
# Entrar al contenedor
docker-compose exec backend bash

# Verificar Alembic
alembic current
alembic history

# Verificar conexión DB
python -c "from database import engine; print(engine.url)"
```

### Problema: Backend no inicia

```bash
# Logs completos
docker-compose logs backend

# Verificar variables
docker-compose exec backend env | grep DB_

# Probar Python
docker-compose exec backend python --version
```

---

## CHECKLIST FINAL PRE-DEPLOY

Antes de hacer deploy a GCP:

- [ ] Todos los tests locales pasan
- [ ] Build de Docker exitoso
- [ ] Migraciones funcionan
- [ ] Health check responde
- [ ] `.env.gcp.template` revisado
- [ ] Secrets de GCP configurados
- [ ] Cloud SQL instance creada
- [ ] Permisos IAM configurados
- [ ] Documentación actualizada
- [ ] README actualizado
- [ ] Commits pusheados a repo

---

## 🎉 TODO LISTO

Si todos los checks están , estás listo para:

1. Commitear cambios
2. Deploy a GCP Cloud Run
3. Profit!

---

**Última actualización:** Diciembre 2024  
**Versión:** 1.0
