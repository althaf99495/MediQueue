document.addEventListener('DOMContentLoaded', function () {
    const container = document.getElementById('canvas-container');
    if (!container) return;

    // Scene setup
    const scene = new THREE.Scene();

    // Camera setup
    const camera = new THREE.PerspectiveCamera(75, container.clientWidth / container.clientHeight, 0.1, 1000);
    camera.position.z = 20;

    // Renderer setup
    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(renderer.domElement);

    // Particles setup
    const particlesGeometry = new THREE.BufferGeometry();
    const particlesCount = 100; // Number of particles
    const posArray = new Float32Array(particlesCount * 3);

    // Initial positions
    for (let i = 0; i < particlesCount * 3; i++) {
        posArray[i] = (Math.random() - 0.5) * 40; // Spread particles
    }

    particlesGeometry.setAttribute('position', new THREE.BufferAttribute(posArray, 3));

    // Material for particles
    const particlesMaterial = new THREE.PointsMaterial({
        size: 0.2,
        color: 0x0284C7, // Primary Blue
        transparent: true,
        opacity: 0.6,
    });

    // Mesh
    const particlesMesh = new THREE.Points(particlesGeometry, particlesMaterial);
    scene.add(particlesMesh);

    // Lines connecting particles
    const linesMaterial = new THREE.LineBasicMaterial({
        color: 0xffffff,
        transparent: true,
        opacity: 0.15
    });

    // Mouse interaction
    let mouseX = 0;
    let mouseY = 0;
    let targetX = 0;
    let targetY = 0;

    const windowHalfX = container.clientWidth / 2;
    const windowHalfY = container.clientHeight / 2;

    document.addEventListener('mousemove', (event) => {
        mouseX = (event.clientX - windowHalfX);
        mouseY = (event.clientY - windowHalfY);
    });

    // Animation Loop
    const clock = new THREE.Clock();

    function animate() {
        requestAnimationFrame(animate);

        targetX = mouseX * 0.001;
        targetY = mouseY * 0.001;

        const elapsedTime = clock.getElapsedTime();

        // Gentle rotation
        particlesMesh.rotation.y += 0.001;
        particlesMesh.rotation.x += 0.0005;

        // Mouse interaction easing
        particlesMesh.rotation.y += 0.05 * (targetX - particlesMesh.rotation.y);
        particlesMesh.rotation.x += 0.05 * (targetY - particlesMesh.rotation.x);

        // Wave movement for particles
        const positions = particlesMesh.geometry.attributes.position.array;
        for (let i = 0; i < particlesCount; i++) {
            const i3 = i * 3;
            // Add subtle wave motion
            positions[i3 + 1] += Math.sin(elapsedTime + positions[i3]) * 0.002;
        }
        particlesMesh.geometry.attributes.position.needsUpdate = true;

        // Dynamic Lines
        // Note: Recreating geometry every frame can be expensive, but for <100 particles it's fine for this demo.
        // For better performance, we would update an existing line geometry.
        // Here we'll use a simpler approach: just render the points. 
        // If we want lines, we need to calculate distances.

        // Let's add a separate object for lines to keep it clean or just stick to particles for "minimal" look.
        // The user asked for "minimal 3d animation". Floating particles are very minimal.
        // Let's add the lines for that "network" feel which is popular.

        // Cleanup old lines if we were doing dynamic lines... but for simplicity and performance, 
        // let's stick to just the floating particles with the nice movement. 
        // It looks like "smart dust" or "data points".

        renderer.render(scene, camera);
    }

    animate();

    // Handle Resize
    window.addEventListener('resize', () => {
        camera.aspect = container.clientWidth / container.clientHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(container.clientWidth, container.clientHeight);
    });
});
