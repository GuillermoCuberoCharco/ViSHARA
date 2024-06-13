import { useAnimations, useGLTF } from "@react-three/drei";
import React, { useEffect, useRef } from "react";
import { useCharacterAnimations } from "../contexts/CharacterAnimations";

const Shara = (props) => {
  const group = useRef();
  const { nodes, materials, animations } = useGLTF("./models/SHARA3.gltf");
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
          <primitive object={nodes.Armature} />
          <skinnedMesh
            castShadow
            name="cuerpo_brazo_i"
            geometry={nodes.cuerpo_brazo_i.geometry}
            material={materials.Body_parts}
            skeleton={nodes.cuerpo_brazo_i.skeleton}
          />
        </group>
        <group name="cuerpo_base">
          <mesh
            castShadow
            geometry={nodes.cuerpo_base.geometry}
            material={materials.Face_Mask}
          />
        </group>
        <group name="Cylinder">
          <mesh
            castShadow
            geometry={nodes.Cylinder.geometry}
            material={materials.Body}
          />
        </group>
        <group name="Empty">
          <primitive object={nodes.Empty} />
        </group>
        <group name="Empty.001">
          <primitive object={nodes.Empty_001} />
        </group>
        <group name="Empty.002">
          <primitive object={nodes.Empty_002} />
        </group>
        <group name="Eyes">
          <primitive object={nodes.Eyes} />
        </group>
        <group name="Head">
          <skinnedMesh
            castShadow
            geometry={nodes.Head.geometry}
            material={materials.Screen}
            skeleton={nodes.Head.skeleton}
          />
          <skinnedMesh
            castShadow
            geometry={nodes.Head.geometry}
            material={materials.Body}
            skeleton={nodes.Head.skeleton}
          />
          <skinnedMesh
            castShadow
            geometry={nodes.Head.geometry}
            material={materials.Face_Mask}
            skeleton={nodes.Head.skeleton}
          />
        </group>
        <group name="SHARA3.035">
          <mesh
            castShadow
            geometry={nodes.SHARA3_035.geometry}
            material={materials.Body_parts}
          />
        </group>
        <group name="SHARA3.115">
          <mesh
            castShadow
            geometry={nodes.SHARA3_115.geometry}
            material={materials.Body_parts}
          />
        </group>
      </group>
    </group>
  );
};

export default Shara;

useGLTF.preload("./models/SHARA3.gltf");
