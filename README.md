# ViSHARA: Simulación Virtual de $\text{SHARA}^3$ mediante técnicas WoZ

Sistema que permite la simulación y evaluación remota del robot asistencial social $\text{SHARA}^3$ mediante un enfoque semi-automático basado en la metodología Wizard of Oz (WoZ). Esta infraestructura facilita la evaluación y refinamiento de interacciones humano-robot sin necesidad de desplegar equipos físicos.

![webGeneral](https://github.com/user-attachments/assets/d7968e9e-ac2a-4df3-aac1-479300e9e399)

## 🤖 Descripción General

El sistema implementa una arquitectura distribuida compuesta por tres componentes principales:

- **La Tierra de Oz**: Aplicación web que proporciona una simulación 3D interactiva del robot $\text{SHARA}^3$.
- **El Camino de Baldosas Amarillas**: Servidor central que gestiona las comunicaciones y procesa las interacciones.
- **La Ciudad Esmeralda**: Interfaz de control WoZ para operadores.

## 🚀 Características Principales

- Simulación 3D realista del robot $\text{SHARA}^3$ con animaciones orientativas.
- Sistema de activación "wakeface" mediante detección facial.
- Comunicación bidireccional por voz y texto.
- Análisis emocional en tiempo real.
- Modo híbrido de operación (automático/semi-automático).
- Streaming de vídeo en tiempo real.
- Integración con servicios cognitivos en la nube (Google Cloud STT, TTS, Translate; IBM Watson Assistant, NLU).

## 💻 Tecnologías

### Frontend Web (La Tierra de Oz)
- React + Three.js para simulación 3D.
- Face-api.js para detección facial.
- React-mic para captura de audio.
- Socket.IO para comunicación en tiempo real.

### Servidor (El Camino de Baldosas Amarillas)
- Node.js y Express.
- Socket.IO y WebSocket.
- IBM Watson (Assistant y NLU).
- Google Cloud Services (STT, TTS, Translation).

### Aplicación de Control (La Ciudad Esmeralda)
- Python con PyQt6.
- OpenCV para procesamiento de video.
- WebSocket para streaming.
- QAsync para operaciones asíncronas.

## ⚙️ Instalación

### Prerequisitos
- Node.js v14 o superior.
- Python 3.8 o superior.
- Navegador moderno con soporte WebGL 2.0.
- Cámara web y micrófono.

### Configuración del Servidor

1. Clonar el repositorio
```bash
git clone https://github.com/GuillermoCuberoCharco/TFG-ViSHARA
cd TFG-ViSHARA/src
```

2. Instalar dependencias
```bash
cd server
npm install
```

3. Configurar variables de entorno
```bash
cp .env.example .env
# Editar .env con tus credenciales de IBM Watson y Google Cloud
```

### Configuración del Cliente Web

```bash
cd web
yarn install
```

### Configuración de la Aplicación WoZ

```bash
cd wizard
pip install -r requirements.txt
```

## 🖥️ Uso

1. Iniciar el servidor
```bash
cd server/src
node YellowBrickRoad.cjs
```

2. Iniciar el cliente web
```bash
cd web/src
yarn dev
```

3. Iniciar la aplicación WoZ
```bash
cd wizard/src
python EmeraldCity.py
```

## 📊 Arquitectura del Sistema

```
[Cliente Web] <--WebSocket/Socket.IO--> [Servidor Central] <--WebSocket/Socket.IO--> [App WoZ]
```

## 👥 Contribuir

Las contribuciones son bienvenidas. Por favor:

1. Haz Fork del repositorio.
2. Crea una rama para tu característica (`git checkout -b feature/nueva-caracteristica`).
3. Realiza tus cambios y haz commit (`git commit -m 'Añade nueva característica'`).
4. Push a la rama (`git push origin feature/nueva-caracteristica`).
5. Abre un Pull Request.

## 📝 Licencia

[MIT](https://choosealicense.com/licenses/mit/)

## ✉️ Contacto

Guillermo Cubero Charco
Guillermo.Cubero@uclm.es

Este proyecto es parte de un Trabajo Fin de Grado realizado en la Escuela Superior de Informática (UCLM).

## 🙏 Agradecimientos

- Ramón Hervás Lucas (Tutor).
- Laura Villa Fernández-Arroyo (Co-tutora).
- Grupo de investigación MAmI Research Lab.
- Panel internacional de expertos en HRI por su evaluación y retroalimentación.