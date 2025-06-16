#!/usr/bin/env python3
"""
SHARA Wizard of Oz Interface
Punto de entrada principal de la aplicación
"""

import sys
import asyncio
import qasync
from qasync import QEventLoop
from PyQt6.QtWidgets import QApplication

from core.app import SharaWizardApp
from utils.logger import setup_logger
from config.settings import AppSettings

shutdown_requested = False

def main():
    """Función principal de la aplicación."""
    # Variable global para manejar el cierre de la aplicación
    global shutdown_requested
    shutdown_requested = False

    # Configurar logging
    logger = setup_logger()
    logger.info("Iniciando SHARA Wizard of Oz Interface")
    
    try:
        # Crear aplicación Qt
        app = QApplication(sys.argv)
        app.setApplicationName("SHARA Wizard Interface")
        app.setApplicationVersion("2.0.0")
        app.setOrganizationName("SHARA Project")
        
        # Configurar event loop asíncrono
        loop = QEventLoop(app)
        asyncio.set_event_loop(loop)
        
        # Crear y mostrar la aplicación principal
        wizard_app = SharaWizardApp()
        wizard_app.show()
        
        
        async def shutdown_app():
            """Maneja el cierre seguro de la aplicación."""
            try:
                await wizard_app.cleanup()
            except Exception as e:
                logger.error(f"Error durante cleanup: {e}")

        def request_shutdown():
            global shutdown_requested
            shutdown_requested = True

        app.lastWindowClosed.connect(request_shutdown)
        
        # Ejecutar aplicación
        logger.info("Aplicación iniciada correctamente")
        
        async def run_app():
            global shutdown_requested
            await wizard_app.initialize()
            
            while not shutdown_requested:
                await asyncio.sleep(0.1)

            await shutdown_app()
        try:
            return qasync.run(run_app())
        except KeyboardInterrupt:
            logger.info("Interrupción del usuario, cerrando la aplicación...")
            return 0
        except Exception as e:
            logger.error(f"Error en la aplicación: {e}")
            return 1
        finally:
            try:
                pending = asyncio.all_tasks()
                for task in pending:
                    task.cancel()
            except Exception:
                pass
        
    except Exception as e:
        logger.error(f"Error fatal en la aplicación: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())