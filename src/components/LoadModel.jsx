import { useAnimations, useGLTF } from "@react-three/drei";
import React, { useRef } from "react";
import { useCharacterAnimations } from "../contexts/CharacterAnimations";

const GlbViewer = () => {
  const group = useRef();
  const { nodes, materials, animations } = useGLTF('./models/Shara_test.glb');
  const { actions } = useAnimations(animations, group);
  const { animationIndex, setAnimations } = useCharacterAnimations();

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

useGLTF.preload('./Shara_test.glb');

export default GlbViewer;


