"""
Sistema de eventos centralizado para SHARA Wizard
"""

import asyncio
from typing import Dict, List, Callable, Any, Optional
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal

from utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class Event:
    """Representa un evento en el sistema."""
    name: str
    data: Any = None
    timestamp: datetime = field(default_factory=datetime.now)
    source: Optional[str] = None

class EventManager(QObject):
    """
    Gestor de eventos centralizado que permite comunicación desacoplada
    entre diferentes componentes de la aplicación.
    """
    
    # Señal Qt para eventos globales
    event_emitted = pyqtSignal(str, object)
    
    def __init__(self):
        super().__init__()
        
        # Almacén de suscriptores
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._async_subscribers: Dict[str, List[Callable]] = defaultdict(list)
        
        # Historial de eventos (limitado)
        self._event_history: List[Event] = []
        self._max_history = 1000
        
        # Estado del gestor
        self._is_active = True
        
        logger.debug("EventManager inicializado")
    
    def subscribe(self, event_name: str, callback: Callable, async_callback: bool = False):
        """
        Suscribe un callback a un evento específico.
        
        Args:
            event_name: Nombre del evento
            callback: Función a llamar cuando ocurra el evento
            async_callback: Si el callback es asíncrono
        """
        if not callable(callback):
            raise ValueError("El callback debe ser una función callable")
        
        if async_callback:
            self._async_subscribers[event_name].append(callback)
            logger.debug(f"Suscriptor asíncrono agregado para '{event_name}'")
        else:
            self._subscribers[event_name].append(callback)
            logger.debug(f"Suscriptor agregado para '{event_name}'")
    
    def unsubscribe(self, event_name: str, callback: Callable, async_callback: bool = False):
        """
        Desuscribe un callback de un evento específico.
        
        Args:
            event_name: Nombre del evento
            callback: Función a desuscribir
            async_callback: Si el callback es asíncrono
        """
        try:
            if async_callback:
                self._async_subscribers[event_name].remove(callback)
                logger.debug(f"Suscriptor asíncrono removido de '{event_name}'")
            else:
                self._subscribers[event_name].remove(callback)
                logger.debug(f"Suscriptor removido de '{event_name}'")
        except ValueError:
            logger.warning(f"Callback no encontrado para evento '{event_name}'")
    
    def emit(self, event_name: str, data: Any = None, source: Optional[str] = None):
        """
        Emite un evento a todos los suscriptores.
        
        Args:
            event_name: Nombre del evento
            data: Datos asociados al evento
            source: Fuente que emite el evento
        """
        if not self._is_active:
            return
        
        # Crear evento
        event = Event(name=event_name, data=data, source=source)
        
        # Agregar al historial
        self._add_to_history(event)
        
        # Emitir señal Qt
        self.event_emitted.emit(event_name, data)
        
        # Notificar suscriptores síncronos
        self._notify_sync_subscribers(event)
        
        # Notificar suscriptores asíncronos
        if self._async_subscribers[event_name]:
            asyncio.create_task(self._notify_async_subscribers(event))
        
        logger.debug(f"Evento '{event_name}' emitido desde {source or 'desconocido'}")
    
    def _notify_sync_subscribers(self, event: Event):
        """Notifica a los suscriptores síncronos."""
        for callback in self._subscribers[event.name]:
            try:
                if event.data is not None:
                    callback(event.data)
                else:
                    callback()
            except Exception as e:
                logger.error(f"Error en callback síncrono para '{event.name}': {e}")
    
    async def _notify_async_subscribers(self, event: Event):
        """Notifica a los suscriptores asíncronos."""
        tasks = []
        
        for callback in self._async_subscribers[event.name]:
            try:
                if event.data is not None:
                    task = callback(event.data)
                else:
                    task = callback()
                
                if asyncio.iscoroutine(task):
                    tasks.append(task)
            except Exception as e:
                logger.error(f"Error creando tarea para callback de '{event.name}': {e}")
        
        if tasks:
            try:
                await asyncio.gather(*tasks, return_exceptions=True)
            except Exception as e:
                logger.error(f"Error ejecutando callbacks asíncronos para '{event.name}': {e}")
    
    def _add_to_history(self, event: Event):
        """Agrega un evento al historial."""
        self._event_history.append(event)
        
        # Mantener historial limitado
        if len(self._event_history) > self._max_history:
            self._event_history = self._event_history[-self._max_history:]
    
    def get_event_history(self, event_name: Optional[str] = None, limit: Optional[int] = None) -> List[Event]:
        """
        Obtiene el historial de eventos.
        
        Args:
            event_name: Filtrar por nombre de evento específico
            limit: Limitar número de eventos devueltos
            
        Returns:
            Lista de eventos del historial
        """
        events = self._event_history
        
        if event_name:
            events = [e for e in events if e.name == event_name]
        
        if limit:
            events = events[-limit:]
        
        return events
    
    def get_subscribers_count(self, event_name: str) -> Dict[str, int]:
        """
        Obtiene el número de suscriptores para un evento.
        
        Args:
            event_name: Nombre del evento
            
        Returns:
            Diccionario con conteos de suscriptores síncronos y asíncronos
        """
        return {
            'sync': len(self._subscribers[event_name]),
            'async': len(self._async_subscribers[event_name])
        }
    
    def clear_subscribers(self, event_name: Optional[str] = None):
        """
        Limpia suscriptores de un evento específico o todos.
        
        Args:
            event_name: Nombre del evento específico, None para todos
        """
        if event_name:
            self._subscribers[event_name].clear()
            self._async_subscribers[event_name].clear()
            logger.debug(f"Suscriptores limpiados para '{event_name}'")
        else:
            self._subscribers.clear()
            self._async_subscribers.clear()
            logger.debug("Todos los suscriptores limpiados")
    
    def clear_history(self):
        """Limpia el historial de eventos."""
        self._event_history.clear()
        logger.debug("Historial de eventos limpiado")
    
    def pause(self):
        """Pausa la emisión de eventos."""
        self._is_active = False
        logger.debug("EventManager pausado")
    
    def resume(self):
        """Reanuda la emisión de eventos."""
        self._is_active = True
        logger.debug("EventManager reanudado")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del gestor de eventos.
        
        Returns:
            Diccionario con estadísticas
        """
        total_subscribers = sum(len(subs) for subs in self._subscribers.values())
        total_async_subscribers = sum(len(subs) for subs in self._async_subscribers.values())
        
        return {
            'is_active': self._is_active,
            'total_events_in_history': len(self._event_history),
            'total_sync_subscribers': total_subscribers,
            'total_async_subscribers': total_async_subscribers,
            'unique_events': len(set(self._subscribers.keys()) | set(self._async_subscribers.keys())),
            'events_by_name': {
                name: self.get_subscribers_count(name) 
                for name in set(self._subscribers.keys()) | set(self._async_subscribers.keys())
            }
        }
    
    def __del__(self):
        """Limpia recursos al destruir el objeto."""
        self.clear_subscribers()
        self.clear_history()