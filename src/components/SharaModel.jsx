import { useAnimations, useGLTF } from "@react-three/drei";
import React, { useEffect, useRef } from "react";
import { useCharacterAnimations } from "../contexts/CharacterAnimations";

const Shara = (props) => {
  const group = useRef();
  const { nodes, materials, animations } = useGLTF("./models/SHARA_Animations.glb");
  const { setAnimations, animationIndex } = useCharacterAnimations();
  const { actions, names } = useAnimations(animations, group);

  useEffect(() => {
    setAnimations(names);
    console.log("Nombres de animaciones", names);
  }, [names, setAnimations]);

  useEffect(() => {
    actions[names[animationIndex]].reset().fadeIn(0.5).play();
    return () => {
      actions[names[animationIndex]].fadeOut(0.5);
    };
  }, [animationIndex, actions, names]);

  return (
    <group ref={group} {...props} dispose={null}>
      <group name="Scene">
        <group name="Armature" rotation={[Math.PI / 2, 0, 0]} scale={0.01}>
          <primitive object={nodes.mixamorigHips} />
          <group name="SHARA_Model">
            <skinnedMesh
              castShadow
              name="Mesh001"
              geometry={nodes.Mesh001.geometry}
              material={materials.Material1}
              skeleton={nodes.Mesh001.skeleton}
            />
            <skinnedMesh
              castShadow
              name="Mesh002"
              geometry={nodes.Mesh002.geometry}
              material={materials.Material2}
              skeleton={nodes.Mesh002.skeleton}
            />
            <skinnedMesh
              castShadow
              name="Mesh003"
              geometry={nodes.Mesh003.geometry}
              material={materials.Material3}
              skeleton={nodes.Mesh003.skeleton}
            />
            <skinnedMesh
              castShadow
              name="Mesh004"
              geometry={nodes.Mesh004.geometry}
              material={materials.Material4}
              skeleton={nodes.Mesh004.skeleton}
            />
          </group>
        </group>
      </group>
    </group>
  );
};

export default Shara;

useGLTF.preload("./models/SHARA_Animations.glb");