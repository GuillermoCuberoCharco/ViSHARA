# ViSHARA: Virtual Simulation of $\text{SHARA}^3$ using WoZ techniques

A system that enables remote simulation and evaluation of the $\text{SHARA}^3$ social assistive robot through a semi-automatic approach based on the Wizard of Oz (WoZ) methodology. This infrastructure facilitates human-robot interaction evaluation and refinement without the need to deploy physical equipment or proffesionals teams.

![webGeneral](https://github.com/user-attachments/assets/d7968e9e-ac2a-4df3-aac1-479300e9e399)

## 🤖 General Description

The system implements a distributed architecture composed of three main components:

- **The Land of Oz**: Web application that provides an interactive 3D simulation of the $\text{SHARA}^3$ robot.
- **The Yellow Brick Road**: Central server that manages communications and processes interactions.
- **The Emerald City**: WoZ control interface for operators.

## 🚀 Main Features

- Realistic 3D simulation of the $\text{SHARA}^3$ robot with orientation animations.
- "Wakeface" activation system through facial detection.
- Bidirectional voice and text communication.
- Real-time emotional analysis.
- Hybrid operation mode (automatic/semi-automatic).
- Real-time video streaming.
- Integration with cloud cognitive services (Google Cloud STT, TTS, Translate; IBM Watson Assistant, NLU).

## 💻 Technologies

### Web Frontend (The Land of Oz)
- React + Three.js for 3D simulation.
- Face-api.js for facial detection.
- React-mic for audio capture.
- Socket.IO for real-time communication.

### Server (The Yellow Brick Road)
- Node.js and Express.
- Socket.IO and WebSocket.
- IBM Watson (Assistant and NLU).
- Google Cloud Services (STT, TTS, Translation).

### Control Application (The Emerald City)
- Python with PyQt6.
- OpenCV for video processing.
- WebSocket for streaming.
- QAsync for asynchronous operations.

## ⚙️ Local Installation

### Prerequisites
- Node.js v14 or higher.
- Python 3.8 or higher.
- Modern browser with WebGL 2.0 support.
- Webcam and microphone.

### Server Setup

1. Clone the repository
```bash
git clone https://github.com/GuillermoCuberoCharco/ViSHARA
cd ViSHARA/src
```

2. Install dependencies
```bash
cd server
npm install
```

3. Configure environment variables
```bash
cp .env.example .env
# Edit .env with your IBM Watson and Google Cloud credentials
```

### Web Client Setup

```bash
cd web
yarn install
```

### WoZ Application Setup

```bash
cd wizard
pip install -r requirements.txt
```

## 🖥️ Usage

1. Start the server
```bash
cd server/src
node YellowBrickRoad.cjs
```

2. Start the web client
```bash
cd web/src
yarn dev
```

3. Start the WoZ application
```bash
cd wizard/src
python EmeraldCity.py
```

## 📊 System Architecture

```
[Web Client] <--WebSocket/Socket.IO--> [Central Server] <--WebSocket/Socket.IO--> [WoZ App]
```
Here's how to install the system for a local deployment. However, to use it as proposed, both the web application and server should be deployed to enable remote evaluations. Currently, both deployments have been made on Vercel and Render.

```https://vi-shara.vercel.app```

## 👥 Contributing

Contributions are welcome. Please:

1. Fork the repository.
2. Create a branch for your feature (`git checkout -b feature/new-feature`).
3. Make your changes and commit (`git commit -m 'Add new feature'`).
4. Push to the branch (`git push origin feature/new-feature`).
5. Open a Pull Request.

## 📝 License

[MIT](https://choosealicense.com/licenses/mit/)

## ✉️ Contact

Guillermo Cubero Charco
Guillermo.Cubero@uclm.es

This project is part of a Final Degree Project carried out at the ESI(UCLM) Ciudad Real, Spain.

## 🙏 Acknowledgments

- Ramón Hervás Lucas (Advisor).
- Laura Villa Fernández-Arroyo (Co-advisor).
- MAmI Research Lab research group.
- International panel of HRI experts for their evaluation and feedback.