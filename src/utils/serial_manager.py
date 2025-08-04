import serial
import logging
import time
from typing import Optional

class SerialManager:
    def __init__(self, port: str, baud_rate: int, retry_attempts: int = 3):
        self.port = port
        self.baud_rate = baud_rate
        self.retry_attempts = retry_attempts
        self.connection: Optional[serial.Serial] = None
        self.initialize_connection()

    def initialize_connection(self) -> bool:
        for attempt in range(self.retry_attempts):
            try:
                self.connection = serial.Serial(port=self.port, baudrate=self.baud_rate, timeout=1)
                logging.info(f"Connexion série établie sur {self.port}")
                return True
            except serial.SerialException as e:
                logging.warning(f"Tentative {attempt+1} échouée : {e}")
                time.sleep(2)
        return False

    def is_connected(self) -> bool:
        return self.connection is not None and self.connection.is_open

    def send_command(self, command: str, max_retries: int = 3) -> Optional[str]:
        """
        Envoie une commande via la connexion série avec retry logic.
        
        Args:
            command: Commande à envoyer
            max_retries: Nombre maximum de tentatives
            
        Returns:
            Réponse de l'Arduino ou None si échec
        """
        if not self.is_connected():
            logging.error("Connexion série non établie")
            return None
            
        for attempt in range(max_retries):
            try:
                # Envoi de la commande
                command_with_newline = f"{command}\n"
                self.connection.write(command_with_newline.encode('utf-8'))
                self.connection.flush()  # Force l'envoi immédiat
                
                # Lecture de la réponse
                response = self.connection.readline().decode('utf-8').strip()
                
                if response:
                    logging.debug(f"Commande '{command}' envoyée, réponse: '{response}'")
                    return response
                else:
                    logging.warning(f"Pas de réponse pour la commande '{command}' (tentative {attempt+1})")
                    
            except serial.SerialException as e:
                logging.error(f"Erreur série lors de l'envoi de '{command}': {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)  # Pause avant retry
                continue
            except UnicodeDecodeError as e:
                logging.error(f"Erreur de décodage pour la commande '{command}': {e}")
                continue
            except Exception as e:
                logging.error(f"Erreur inattendue pour la commande '{command}': {e}")
                continue
                
        logging.error(f"Échec de l'envoi de la commande '{command}' après {max_retries} tentatives")
        return None

    def close_connection(self) -> None:
        """Ferme proprement la connexion série."""
        if self.connection and self.connection.is_open:
            self.connection.close()
            logging.info("Connexion série fermée")