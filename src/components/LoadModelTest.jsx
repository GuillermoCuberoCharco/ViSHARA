// GltfViewer.js
import { useAnimations, useGLTF } from "@react-three/drei";
import React, { useRef } from "react";

const GltfViewer = () => {
  const group = useRef();
  const { nodes, materials, animations } = useGLTF('./models/SHARA3.gltf');
  const { actions } = useAnimations(animations, group);

  React.useEffect(() => {
    // Reproduce la primera animación (ajusta según sea necesario)
    if (actions && Object.keys(actions).length > 0) {
      actions[Object.keys(actions)[0]].play();
    }
  }, [actions]);

  return (
    <group ref={group} dispose={null}>
      <primitive object={nodes.Scene} />
    </group>
  );
};

useGLTF.preload('./SHARA3.gltf');

export default GltfViewer;


