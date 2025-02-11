import * as blazeface from '@tensorflow-models/blazeface';
import * as tf from '@tensorflow/tfjs';
import * as faceapi from 'face-api.js';
import React, { useEffect, useRef, useState } from 'react';

const FaceDetection = ({ onFaceDetected, OnFaceRecognized, stream }) => {
    const videoRef = useRef(null);
    const modelRef = useRef(null);
    const detectionRef = useRef(null);
    const [isModelLoaded, setIsModelLoaded] = useState(false);
    const [knownDescriptors, setKnownDescriptors] = useState([]);

    useEffect(() => {
        const initializeModel = async () => {
            try {
                console.log('Initializing TensorFlow...');
                await tf.ready();
                await tf.setBackend('cpu');
                console.log('TensorFlow initialized with backend:', tf.getBackend());
                console.log('Loading BlazeFace model...');
                modelRef.current = await blazeface.load({
                    maxFaces: 1,
                    inputWidth: 128,
                    inputHeight: 128,
                    iouThreshold: 0.3,
                    scoreThreshold: 0.75
                });

                console.log('Loading face-api.js models...');
                await faceapi.nets.tinyFaceDetector.loadFromUri('/models');
                await faceapi.nets.faceLandmark68Net.loadFromUri('/models');
                await faceapi.nets.faceRecognitionNet.loadFromUri('/models');
                console.log('face-api.js models loaded successfully');

                setIsModelLoaded(true);
            } catch (error) {
                console.error('Error during initialization:', error);
            }
        };

        initializeModel();

        return () => {
            if (detectionRef.current) {
                clearInterval(detectionRef.current);
            }
        };
    }, []);

    useEffect(() => {
        if (!stream || !videoRef.current) return;

        const video = videoRef.current;
        video.srcObject = stream;

        video.onloadedmetadata = () => {
            video.play()
                .then(() => console.log('Video playback started'))
                .catch(error => console.error('Video playback error:', error));
        };

        return () => {
            video.srcObject = null;
        };
    }, [stream]);

    useEffect(() => {
        if (!isModelLoaded || !stream || !videoRef.current) {
            console.log('Detection prerequisites not met:', {
                modelLoaded: isModelLoaded,
                streamExists: !!stream,
                videoExists: !!videoRef.current
            });
            return;
        }

        console.log('Starting face detection...');

        const recognizeFace = async (faceImage) => {
            try {
                const detections = await faceapi.detectAllFaces(faceImage, new faceapi.TinyFaceDetectorOptions())
                    .withFaceLandmarks()
                    .withFaceDescriptors();
                if (detections.length > 0) {
                    const descriptor = detections[0].descriptor;
                    const bestMatch = findBestMatch(descriptor);
                    if (bestMatch) {
                        console.log('Face recognized:', bestMatch);
                        OnFaceRecognized(bestMatch);
                    } else {
                        console.log('New face detected:', detections[0]);
                        setKnownDescriptors([...knownDescriptors, descriptor]);
                        OnFaceRecognized(detections[0]);
                    }
                }
            } catch (error) {
                console.error('Recognition error:', error);
            }
        };

        const findBestMatch = (descriptor) => {
            if (knownDescriptors.length === 0) return null;
            const labeledDescriptors = new faceapi.LabeledFaceDescriptors(
                'known',
                knownDescriptors.map(d => new Float32Array(d))
            );
            const faceMatcher = new faceapi.FaceMatcher(labeledDescriptors);
            const bestMatch = faceMatcher.findBestMatch(descriptor);
            return bestMatch.label === 'unknown' ? null : bestMatch;
        };

        const detectFace = async () => {
            if (!videoRef.current || videoRef.current.readyState !== 4) return;

            try {
                const video = videoRef.current;

                if (video.paused || video.ended) return;

                const predictions = await modelRef.current.estimateFaces(video, false);

                if (predictions && predictions.length > 0) {
                    console.log('Face detected');
                    onFaceDetected();

                    const topLeft = predictions[0].topLeft.map(Math.round);
                    const bottomRight = predictions[0].bottomRight.map(Math.round);

                    console.log('topLeft:', topLeft);
                    console.log('bottomRight:', bottomRight);

                    const faceImage = tf.browser.fromPixels(video).slice(
                        [topLeft[1], topLeft[0], 0],
                        [bottomRight[1] - topLeft[1], bottomRight[0] - topLeft[0], 3]
                    );

                    console.log('faceImage shape:', faceImage.shape);

                    // Convert tf.Tensor to ImageData, then to a canvas element
                    const pixels = await faceImage.data();
                    const width = faceImage.shape[1], height = faceImage.shape[0];
                    const imageData = new ImageData(new Uint8ClampedArray(pixels), width, height);
                    const tempCanvas = document.createElement('canvas');
                    tempCanvas.width = width;
                    tempCanvas.height = height;
                    const ctx = tempCanvas.getContext('2d');
                    ctx.putImageData(imageData, 0, 0);
                    await recognizeFace(tempCanvas);
                    faceImage.dispose();
                }
            } catch (error) {
                console.error('Detection error:', error);
                if (error.message.includes('backend') || error.message.includes('tensor')) {
                    clearInterval(detectionRef.current);
                }
            }
        };

        detectionRef.current = setInterval(detectFace, 500);

        return () => {
            if (detectionRef.current) {
                clearInterval(detectionRef.current);
            }
        };
    }, [isModelLoaded, stream, onFaceDetected]);

    return (
        <div style={{ position: 'absolute', opacity: 0, pointerEvents: 'none' }}>
            <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                width="640"
                height="480"
            />
        </div>
    );
};

export default FaceDetection;