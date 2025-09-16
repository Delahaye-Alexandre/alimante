/**
 * Alimante - Application JavaScript
 * Gère l'interface utilisateur et la communication avec l'API
 */

class AlimanteApp {
  constructor() {
    this.apiBase = "";
    this.updateInterval = 2000; // 2 secondes
    this.isConnected = false;
    this.currentTab = "dashboard";
    this.data = {
      sensors: {},
      controls: {},
      alerts: [],
      system_status: "initializing",
    };

    this.init();
  }

  init() {
    console.log("Initialisation de l'application Alimante...");

    // Initialiser les événements
    this.setupEventListeners();

    // Démarrer la mise à jour des données
    this.startDataUpdates();

    // Charger les données initiales
    this.loadInitialData();

    console.log("Application Alimante initialisée");
  }

  setupEventListeners() {
    // Navigation
    document.querySelectorAll(".nav-item").forEach((item) => {
      item.addEventListener("click", (e) => {
        const tab = e.currentTarget.dataset.tab;
        this.switchTab(tab);
      });
    });

    // Contrôles
    document
      .getElementById("heatingToggle")
      ?.addEventListener("change", (e) => {
        this.toggleControl("heating", e.target.checked);
      });

    document
      .getElementById("lightingToggle")
      ?.addEventListener("change", (e) => {
        this.toggleControl("lighting", e.target.checked);
      });

    document
      .getElementById("humidificationToggle")
      ?.addEventListener("change", (e) => {
        this.toggleControl("humidification", e.target.checked);
      });

    document
      .getElementById("ventilationToggle")
      ?.addEventListener("change", (e) => {
        this.toggleControl("ventilation", e.target.checked);
      });

    document
      .getElementById("feedingToggle")
      ?.addEventListener("change", (e) => {
        this.toggleControl("feeding", e.target.checked);
      });

    // Configuration
    document.getElementById("saveConfigBtn")?.addEventListener("click", () => {
      this.saveConfiguration();
    });

    document.getElementById("resetConfigBtn")?.addEventListener("click", () => {
      this.resetConfiguration();
    });

    // Alertes
    document.getElementById("clearAlertsBtn")?.addEventListener("click", () => {
      this.clearAlerts();
    });
  }

  async loadInitialData() {
    try {
      await this.updateStatus();
      await this.updateSensors();
      await this.updateControls();
      await this.updateAlerts();
    } catch (error) {
      console.error("Erreur chargement données initiales:", error);
    }
  }

  startDataUpdates() {
    setInterval(() => {
      this.updateAllData();
    }, this.updateInterval);
  }

  async updateAllData() {
    try {
      await Promise.all([
        this.updateStatus(),
        this.updateSensors(),
        this.updateControls(),
        this.updateAlerts(),
      ]);
    } catch (error) {
      console.error("Erreur mise à jour données:", error);
      this.setConnectionStatus(false);
    }
  }

  async updateStatus() {
    try {
      const response = await fetch(`${this.apiBase}/api/status`);
      if (!response.ok) throw new Error("Erreur API status");

      const data = await response.json();
      this.data = { ...this.data, ...data.data };
      this.setConnectionStatus(true);
      this.updateStatusDisplay();
    } catch (error) {
      console.error("Erreur mise à jour statut:", error);
      this.setConnectionStatus(false);
    }
  }

  async updateSensors() {
    try {
      const response = await fetch(`${this.apiBase}/api/sensors`);
      if (!response.ok) throw new Error("Erreur API sensors");

      const data = await response.json();
      this.data.sensors = data.sensors;
      this.updateSensorsDisplay();
    } catch (error) {
      console.error("Erreur mise à jour capteurs:", error);
    }
  }

  async updateControls() {
    try {
      const response = await fetch(`${this.apiBase}/api/controls`);
      if (!response.ok) throw new Error("Erreur API controls");

      const data = await response.json();
      this.data.controls = data.controls;
      this.updateControlsDisplay();
    } catch (error) {
      console.error("Erreur mise à jour contrôles:", error);
    }
  }

  async updateAlerts() {
    try {
      const response = await fetch(`${this.apiBase}/api/alerts`);
      if (!response.ok) throw new Error("Erreur API alerts");

      const data = await response.json();
      this.data.alerts = data.alerts;
      this.updateAlertsDisplay();
    } catch (error) {
      console.error("Erreur mise à jour alertes:", error);
    }
  }

  setConnectionStatus(connected) {
    this.isConnected = connected;
    const statusDot = document.getElementById("statusDot");
    const statusText = document.getElementById("statusText");

    if (connected) {
      statusDot.className = "status-dot connected";
      statusText.textContent = "Connecté";
    } else {
      statusDot.className = "status-dot error";
      statusText.textContent = "Déconnecté";
    }
  }

  updateStatusDisplay() {
    // Statut système
    const systemStatus = document.getElementById("systemStatus");
    if (systemStatus) {
      systemStatus.textContent = this.data.system_status || "Inconnu";
    }

    // Uptime
    const systemUptime = document.getElementById("systemUptime");
    if (systemUptime && this.data.stats) {
      const uptime = this.data.stats.uptime || 0;
      systemUptime.textContent = this.formatUptime(uptime);
    }

    // Dernière mise à jour
    const lastUpdate = document.getElementById("lastUpdate");
    if (lastUpdate) {
      lastUpdate.textContent = new Date().toLocaleTimeString();
    }
  }

  updateSensorsDisplay() {
    const sensors = this.data.sensors || {};

    // DHT22
    const dht22 = sensors.dht22 || {};
    const temperature = dht22.temperature;
    const humidity = dht22.humidity;

    // Température
    const tempValue = document.getElementById("temperatureValue");
    const tempStatus = document.getElementById("temperatureStatus");
    const dht22Temp = document.getElementById("dht22Temp");

    if (temperature !== undefined) {
      if (tempValue) tempValue.textContent = temperature.toFixed(1);
      if (dht22Temp) dht22Temp.textContent = `${temperature.toFixed(1)} °C`;
      if (tempStatus) {
        tempStatus.className = "sensor-status available";
        tempStatus.innerHTML =
          '<i class="fas fa-circle"></i><span>Capteur disponible</span>';
      }
    } else {
      if (tempValue) tempValue.textContent = "--";
      if (dht22Temp) dht22Temp.textContent = "-- °C";
      if (tempStatus) {
        tempStatus.className = "sensor-status unavailable";
        tempStatus.innerHTML =
          '<i class="fas fa-circle"></i><span>Capteur non disponible</span>';
      }
    }

    // Humidité
    const humValue = document.getElementById("humidityValue");
    const humStatus = document.getElementById("humidityStatus");
    const dht22Hum = document.getElementById("dht22Hum");

    if (humidity !== undefined) {
      if (humValue) humValue.textContent = humidity.toFixed(1);
      if (dht22Hum) dht22Hum.textContent = `${humidity.toFixed(1)} %`;
      if (humStatus) {
        humStatus.className = "sensor-status available";
        humStatus.innerHTML =
          '<i class="fas fa-circle"></i><span>Capteur disponible</span>';
      }
    } else {
      if (humValue) humValue.textContent = "--";
      if (dht22Hum) dht22Hum.textContent = "-- %";
      if (humStatus) {
        humStatus.className = "sensor-status unavailable";
        humStatus.innerHTML =
          '<i class="fas fa-circle"></i><span>Capteur non disponible</span>';
      }
    }

    // Qualité de l'air
    const airQuality = sensors.air_quality || {};
    const aqi = airQuality.aqi;

    const airValue = document.getElementById("airQualityValue");
    const airStatus = document.getElementById("airQualityStatus");
    const airDetail = document.getElementById("airQualityDetail");
    const airDetailStatus = document.getElementById("airQualityDetailStatus");

    if (aqi !== undefined) {
      if (airValue) airValue.textContent = aqi;
      if (airDetail) airDetail.textContent = aqi;
      if (airStatus) {
        airStatus.className = "sensor-status available";
        airStatus.innerHTML =
          '<i class="fas fa-circle"></i><span>Capteur disponible</span>';
      }
      if (airDetailStatus) {
        airDetailStatus.textContent = "Disponible";
      }
    } else {
      if (airValue) airValue.textContent = "--";
      if (airDetail) airDetail.textContent = "--";
      if (airStatus) {
        airStatus.className = "sensor-status unavailable";
        airStatus.innerHTML =
          '<i class="fas fa-circle"></i><span>Capteur non disponible</span>';
      }
      if (airDetailStatus) {
        airDetailStatus.textContent = "Non disponible";
      }
    }

    // Niveau d'eau
    const waterLevel = sensors.water_level || {};
    const level = waterLevel.level;

    const waterValue = document.getElementById("waterLevel");
    const waterStatus = document.getElementById("waterLevelStatus");

    if (level !== undefined) {
      if (waterValue) waterValue.textContent = `${level} %`;
      if (waterStatus) {
        waterStatus.textContent = "Disponible";
      }
    } else {
      if (waterValue) waterValue.textContent = "-- %";
      if (waterStatus) {
        waterStatus.textContent = "Non disponible";
      }
    }
  }

  updateControlsDisplay() {
    const controls = this.data.controls || {};

    // Mettre à jour les statuts des contrôles
    this.updateControlStatus("heating", controls.heating);
    this.updateControlStatus("lighting", controls.lighting);
    this.updateControlStatus("humidification", controls.humidification);
    this.updateControlStatus("ventilation", controls.ventilation);
    this.updateControlStatus("feeding", controls.feeding);

    // Mettre à jour les toggles
    this.updateControlToggle("heatingToggle", controls.heating);
    this.updateControlToggle("lightingToggle", controls.lighting);
    this.updateControlToggle("humidificationToggle", controls.humidification);
    this.updateControlToggle("ventilationToggle", controls.ventilation);
    this.updateControlToggle("feedingToggle", controls.feeding);
  }

  updateControlStatus(controlName, isActive) {
    const statusElement = document.getElementById(`${controlName}Status`);
    if (statusElement) {
      const icon = statusElement.querySelector("i");
      const text = statusElement.querySelector("span");

      if (isActive) {
        statusElement.className = "control-status active";
        if (text) text.textContent = "Actif";
      } else {
        statusElement.className = "control-status inactive";
        if (text) text.textContent = "Arrêté";
      }
    }
  }

  updateControlToggle(toggleId, isActive) {
    const toggle = document.getElementById(toggleId);
    if (toggle) {
      toggle.checked = isActive || false;
    }
  }

  updateAlertsDisplay() {
    const alertsList = document.getElementById("alertsList");
    if (!alertsList) return;

    const alerts = this.data.alerts || [];

    if (alerts.length === 0) {
      alertsList.innerHTML = `
                <div class="alert-item info">
                    <i class="fas fa-info-circle"></i>
                    <span>Aucune alerte active</span>
                    <span class="alert-time">--</span>
                </div>
            `;
      return;
    }

    alertsList.innerHTML = alerts
      .map((alert) => {
        const time = new Date(alert.timestamp * 1000).toLocaleTimeString();
        const level = alert.level || "info";
        const message = alert.message || "Alerte inconnue";

        return `
                <div class="alert-item ${level}">
                    <i class="fas fa-${this.getAlertIcon(level)}"></i>
                    <span>${message}</span>
                    <span class="alert-time">${time}</span>
                </div>
            `;
      })
      .join("");
  }

  getAlertIcon(level) {
    const icons = {
      error: "exclamation-circle",
      warning: "exclamation-triangle",
      success: "check-circle",
      info: "info-circle",
    };
    return icons[level] || "info-circle";
  }

  switchTab(tabName) {
    // Mettre à jour la navigation
    document.querySelectorAll(".nav-item").forEach((item) => {
      item.classList.remove("active");
    });
    document.querySelector(`[data-tab="${tabName}"]`).classList.add("active");

    // Mettre à jour le contenu
    document.querySelectorAll(".tab-content").forEach((content) => {
      content.classList.remove("active");
    });
    document.getElementById(tabName).classList.add("active");

    this.currentTab = tabName;
  }

  async toggleControl(controlName, enabled) {
    try {
      const response = await fetch(`${this.apiBase}/api/control`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          action: controlName,
          value: enabled,
        }),
      });

      if (!response.ok) throw new Error("Erreur contrôle");

      const result = await response.json();
      if (result.success) {
        console.log(
          `Contrôle ${controlName} ${enabled ? "activé" : "désactivé"}`
        );
      } else {
        console.error("Erreur contrôle:", result.error);
        // Remettre le toggle dans l'état précédent
        const toggle = document.getElementById(`${controlName}Toggle`);
        if (toggle) toggle.checked = !enabled;
      }
    } catch (error) {
      console.error(`Erreur contrôle ${controlName}:`, error);
      // Remettre le toggle dans l'état précédent
      const toggle = document.getElementById(`${controlName}Toggle`);
      if (toggle) toggle.checked = !enabled;
    }
  }

  async clearAlerts() {
    try {
      // Émettre un événement pour effacer les alertes
      this.data.alerts = [];
      this.updateAlertsDisplay();
      console.log("Alertes effacées");
    } catch (error) {
      console.error("Erreur effacement alertes:", error);
    }
  }

  async saveConfiguration() {
    try {
      const config = {
        terrarium_name: document.getElementById("terrariumName")?.value,
        species: document.getElementById("speciesSelect")?.value,
        sensor_interval: parseInt(
          document.getElementById("sensorInterval")?.value
        ),
        auto_mode: document.getElementById("autoModeToggle")?.checked,
      };

      const response = await fetch(`${this.apiBase}/api/config`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(config),
      });

      if (!response.ok) throw new Error("Erreur sauvegarde");

      const result = await response.json();
      if (result.success) {
        console.log("Configuration sauvegardée");
        this.showNotification(
          "Configuration sauvegardée avec succès",
          "success"
        );
      } else {
        console.error("Erreur sauvegarde:", result.error);
        this.showNotification("Erreur lors de la sauvegarde", "error");
      }
    } catch (error) {
      console.error("Erreur sauvegarde configuration:", error);
      this.showNotification("Erreur lors de la sauvegarde", "error");
    }
  }

  resetConfiguration() {
    // Remettre les valeurs par défaut
    document.getElementById("terrariumName").value = "Terrarium Principal";
    document.getElementById("speciesSelect").value = "mantis_religiosa";
    document.getElementById("sensorInterval").value = "5";
    document.getElementById("autoModeToggle").checked = true;

    console.log("Configuration réinitialisée");
    this.showNotification("Configuration réinitialisée", "info");
  }

  showNotification(message, type = "info") {
    // Créer une notification temporaire
    const notification = document.createElement("div");
    notification.className = `notification ${type}`;
    notification.textContent = message;
    notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 1rem 1.5rem;
            background-color: ${this.getNotificationColor(type)};
            color: white;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            z-index: 1000;
            animation: slideIn 0.3s ease-out;
        `;

    document.body.appendChild(notification);

    // Supprimer après 3 secondes
    setTimeout(() => {
      notification.remove();
    }, 3000);
  }

  getNotificationColor(type) {
    const colors = {
      success: "#4CAF50",
      error: "#F44336",
      warning: "#FF9800",
      info: "#2196F3",
    };
    return colors[type] || colors.info;
  }

  formatUptime(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);

    if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`;
    } else {
      return `${secs}s`;
    }
  }
}

// Initialiser l'application quand le DOM est chargé
document.addEventListener("DOMContentLoaded", () => {
  window.alimanteApp = new AlimanteApp();
});

// Ajouter les styles pour les notifications
const style = document.createElement("style");
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
`;
document.head.appendChild(style);
