# Dockerfile pour Alimante
# Basé sur Python 3.11 slim pour optimiser la taille

FROM python:3.11-slim

# Métadonnées
LABEL description="Système de gestion automatisée des mantes avec Raspberry Pi"
LABEL version="1.0.0"

# Variables d'environnement
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Installation des dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    libjpeg-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libopenjp2-7-dev \
    libtiff5-dev \
    zlib1g-dev \
    libharfbuzz0b \
    libwebp-dev \
    libxcb1-dev \
    libxrandr-dev \
    libxss-dev \
    libasound2-dev \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    libcairo2-dev \
    pkg-config \
    git \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Création de l'utilisateur non-root
RUN groupadd -r alimante && useradd -r -g alimante alimante

# Création des répertoires de travail
WORKDIR /app

# Copie des fichiers de dépendances
COPY requirements.txt pyproject.toml setup.py ./

# Installation des dépendances Python
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code source
COPY . .

# Installation du package en mode développement
RUN pip install -e .

# Création des répertoires nécessaires
RUN mkdir -p logs data config/backups

# Changement des permissions
RUN chown -R alimante:alimante /app
RUN chmod +x start_api.py

# Passage à l'utilisateur non-root
USER alimante

# Exposition du port
EXPOSE 8000

# Point d'entrée par défaut
CMD ["python", "start_api.py"]

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1
