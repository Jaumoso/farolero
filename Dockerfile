FROM python:3.10-slim
WORKDIR /app

# Copiar requirements.txt e instalar dependencias primero (mejor caché)
RUN apt-get update \
	&& apt-get install -y ca-certificates curl gnupg lsb-release \
	&& mkdir -p /etc/apt/keyrings \
	&& curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg \
	&& echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list \
	&& apt-get update \
	&& apt-get install -y docker-ce-cli \
	&& mkdir -p /usr/local/lib/docker/cli-plugins \
	&& curl -SL https://github.com/docker/compose/releases/download/v2.27.1/docker-compose-linux-x86_64 -o /usr/local/lib/docker/cli-plugins/docker-compose \
	&& chmod +x /usr/local/lib/docker/cli-plugins/docker-compose \
	&& apt-get purge -y curl gnupg lsb-release \
	&& rm -rf /var/lib/apt/lists/*
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la app
COPY app/ /app/

EXPOSE 8080
ENV PYTHONPATH=/
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]