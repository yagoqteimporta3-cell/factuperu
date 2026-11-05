# Guía para subir Sefactel a un servidor (producción)

Esta guía explica cómo dejar la app corriendo en un servidor real (Linux) para que
tus clientes la usen por internet.

## Lo que necesitas saber de tu servidor
- Sistema operativo: idealmente **Linux** (Ubuntu/Debian). Windows Server también
  funciona pero es más trabajo.
- Acceso por **SSH** (terminal) con permisos para instalar programas (root/sudo).
- Opcional pero recomendado: **Docker** instalado (facilita todo).
- Un **dominio** apuntando a la IP del servidor (DNS) si quieres que se acceda
  por `tudominio.com` en vez de la IP.

---

## Opción A — Con Docker (la más fácil)

1. Instala Docker y Docker Compose en el servidor.
2. Sube el proyecto al servidor (por Git, SFTP o copiando la carpeta).
3. Edita `docker-compose.yml` y cambia:
   - `POSTGRES_PASSWORD` (clave de la base de datos)
   - `SECRET_KEY` (clave larga y aleatoria)
   - `ALLOWED_HOSTS` (tu dominio)
   - `DATABASE_URL` (que coincida con la clave de Postgres)
4. Ejecuta:
   ```bash
   docker compose up -d --build
   ```
5. La app queda en `http://IP-del-servidor:8000`. Crea el primer usuario entrando
   a `/register/`.

Para acceso por puerto 80 (sin ":8000"), pon un proxy delante (nginx/Caddy) o
cambia el puerto del contenedor a `80:8000`.

---

## Opción B — Sin Docker (manual, Ubuntu/Debian)

```bash
# 1. Instalar paquetes
sudo apt update
sudo apt install -y python3 python3-venv python3-pip postgresql nginx

# 2. Crear base de datos y usuario
sudo -u postgres psql -c "CREATE USER factuperu WITH PASSWORD 'clave';"
sudo -u postgres psql -c "CREATE DATABASE factuperu OWNER factuperu;"

# 3. Clonar/subir el proyecto y crear el entorno
cd /ruta/al/proyecto
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Configurar variables (.env)
cp .env.example .env
nano .env   # pon SECRET_KEY, DEBUG=False, ALLOWED_HOSTS, DATABASE_URL

# 5. Migrar y recolectar estáticos
python manage.py migrate --noinput
python manage.py collectstatic --noinput

# 6. Servir con gunicorn (prueba rápida)
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

Para dejarlo permanente (systemd), crea `/etc/systemd/system/factuperu.service`:
```ini
[Unit]
Description=FactuPeru
After=network.target

[Service]
User=tu-usuario
WorkingDirectory=/ruta/al/proyecto
EnvironmentFile=/ruta/al/proyecto/.env
ExecStart=/ruta/al/proyecto/venv/bin/gunicorn config.wsgi:application --bind 127.0.0.1:8000 --workers 3
Restart=always

[Install]
WantedBy=multi-user.target
```
```bash
sudo systemctl enable --now factuperu
```

### nginx (para servir por el dominio + HTTPS)
Crea `/etc/nginx/sites-available/factuperu`:
```nginx
server {
    listen 80;
    server_name tu-dominio.com;

    location /static/ {
        alias /ruta/al/proyecto/staticfiles/;
    }
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```
```bash
sudo ln -s /etc/nginx/sites-available/factuperu /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
# HTTPS gratis con Let's Encrypt:
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d tu-dominio.com
```

---

## Checklist final
- [ ] `SECRET_KEY` cambiada (no usar la de ejemplo)
- [ ] `DEBUG=False`
- [ ] `ALLOWED_HOSTS` con el dominio real
- [ ] Base de datos PostgreSQL configurada
- [ ] Respaldos automáticos de la base de datos
- [ ] Valores legales (RMV, UIT) actualizados en `core/planilla.py`
