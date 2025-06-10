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

def main():
    """Función principal de la aplicación."""
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
        
        # Configurar manejo de cierre
        def close_future(future, loop):
            loop.call_later(10, future.cancel)
            future.cancel()
        
        future = asyncio.Future()
        app.lastWindowClosed.connect(lambda: close_future(future, loop))
        
        # Ejecutar aplicación
        logger.info("Aplicación iniciada correctamente")
        
        async def run_app():
            await wizard_app.initialize()
            try:
                await future
            except asyncio.CancelledError:
                pass
            finally:
                await wizard_app.cleanup()
        
        return qasync.run(run_app())
        
    except Exception as e:
        logger.error(f"Error fatal en la aplicación: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())