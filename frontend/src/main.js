import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import './style.css';

// 1. SCENE SETUP
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x87ceeb); // Sky blue background

// 2. CAMERA SETUP
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
camera.position.set(20, 15, 30); 

// 3. RENDERER SETUP
const renderer = new THREE.WebGLRenderer({ antialias: true }); 
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.shadowMap.enabled = true; 
document.querySelector('#app').appendChild(renderer.domElement);

// 4. LIGHTING
const ambientLight = new THREE.AmbientLight(0xffffff, 0.6); 
scene.add(ambientLight);

const dirLight = new THREE.DirectionalLight(0xffffff, 0.8); 
dirLight.position.set(50, 50, 30);
dirLight.castShadow = true;
scene.add(dirLight);

// 5. SITE INFRASTRUCTURE: GROUND
const groundGeo = new THREE.PlaneGeometry(100, 100);
const groundMat = new THREE.MeshStandardMaterial({ color: 0x4f7942 }); 
const ground = new THREE.Mesh(groundGeo, groundMat);
ground.rotation.x = -Math.PI / 2; 
ground.receiveShadow = true;
scene.add(ground);

// 6. SITE INFRASTRUCTURE: TELECOM TOWER 
const towerGroup = new THREE.Group();

const mastGeo = new THREE.CylinderGeometry(0.5, 1, 20, 8); 
const mastMat = new THREE.MeshStandardMaterial({ color: 0xcccccc, metalness: 0.8, roughness: 0.2 });
const mast = new THREE.Mesh(mastGeo, mastMat);
mast.position.y = 10; 
mast.castShadow = true;
towerGroup.add(mast);

const antennaGeo = new THREE.BoxGeometry(0.3, 2, 0.1);
const antennaMat = new THREE.MeshStandardMaterial({ color: 0xffffff });
for (let i = 0; i < 3; i++) {
    const antenna = new THREE.Mesh(antennaGeo, antennaMat);
    const angle = (i * Math.PI * 2) / 3; 
    antenna.position.set(Math.sin(angle) * 1.5, 18, Math.cos(angle) * 1.5);
    antenna.rotation.y = angle; 
    antenna.castShadow = true;
    towerGroup.add(antenna);
}
scene.add(towerGroup);

// 7. SITE INFRASTRUCTURE: EQUIPMENT SHELTER
const shelterGeo = new THREE.BoxGeometry(4, 3, 5);
const shelterMat = new THREE.MeshStandardMaterial({ color: 0xdddddd });
const shelter = new THREE.Mesh(shelterGeo, shelterMat);
shelter.position.set(8, 1.5, 0); 
shelter.castShadow = true;
shelter.receiveShadow = true;
scene.add(shelter);

// 8. INTERACTIVE CONTROLS
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true; 
controls.dampingFactor = 0.05;
controls.maxPolarAngle = (Math.PI / 2) - 0.05; 

// 9. ANIMATION LOOP
function animate() {
    requestAnimationFrame(animate);
    controls.update(); 
    renderer.render(scene, camera);
}
animate();

// 10. WINDOW RESIZE HANDLER
window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});