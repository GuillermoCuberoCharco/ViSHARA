#!/usr/bin/env python3
"""
Script de instalación y configuración para SHARA Wizard of Oz Interface
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional

def print_banner():
    """Muestra el banner de instalación."""
    banner = """
    ╔════════════════════════════════════════════════════════════════╗
    ║                 SHARA Wizard of Oz Interface                   ║
    ║                    Script de Instalación                       ║
    ║                        Versión 2.0.0                           ║
    ╚════════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_python_version():
    """Verifica que la versión de Python sea compatible."""
    min_version = (3, 8)
    current_version = sys.version_info[:2]
    
    if current_version < min_version:
        print(f"❌ Error: Se requiere Python {min_version[0]}.{min_version[1]} o superior.")
        print(f"   Versión actual: {current_version[0]}.{current_version[1]}")
        sys.exit(1)
    
    print(f"✅ Python {current_version[0]}.{current_version[1]} detectado")

def check_system_requirements():
    """Verifica los requisitos del sistema."""
    print("\n📋 Verificando requisitos del sistema...")
    
    # Verificar Python
    check_python_version()
    
    # Verificar pip
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], 
                      check=True, capture_output=True)
        print("✅ pip disponible")
    except subprocess.CalledProcessError:
        print("❌ Error: pip no está disponible")
        sys.exit(1)
    
    # Verificar sistema operativo y dependencias específicas
    import platform
    system = platform.system()
    print(f"✅ Sistema operativo: {system} {platform.release()}")
    
    if system == "Linux":
        print("ℹ️  En Linux, asegúrate de tener instalado: python3-pyqt6.qtwebengine")
        print("   Comando: sudo apt-get install python3-pyqt6.qtwebengine")
    elif system == "Windows":
        print("ℹ️  En Windows, puedes necesitar: pip install pywin32")
    elif system == "Darwin":  # macOS
        print("ℹ️  En macOS, puedes necesitar: pip install pyobjc-framework-Cocoa")

def create_virtual_environment():
    """Crea un entorno virtual."""
    venv_path = Path("venv")
    
    if venv_path.exists():
        print("ℹ️  El entorno virtual ya existe")
        return
    
    print("\n🐍 Creando entorno virtual...")
    try:
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("✅ Entorno virtual creado")
    except subprocess.CalledProcessError:
        print("❌ Error creando entorno virtual")
        sys.exit(1)

def get_pip_command():
    """Obtiene el comando pip apropiado para el sistema."""
    if sys.platform == "win32":
        return ["venv\\Scripts\\pip.exe"]
    else:
        return ["venv/bin/pip"]

def install_dependencies():
    """Instala las dependencias del proyecto."""
    print("\n📦 Instalando dependencias...")
    
    pip_cmd = get_pip_command()
    
    try:
        # Actualizar pip
        subprocess.run(pip_cmd + ["install", "--upgrade", "pip"], check=True)
        print("✅ pip actualizado")
        
        # Instalar dependencias
        subprocess.run(pip_cmd + ["install", "-r", "requirements.txt"], check=True)
        print("✅ Dependencias instaladas")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error instalando dependencias: {e}")
        sys.exit(1)

def create_directories():
    """Crea los directorios necesarios."""
    print("\n📁 Creando directorios...")
    
    directories = [
        "logs",
        "temp", 
        "resources",
        "resources/icons",
        "data"
    ]
    
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✅ Directorio creado: {dir_path}")

def setup_environment_file():
    """Configura el archivo de entorno."""
    print("\n⚙️  Configurando archivo de entorno...")
    
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        shutil.copy(env_example, env_file)
        print("✅ Archivo .env creado desde .env.example")
        print("ℹ️  Edita .env para configurar tu entorno específico")
    elif env_file.exists():
        print("ℹ️  El archivo .env ya existe")
    else:
        print("⚠️  No se encontró .env.example, creando .env básico...")
        
        basic_env = """# Configuración básica de SHARA Wizard
SHARA_SERVER_URL=https://vishara.onrender.com
SHARA_WEB_URL=https://vi-shara.vercel.app
LOG_LEVEL=INFO
WINDOW_WIDTH=1400
WINDOW_HEIGHT=900
"""
        env_file.write_text(basic_env)
        print("✅ Archivo .env básico creado")

def download_default_icons():
    """Descarga iconos por defecto si no existen."""
    print("\n🎨 Configurando recursos...")
    
    icons_dir = Path("resources/icons")
    
    # Lista de iconos necesarios (nombres sin extensión)
    required_icons = [
        "send", "auto", "attention", "hello", "no", "yes",
        "angry", "sad", "joy", "blush"
    ]
    
    # Crear iconos placeholder si no existen
    for icon_name in required_icons:
        icon_file = icons_dir / f"{icon_name}.png"
        if not icon_file.exists():
            # Crear un archivo placeholder
            icon_file.write_text(f"# Placeholder for {icon_name} icon")
    
    print("✅ Recursos configurados")

def create_run_scripts():
    """Crea scripts de ejecución."""
    print("\n🚀 Creando scripts de ejecución...")
    
    # Script para Windows
    windows_script = """@echo off
echo Iniciando SHARA Wizard of Oz Interface...
venv\\Scripts\\python.exe main.py
pause
"""
    Path("run_wizard.bat").write_text(windows_script)
    
    # Script para Unix/Linux/macOS
    unix_script = """#!/bin/bash
echo "Iniciando SHARA Wizard of Oz Interface..."
venv/bin/python main.py
"""
    unix_script_path = Path("run_wizard.sh")
    unix_script_path.write_text(unix_script)
    
    # Hacer ejecutable en sistemas Unix
    if sys.platform != "win32":
        os.chmod(unix_script_path, 0o755)
    
    print("✅ Scripts de ejecución creados")
    print("   Windows: run_wizard.bat")
    print("   Unix/Linux/macOS: ./run_wizard.sh")

def run_initial_tests():
    """Ejecuta pruebas básicas de la instalación."""
    print("\n🧪 Ejecutando pruebas básicas...")
    
    python_cmd = get_pip_command()[0].replace("pip", "python")
    
    try:
        # Probar importaciones básicas - sin emojis para compatibilidad
        test_script = """
import sys
import os
sys.path.insert(0, '.')

# Configurar encoding para Windows
if os.name == 'nt':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())

try:
    from PyQt6.QtWidgets import QApplication
    print("[OK] PyQt6 disponible")
except ImportError as e:
    print(f"[ERROR] Error importando PyQt6: {e}")
    sys.exit(1)

try:
    import socketio
    print("[OK] python-socketio disponible")
except ImportError as e:
    print(f"[ERROR] Error importando socketio: {e}")
    sys.exit(1)

try:
    import cv2
    print("[OK] OpenCV disponible")
except ImportError as e:
    print("[WARNING] OpenCV no disponible (opcional)")

try:
    import numpy
    print("[OK] NumPy disponible")
except ImportError as e:
    print(f"[ERROR] Error importando NumPy: {e}")
    sys.exit(1)

try:
    import qasync
    print("[OK] qasync disponible")
except ImportError as e:
    print(f"[ERROR] Error importando qasync: {e}")
    sys.exit(1)

print("[SUCCESS] Todas las importaciones básicas exitosas")
"""
        
        # Ejecutar con encoding UTF-8
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        result = subprocess.run([python_cmd, "-c", test_script], 
                              capture_output=True, text=True, 
                              encoding='utf-8', env=env)
        
        if result.returncode == 0:
            # Reemplazar marcadores con emojis para mostrar
            output = result.stdout
            output = output.replace("[OK]", "✅")
            output = output.replace("[ERROR]", "❌") 
            output = output.replace("[WARNING]", "⚠️ ")
            output = output.replace("[SUCCESS]", "✅")
            print(output)
        else:
            print("❌ Error en pruebas básicas:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error ejecutando pruebas: {e}")
        return False
    
    return True

def print_post_install_instructions():
    """Muestra instrucciones post-instalación."""
    instructions = """
    ╔════════════════════════════════════════════════════════════════╗
    ║                     ¡Instalación Completada!                   ║
    ╚════════════════════════════════════════════════════════════════╝
    
    📋 Próximos pasos:
    
    1. 📝 Edita el archivo .env con tu configuración específica:
       - SHARA_SERVER_URL: URL de tu servidor SHARA
       - SHARA_WEB_URL: URL de la interfaz web
       - LOG_LEVEL: Nivel de logging deseado
    
    2. 🚀 Ejecuta la aplicación:
       • Windows: run_wizard.bat
       • Linux/macOS: ./run_wizard.sh
       • Manual: venv/bin/python main.py (o venv\\Scripts\\python.exe main.py en Windows)
    
    3. 📁 Directorios importantes:
       • logs/: Archivos de log de la aplicación
       • resources/: Recursos de la aplicación (iconos, etc.)
       • temp/: Archivos temporales
    
    4. 🔧 Configuración adicional:
       • Revisa config/settings.py para configuraciones avanzadas
       • Consulta la documentación en README.md
    
    ❓ ¿Problemas?
       • Revisa los logs en logs/shara_wizard.log
       • Verifica que las URLs en .env sean accesibles
       • Asegúrate de tener conexión a internet
    
    🎉 ¡Disfruta usando SHARA Wizard of Oz Interface!
    """
    print(instructions)

def main():
    """Función principal de instalación."""
    print_banner()
    
    try:
        # Verificar requisitos
        check_system_requirements()
        
        # Crear entorno virtual
        create_virtual_environment()
        
        # Instalar dependencias
        install_dependencies()
        
        # Crear estructura de directorios
        create_directories()
        
        # Configurar archivos de entorno
        setup_environment_file()
        
        # Configurar recursos
        download_default_icons()
        
        # Crear scripts de ejecución
        create_run_scripts()
        
        # Ejecutar pruebas básicas
        if run_initial_tests():
            print_post_install_instructions()
        else:
            print("\n⚠️  La instalación se completó pero hay problemas en las pruebas.")
            print("   Revisa los mensajes de error anteriores.")
            
    except KeyboardInterrupt:
        print("\n\n❌ Instalación cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error durante la instalación: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()