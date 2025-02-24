import os
import json

def select_config():
    """
        Ce module permet de sélectionner une configuration système en fonction du type d'insectes que l'utilisateur souhaite s'occuper.

        Pour cela, l'utilsateur choisira dans le dossier config une configuration trié entre l'ordre (ex: orthoptères, coléoptères, diptères, lépidoptères).

        Ensuite, l'utilisateur selectionnera la configuration qui correspond à la famille (ex: mantidae, tenebrionidae, drosophilidae, saturniidae).

        Enfin, l'utilisateur choisira la configuration qui correspond à l'espèce (ex: mantis religiosa, tenebrio molitor, drosophila melanogaster, saturnia pyri).

        La configuration sélectionnée sera alors chargée et utilisée pour initialiser le système.
    """

    orders = {
        "1": "orthopteres",
        "2": "coleopteres",
        "3": "dipteres",
        "4": "lepidopteres"
    }

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

    print("Sélectionnez l'ordre d'insectes :")
    for key, value in orders.items():
        print(f"{key}. {value.capitalize()}")
    order_choice = input("Entrez le numéro correspondant : ")

    if order_choice not in orders:
        print("Choix invalide.")
        return None

    selected_order = orders[order_choice]

    print(f"Sélectionnez la famille d'insectes dans l'ordre {selected_order} :")
    for key, value in families[selected_order].items():
        print(f"{key}. {value.capitalize()}")
    family_choice = input("Entrez le numéro correspondant : ")

    if family_choice not in families[selected_order]:
        print("Choix invalide.")
        return None

    selected_family = families[selected_order][family_choice]

    print(f"Sélectionnez l'espèce d'insectes dans la famille {selected_family} :")
    for key, value in species[selected_family].items():
        print(f"{key}. {value.replace('_', ' ').capitalize()}")
    species_choice = input("Entrez le numéro correspondant : ")

    if species_choice not in species[selected_family]:
        print("Choix invalide.")
        return None

    selected_species = species[selected_family][species_choice]

    config_path = os.path.join("config", selected_order, selected_family, f"{selected_species}.json")
    return config_path

def create_custom_config():
    """
    Permet à l'utilisateur de créer une configuration personnalisée.
    """
    config = {}

    config['temperature'] = {
        'target': float(input("Entrez la température cible (en °C) : ")),
        'tolerance': float(input("Entrez la tolérance de température (en °C) : "))
    }

    config['humidity'] = {
        'target': float(input("Entrez le taux d'humidité cible (en %) : ")),
        'tolerance': float(input("Entrez la tolérance d'humidité (en %) : "))
    }

    config['location'] = {
        'latitude': float(input("Entrez la latitude : ")),
        'longitude': float(input("Entrez la longitude : "))
    }

    config['feeding'] = {
        'interval_days': int(input("Entrez l'intervalle de jours entre les nourrissages : ")),
        'feed_count': int(input("Entrez le nombre de mouches à libérer à chaque nourrissage : "))
    }

    config['lighting'] = {
        'sunrise': input("Entrez l'heure de lever du soleil (HH:MM) : "),
        'sunset': input("Entrez l'heure de coucher du soleil (HH:MM) : ")
    }

    filename = input("Entrez le nom du fichier de configuration (sans extension) : ")
    filepath = os.path.join("config", f"{filename}.json")

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

    print(f"Configuration sauvegardée dans {filepath}")
    return filepath