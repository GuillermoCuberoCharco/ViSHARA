import { useAnimations, useGLTF } from "@react-three/drei";
import React, { useRef } from "react";

const GlbViewer = ({ animationIndex, setAnimations }) => {
  const group = useRef();
  const { nodes, materials, animations } = useGLTF('/models/SHARA3.gltf');
  const { actions } = useAnimations(animations, group);

  React.useEffect(() => {
    if (actions) {
      const animationNames = Object.keys(actions);
      console.log("Available animations:", animationNames);

      setAnimations(animationNames);

      if (animationNames.length > 0) {
        Object.values(actions).forEach((action) => action.stop());
        if (animationNames[animationIndex]) {
          actions[animationNames[animationIndex]].play();
        }
      }
    }
  }, [actions, animationIndex, setAnimations]);

  return (
    <group ref={group} dispose={null}>
      <primitive object={nodes.Scene} />
    </group>
  );
};

useGLTF.preload('./SHARA3.gltf');

export default GlbViewer;


