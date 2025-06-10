#!/usr/bin/env python3
"""
Configuración específica para desarrollo y testing de SHARA Wizard
"""

import os
import sys
from pathlib import Path

# Agregar directorio raíz al path para importaciones
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

# Configuración de desarrollo
DEVELOPMENT_CONFIG = {
    # URLs de desarrollo/testing
    'server_url': 'http://localhost:8081',
    'web_url': 'http://localhost:5173',
    
    # Configuración de logging para desarrollo
    'log_level': 'DEBUG',
    'log_file': None,  # Solo consola en desarrollo
    
    # Configuración de UI para desarrollo
    'window_width': 1200,
    'window_height': 800,
    'theme': 'light',
    
    # Configuración de video para desarrollo
    'video_fps': 10,  # Menor FPS para desarrollo
    'video_width': 240,
    'video_height': 180,
    
    # Timeouts más largos para debugging
    'socket_timeout': 30,
    'reconnect_attempts': 3,
    'reconnect_delay': 2,
    
    # Configuración de testing
    'enable_mock_services': False,
    'enable_debug_ui': True,
    'auto_connect': False,
    
    # Configuración de desarrollo específica
    'hot_reload': True,
    'show_performance_metrics': True,
    'enable_experimental_features': True
}

# Configuración de testing
TESTING_CONFIG = {
    # URLs de testing
    'server_url': 'http://test.localhost:8081',
    'web_url': 'http://test.localhost:5173',
    
    # Configuración minimal para tests
    'log_level': 'WARNING',
    'window_width': 800,
    'window_height': 600,
    
    # Configuración específica de testing
    'enable_mock_services': True,
    'enable_debug_ui': False,
    'auto_connect': True,
    'fast_mode': True,
    
    # Timeouts cortos para tests rápidos
    'socket_timeout': 5,
    'reconnect_attempts': 1,
    'reconnect_delay': 1,
    
    # Configuración de datos de prueba
    'mock_user_id': 'test_user_001',
    'mock_session_id': 'test_session_001',
    'simulate_network_issues': False
}

def setup_development_environment():
    """Configura el entorno de desarrollo."""
    print("Configurando entorno de desarrollo...")
    
    # Configurar variables de entorno para desarrollo
    for key, value in DEVELOPMENT_CONFIG.items():
        env_key = f"DEV_{key.upper()}"
        os.environ[env_key] = str(value)
    
    # Configurar paths de desarrollo
    os.environ['PYTHONPATH'] = str(ROOT_DIR)
    os.environ['DEVELOPMENT_MODE'] = 'true'
    
    # Crear directorios de desarrollo si no existen
    dev_dirs = [
        ROOT_DIR / 'logs' / 'dev',
        ROOT_DIR / 'temp' / 'dev',
        ROOT_DIR / 'test_data'
    ]
    
    for dir_path in dev_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    print("Entorno de desarrollo configurado")

def setup_testing_environment():
    """Configura el entorno de testing."""
    print("Configurando entorno de testing...")
    
    # Configurar variables de entorno para testing
    for key, value in TESTING_CONFIG.items():
        env_key = f"TEST_{key.upper()}"
        os.environ[env_key] = str(value)
    
    # Configurar paths de testing
    os.environ['TESTING_MODE'] = 'true'
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'  # Para tests sin GUI
    
    # Crear directorios de testing
    test_dirs = [
        ROOT_DIR / 'test_logs',
        ROOT_DIR / 'test_temp',
        ROOT_DIR / 'test_output'
    ]
    
    for dir_path in test_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    print("Entorno de testing configurado")

def create_mock_data():
    """Crea datos de prueba para desarrollo."""
    mock_data_dir = ROOT_DIR / 'test_data'
    mock_data_dir.mkdir(exist_ok=True)
    
    # Datos de usuario mock
    mock_user = {
        'user_id': 'dev_user_001',
        'user_name': 'Usuario de Desarrollo',
        'is_new_user': False,
        'needs_identification': False
    }
    
    # Datos de mensajes mock
    mock_messages = [
        {
            'text': 'Hola, soy un mensaje de prueba',
            'sender': 'client',
            'timestamp': '2025-01-01T10:00:00'
        },
        {
            'text': 'Esta es una respuesta automática de prueba',
            'sender': 'robot',
            'robot_state': 'Joy',
            'timestamp': '2025-01-01T10:00:05'
        }
    ]
    
    # Configuración mock del servidor
    mock_server_config = {
        'url': 'http://localhost:8081',
        'endpoints': {
            'websocket': '/message-socket',
            'video': '/video-socket',
            'api': '/api'
        },
        'features': {
            'face_recognition': True,
            'text_to_speech': True,
            'openai_integration': True
        }
    }
    
    # Guardar datos mock
    import json
    
    with open(mock_data_dir / 'mock_user.json', 'w') as f:
        json.dump(mock_user, f, indent=2)
    
    with open(mock_data_dir / 'mock_messages.json', 'w') as f:
        json.dump(mock_messages, f, indent=2)
    
    with open(mock_data_dir / 'mock_server_config.json', 'w') as f:
        json.dump(mock_server_config, f, indent=2)
    
    print("Datos mock creados en test_data/")

def run_development_server():
    """Ejecuta un servidor de desarrollo mock."""
    try:
        import socketio
        import threading
        from datetime import datetime
        
        print("Iniciando servidor de desarrollo mock...")
        
        # Crear servidor Socket.IO simple
        sio = socketio.Server(cors_allowed_origins="*")
        app = socketio.WSGIApp(sio)
        
        @sio.event
        def connect(sid, environ):
            print(f"Cliente conectado: {sid}")
            sio.emit('registration_success', {'status': 'ok'}, room=sid)
        
        @sio.event
        def disconnect(sid):
            print(f"Cliente desconectado: {sid}")
        
        @sio.event
        def register_operator(sid, data):
            print(f"Operador registrado: {data}")
            sio.emit('registration_confirmed', room=sid)
        
        @sio.event
        def message(sid, data):
            print(f"Mensaje recibido: {data}")
            # Respuesta automática mock
            response = {
                'text': f"Respuesta automática para: {data.get('text', '')}",
                'state': 'Attention'
            }
            sio.emit('openai_message', response, room=sid)
        
        # Ejecutar servidor en thread separado
        def run_server():
            import eventlet
            eventlet.wsgi.server(eventlet.listen(('localhost', 8081)), app)
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        print("Servidor mock ejecutándose en http://localhost:8081")
        print("Presiona Ctrl+C para detener")
        
        return server_thread
        
    except ImportError:
        print("socketio no disponible para servidor mock")
        return None

def setup_ide_configuration():
    """Configura archivos para IDEs (VS Code, PyCharm, etc.)."""
    
    # Configuración de VS Code
    vscode_dir = ROOT_DIR / '.vscode'
    vscode_dir.mkdir(exist_ok=True)
    
    # settings.json para VS Code
    vscode_settings = {
        "python.defaultInterpreterPath": "./venv/bin/python",
        "python.linting.enabled": True,
        "python.linting.flake8Enabled": True,
        "python.formatting.provider": "black",
        "python.testing.pytestEnabled": True,
        "python.testing.pytestArgs": ["tests/"],
        "files.associations": {
            "*.qml": "qml"
        }
    }
    
    # launch.json para debugging
    vscode_launch = {
        "version": "0.2.0",
        "configurations": [
            {
                "name": "SHARA Wizard - Debug",
                "type": "python",
                "request": "launch",
                "program": "main.py",
                "console": "integratedTerminal",
                "env": {
                    "DEVELOPMENT_MODE": "true",
                    "LOG_LEVEL": "DEBUG"
                }
            },
            {
                "name": "SHARA Wizard - Test",
                "type": "python",
                "request": "launch",
                "module": "pytest",
                "args": ["tests/", "-v"],
                "console": "integratedTerminal"
            }
        ]
    }
    
    import json
    
    with open(vscode_dir / 'settings.json', 'w') as f:
        json.dump(vscode_settings, f, indent=2)
    
    with open(vscode_dir / 'launch.json', 'w') as f:
        json.dump(vscode_launch, f, indent=2)
    
    print("Configuración de VS Code creada")

def main():
    """Función principal para configuración de desarrollo."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Configuración de desarrollo para SHARA Wizard')
    parser.add_argument('--mode', choices=['dev', 'test'], default='dev',
                       help='Modo de configuración')
    parser.add_argument('--mock-server', action='store_true',
                       help='Ejecutar servidor mock para desarrollo')
    parser.add_argument('--create-data', action='store_true',
                       help='Crear datos de prueba')
    parser.add_argument('--setup-ide', action='store_true',
                       help='Configurar archivos para IDEs')
    
    args = parser.parse_args()
    
    print("SHARA Wizard - Configuración de Desarrollo")
    print("=" * 50)
    
    if args.mode == 'dev':
        setup_development_environment()
    elif args.mode == 'test':
        setup_testing_environment()
    
    if args.create_data:
        create_mock_data()
    
    if args.setup_ide:
        setup_ide_configuration()
    
    if args.mock_server:
        server_thread = run_development_server()
        if server_thread:
            try:
                # Mantener el servidor ejecutándose
                server_thread.join()
            except KeyboardInterrupt:
                print("\nDeteniendo servidor mock...")
    
    print("\nConfiguración de desarrollo completada")
    
    if args.mode == 'dev':
        print("\nPara ejecutar en modo desarrollo:")
        print("   python main.py")
        print("\nPara ejecutar tests:")
        print("   python -m pytest tests/ -v")

if __name__ == "__main__":
    main()