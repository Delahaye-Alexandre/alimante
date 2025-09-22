#!/usr/bin/env python3
"""
Script de migration des valeurs hardcodées vers les fichiers de configuration
Remplace les valeurs hardcodées dans le code par des appels au ConfigService
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

class HardcodedValueMigrator:
    """
    Migrateur de valeurs hardcodées vers la configuration
    """
    
    def __init__(self, src_dir: str = "src", config_dir: str = "config"):
        self.src_dir = Path(src_dir)
        self.config_dir = Path(config_dir)
        self.migrations = []
        
        # Patterns de valeurs hardcodées à migrer
        self.patterns = {
            # Timeouts et intervalles
            'timeout_join': (r'\.join\(timeout=(\d+)\)', 'get_timeout("thread_join", {})'),
            'timeout_wait': (r'\.wait\((\d+)\)', 'get_interval("cleanup_wait", {})'),
            'sleep_seconds': (r'time\.sleep\((\d+)\)', 'get_interval("error_retry", {})'),
            
            # Ports et adresses
            'port_default': (r'port.*=.*(\d+)', 'get_hardcoded_value("network.default_port", {})'),
            'host_default': (r'host.*=.*["\']([^"\']+)["\']', 'get_hardcoded_value("network.default_host", "{}")'),
            
            # Dimensions et qualités
            'width_default': (r'width.*=.*(\d+)', 'get_hardcoded_value("services.camera.width", {})'),
            'height_default': (r'height.*=.*(\d+)', 'get_hardcoded_value("services.camera.height", {})'),
            'fps_default': (r'fps.*=.*(\d+)', 'get_hardcoded_value("services.camera.fps", {})'),
            'quality_default': (r'quality.*=.*(\d+)', 'get_hardcoded_value("services.camera.quality", {})'),
            
            # Limites et seuils
            'max_alerts': (r'max_alerts.*=.*(\d+)', 'get_hardcoded_value("services.alerts.max_alerts", {})'),
            'max_captures': (r'max_captures.*=.*(\d+)', 'get_hardcoded_value("services.camera.max_captures", {})'),
            'max_clients': (r'max_clients.*=.*(\d+)', 'get_hardcoded_value("services.streaming.max_clients", {})'),
            
            # Positions servo
            'servo_positions': (r'["\'](closed|half_open|open|full_open)["\']:\s*(\d+)', 'get_hardcoded_value("hardware.servo_positions.{}", {})'),
            
            # Fréquences PWM
            'pwm_frequency': (r'frequency.*=.*(\d+)', 'get_hardcoded_value("hardware.pwm_frequencies.servo", {})'),
            
            # Adresses I2C
            'i2c_address': (r'i2c_address.*=.*["\']([^"\']+)["\']', 'get_hardcoded_value("hardware.i2c_addresses.lcd", "{}")'),
        }
    
    def find_hardcoded_values(self) -> List[Dict]:
        """
        Trouve toutes les valeurs hardcodées dans le code
        
        Returns:
            Liste des valeurs hardcodées trouvées
        """
        hardcoded_values = []
        
        for py_file in self.src_dir.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                
                for line_num, line in enumerate(lines, 1):
                    for pattern_name, (pattern, replacement) in self.patterns.items():
                        matches = re.finditer(pattern, line)
                        for match in matches:
                            hardcoded_values.append({
                                'file': str(py_file),
                                'line': line_num,
                                'pattern': pattern_name,
                                'original': match.group(0),
                                'value': match.group(1),
                                'replacement': replacement,
                                'full_line': line.strip()
                            })
            
            except Exception as e:
                print(f"Erreur lecture fichier {py_file}: {e}")
        
        return hardcoded_values
    
    def generate_migration_script(self, hardcoded_values: List[Dict]) -> str:
        """
        Génère un script de migration
        
        Args:
            hardcoded_values: Liste des valeurs hardcodées
            
        Returns:
            Script de migration
        """
        script = '''#!/usr/bin/env python3
"""
Script de migration automatique des valeurs hardcodées
Généré automatiquement par migrate_hardcoded_values.py
"""

import os
import sys
from pathlib import Path

def migrate_file(file_path: str, line_num: int, old_line: str, new_line: str):
    """Migre une ligne dans un fichier"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if line_num <= len(lines):
            lines[line_num - 1] = new_line + '\\n'
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            print(f"✅ Migré: {file_path}:{line_num}")
            return True
        else:
            print(f"❌ Ligne {line_num} non trouvée dans {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur migration {file_path}:{line_num}: {e}")
        return False

def main():
    """Fonction principale de migration"""
    print("🔄 Début de la migration des valeurs hardcodées...")
    
    migrations = [
'''
        
        for i, value in enumerate(hardcoded_values):
            script += f'''        ({i+1}, "{value['file']}", {value['line']}, "{value['original']}", "{value['replacement']}"),
'''
        
        script += '''    ]
    
    success_count = 0
    total_count = len(migrations)
    
    for migration_id, file_path, line_num, old_line, new_line in migrations:
        print(f"Migration {migration_id}/{total_count}: {file_path}:{line_num}")
        
        if migrate_file(file_path, line_num, old_line, new_line):
            success_count += 1
    
    print(f"\\n📊 Résultats de la migration:")
    print(f"✅ Succès: {success_count}/{total_count}")
    print(f"❌ Échecs: {total_count - success_count}/{total_count}")
    
    if success_count == total_count:
        print("🎉 Migration terminée avec succès!")
    else:
        print("⚠️  Certaines migrations ont échoué. Vérifiez les erreurs ci-dessus.")

if __name__ == "__main__":
    main()
'''
        
        return script
    
    def create_config_updates(self, hardcoded_values: List[Dict]) -> Dict[str, str]:
        """
        Crée les mises à jour de configuration
        
        Args:
            hardcoded_values: Liste des valeurs hardcodées
            
        Returns:
            Dictionnaire des mises à jour de configuration
        """
        config_updates = {}
        
        # Grouper par type de configuration
        for value in hardcoded_values:
            pattern_name = value['pattern']
            val = value['value']
            
            if pattern_name == 'timeout_join':
                if 'timeouts' not in config_updates:
                    config_updates['timeouts'] = {}
                config_updates['timeouts']['thread_join'] = int(val)
            
            elif pattern_name == 'timeout_wait':
                if 'intervals' not in config_updates:
                    config_updates['intervals'] = {}
                config_updates['intervals']['cleanup_wait'] = int(val)
            
            elif pattern_name == 'sleep_seconds':
                if 'intervals' not in config_updates:
                    config_updates['intervals'] = {}
                config_updates['intervals']['error_retry'] = int(val)
            
            elif pattern_name == 'port_default':
                if 'network' not in config_updates:
                    config_updates['network'] = {}
                config_updates['network']['default_port'] = int(val)
            
            elif pattern_name == 'host_default':
                if 'network' not in config_updates:
                    config_updates['network'] = {}
                config_updates['network']['default_host'] = val
            
            elif pattern_name == 'width_default':
                if 'services' not in config_updates:
                    config_updates['services'] = {}
                if 'camera' not in config_updates['services']:
                    config_updates['services']['camera'] = {}
                config_updates['services']['camera']['width'] = int(val)
            
            elif pattern_name == 'height_default':
                if 'services' not in config_updates:
                    config_updates['services'] = {}
                if 'camera' not in config_updates['services']:
                    config_updates['services']['camera'] = {}
                config_updates['services']['camera']['height'] = int(val)
            
            elif pattern_name == 'fps_default':
                if 'services' not in config_updates:
                    config_updates['services'] = {}
                if 'camera' not in config_updates['services']:
                    config_updates['services']['camera'] = {}
                config_updates['services']['camera']['fps'] = int(val)
            
            elif pattern_name == 'quality_default':
                if 'services' not in config_updates:
                    config_updates['services'] = {}
                if 'camera' not in config_updates['services']:
                    config_updates['services']['camera'] = {}
                config_updates['services']['camera']['quality'] = int(val)
            
            elif pattern_name == 'max_alerts':
                if 'services' not in config_updates:
                    config_updates['services'] = {}
                if 'alerts' not in config_updates['services']:
                    config_updates['services']['alerts'] = {}
                config_updates['services']['alerts']['max_alerts'] = int(val)
            
            elif pattern_name == 'max_captures':
                if 'services' not in config_updates:
                    config_updates['services'] = {}
                if 'camera' not in config_updates['services']:
                    config_updates['services']['camera'] = {}
                config_updates['services']['camera']['max_captures'] = int(val)
            
            elif pattern_name == 'max_clients':
                if 'services' not in config_updates:
                    config_updates['services'] = {}
                if 'streaming' not in config_updates['services']:
                    config_updates['services']['streaming'] = {}
                config_updates['services']['streaming']['max_clients'] = int(val)
        
        return config_updates
    
    def run_analysis(self):
        """Exécute l'analyse complète"""
        print("🔍 Analyse des valeurs hardcodées...")
        
        # Trouver les valeurs hardcodées
        hardcoded_values = self.find_hardcoded_values()
        
        print(f"📊 {len(hardcoded_values)} valeurs hardcodées trouvées")
        
        # Afficher le résumé
        print("\\n📋 Résumé des valeurs hardcodées:")
        for value in hardcoded_values:
            print(f"  {value['file']}:{value['line']} - {value['pattern']} = {value['value']}")
        
        # Créer les mises à jour de configuration
        config_updates = self.create_config_updates(hardcoded_values)
        
        print("\\n🔧 Mises à jour de configuration suggérées:")
        for section, values in config_updates.items():
            print(f"  {section}: {values}")
        
        # Générer le script de migration
        migration_script = self.generate_migration_script(hardcoded_values)
        
        with open('migrate_hardcoded_script.py', 'w', encoding='utf-8') as f:
            f.write(migration_script)
        
        print("\\n✅ Script de migration généré: migrate_hardcoded_script.py")
        print("\\n📝 Pour appliquer les migrations:")
        print("  1. Vérifiez le script généré")
        print("  2. Exécutez: python migrate_hardcoded_script.py")
        print("  3. Vérifiez que les changements sont corrects")
        
        return hardcoded_values, config_updates

def main():
    """Fonction principale"""
    print("🚀 Migration des valeurs hardcodées Alimante")
    print("=" * 50)
    
    migrator = HardcodedValueMigrator()
    hardcoded_values, config_updates = migrator.run_analysis()
    
    print("\\n🎯 Prochaines étapes:")
    print("1. Vérifiez les valeurs hardcodées identifiées")
    print("2. Mettez à jour le fichier config/hardcoded_values.json si nécessaire")
    print("3. Exécutez le script de migration généré")
    print("4. Testez l'application après migration")

if __name__ == "__main__":
    main()
