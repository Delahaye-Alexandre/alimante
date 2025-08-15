#!/usr/bin/env python3
"""
Script de démarrage de l'API Alimante
Configure et lance l'API FastAPI avec uvicorn
"""

import os
import sys
import uvicorn
from pathlib import Path

# Ajouter le répertoire racine au PYTHONPATH
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """Point d'entrée principal"""
    
    # Configuration par défaut
    config = {
        "host": os.getenv("API_HOST", "0.0.0.0"),
        "port": int(os.getenv("API_PORT", "8000")),
        "reload": os.getenv("API_DEBUG", "false").lower() == "true",
        "log_level": os.getenv("LOG_LEVEL", "info").lower(),
        "access_log": True,
        "workers": 1
    }
    
    print(f"🚀 Démarrage de l'API Alimante...")
    print(f"📍 Host: {config['host']}")
    print(f"🔌 Port: {config['port']}")
    print(f"🔄 Reload: {config['reload']}")
    print(f"📝 Log Level: {config['log_level']}")
    print(f"🌐 Documentation: http://{config['host']}:{config['port']}/docs")
    print("")
    
    try:
        # Démarrer l'API
        uvicorn.run(
            "src.api.app:app",
            **config
        )
    except KeyboardInterrupt:
        print("\n🛑 Arrêt de l'API...")
    except Exception as e:
        print(f"❌ Erreur lors du démarrage de l'API: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
