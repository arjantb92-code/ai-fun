# Better WBW - Database Connection Info

To connect via DBeaver or any other SQL client:

- **Host**: localhost
- **Port**: 5432
- **Database**: better_wbw
- **Username**: wbw_admin
- **Password**: secure_wbw_password_2026

## Running the Database
The database runs in a Docker container.

Start:
```bash
docker compose up -d
```

Stop:
```bash
docker compose down
```

Data is persisted in the `./postgres-data` directory.

## SSL / PEM Certificates
If you need to enable SSL or use `.pem` certificates for the database:

### 1. Server-side (Local Docker)
To make the local Postgres container use SSL, you need a certificate (`server.crt`) and a private key (`server.key`).

1. Place your certificates in a folder, e.g., `./certs/`.
2. Update `docker-compose.yml` to mount them:
   ```yaml
   services:
     db:
       ...
       volumes:
         - ./postgres-data:/var/lib/postgresql/data
         - ./certs/server.crt:/var/lib/postgresql/server.crt:ro
         - ./certs/server.key:/var/lib/postgresql/server.key:ro
       command: -c ssl=on -c ssl_cert_file=/var/lib/postgresql/server.crt -c ssl_key_file=/var/lib/postgresql/server.key
   ```
3. **Note on Permissions**: Postgres requires the key file to have strict permissions (`chmod 0600`). On macOS/Docker Desktop, this can be tricky. You might need to adjust the owner inside the container via a custom Dockerfile or entrypoint script.

### 2. Client-side (DBeaver)
If the database *already* requires SSL (e.g., a remote server):
1. Open **Connection Settings** in DBeaver.
2. Go to the **SSL** tab.
3. Check **Use SSL**.
4. Provide the paths to your:
   - **Root certificate** (CA)
   - **SSL Certificate**
   - **SSL Certificate Key**
5. Change **SSL Mode** to `verify-ca` or `verify-full` depending on your requirements.
