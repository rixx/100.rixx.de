# Deployment docs

Create a user `hundo` (`useradd hundo -m`), clone this repository, `pip install --user -r src/requirements.txt`.

Create a systemd service to run gunicorn at a port of your choice, at `/etc/systemd/system/hundo.service`:

```
[Unit]
Description=hundo web service
After=network.target

[Service]
User=hundo
Group=hundo
WorkingDirectory=/home/hundo/100.rixx.de/src
ExecStart=/home/hundo/.local/bin/gunicorn server:web_app --bind localhost:8091 --worker-class aiohttp.GunicornWebWorker
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

And nginx:

```
server {
    listen 443 default_server;
    listen [::]:443 ipv6only=on default_server;
    server_name 100.rixx.de;

    ssl on;
    ssl_certificate /etc/ssl/letsencrypt/certs/100.rixx.de/fullchain.pem;
    ssl_certificate_key /etc/ssl/letsencrypt/certs/100.rixx.de/privkey.pem;

    add_header Referrer-Policy same-origin;
    add_header X-Content-Type-Options nosniff;

    location / {
        proxy_pass http://localhost:8091/;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header Host $http_host;
    }
}
```
