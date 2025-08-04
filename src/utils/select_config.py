import os
import json

def select_config():
    """
    Sélectionne une configuration système en fonction du type d'insectes.
    
    L'utilisateur choisit:
    1. L'ordre (ex: orthoptères, coléoptères, diptères, lépidoptères)
    2. La famille (ex: mantidae, tenebrionidae, drosophilidae, saturniidae)
    3. L'espèce (ex: mantis religiosa, tenebrio molitor, drosophila melanogaster, saturnia pyri)
    
    Returns:
        str: Chemin vers le fichier de configuration sélectionné ou None si annulé
    """

    # Définition des ordres disponibles
    orders = {
        "1": "orthopteres",
        "2": "coleopteres",
        "3": "dipteres",
        "4": "lepidopteres"
    }

    # Définition des familles par ordre
    families = {
        "orthopteres": {
            "1": "mantidae"
        },
        "coleopteres": {
            "1": "tenebrionidae"
        },
        "dipteres": {
            "1": "drosophilidae"
        },
        "lepidopteres": {
            "1": "saturniidae"
        }
    }

    # Définition des espèces par famille
    species = {
        "mantidae": {
            "1": "mantis_religiosa"
        },
        "tenebrionidae": {
            "1": "tenebrio_molitor"
        },
        "drosophilidae": {
            "1": "drosophila_melanogaster"
        },
        "saturniidae": {
            "1": "saturnia_pyri"
        }
    }

    # Sélection de l'ordre
    print("Sélectionnez l'ordre d'insectes :")
    for key, value in orders.items():
        print(f"{key}. {value.capitalize()}")
    order_choice = input("Entrez le numéro correspondant : ")

    if order_choice not in orders:
        print("Choix invalide.")
        return None

    selected_order = orders[order_choice]

    # Sélection de la famille
    print(f"Sélectionnez la famille d'insectes dans l'ordre {selected_order} :")
    for key, value in families[selected_order].items():
        print(f"{key}. {value.capitalize()}")
    family_choice = input("Entrez le numéro correspondant : ")

    if family_choice not in families[selected_order]:
        print("Choix invalide.")
        return None

    selected_family = families[selected_order][family_choice]

    # Sélection de l'espèce
    print(f"Sélectionnez l'espèce d'insectes dans la famille {selected_family} :")
    for key, value in species[selected_family].items():
        print(f"{key}. {value.replace('_', ' ').capitalize()}")
    species_choice = input("Entrez le numéro correspondant : ")

    if species_choice not in species[selected_family]:
        print("Choix invalide.")
        return None

    selected_species = species[selected_family][species_choice]

    # Construction du chemin vers le fichier de configuration
    config_path = os.path.join("config", selected_order, selected_family, f"{selected_species}.json")
    
    # Vérification de l'existence du fichier
    if not os.path.exists(config_path):
        print(f"Erreur: Le fichier de configuration {config_path} n'existe pas.")
        return None
        
    print(f"Configuration sélectionnée: {config_path}")
    return config_path

def create_custom_config():
    """
    Permet à l'utilisateur de créer une configuration personnalisée.
    
    Returns:
        str: Chemin vers le fichier de configuration créé ou None si annulé
    """
    config = {}

    # Informations de base
    config['species_name'] = input("Entrez le nom scientifique de l'espèce : ")
    config['common_name'] = input("Entrez le nom commun de l'espèce : ")
    
    # Configuration de température
    config['temperature'] = {
        'optimal': float(input("Entrez la température optimale (en °C) : ")),
        'tolerance': float(input("Entrez la tolérance de température (en °C) : "))
    }

    # Configuration d'humidité
    config['humidity'] = {
        'optimal': float(input("Entrez le taux d'humidité optimal (en %) : ")),
        'tolerance': float(input("Entrez la tolérance d'humidité (en %) : "))
    }

    # Configuration d'alimentation
    config['feeding'] = {
        'interval_days': int(input("Entrez l'intervalle de jours entre les nourrissages : ")),
        'feed_count': int(input("Entrez la quantité de nourriture à distribuer : "))
    }

    # Emplacement de sauvegarde
    filename = input("Entrez le nom du fichier de configuration (sans extension) : ")
    filepath = os.path.join("config", "custom", f"{filename}.json")
    
    # Création du dossier custom s'il n'existe pas
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    # Sauvegarde du fichier
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

    print(f"Configuration sauvegardée dans {filepath}")
    return filepath