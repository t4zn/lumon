// Lumon Pages - 3D Animation System
class LumonPageAnimations {
    constructor() {
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.floatingElements = [];
        this.init();
    }

    init() {
        this.create3DScene();
        this.addFallbackAnimations();
        this.animate();
        this.handleResize();
    }

    create3DScene() {
        try {
            // Scene setup
            this.scene = new THREE.Scene();
            
            // Camera setup
            this.camera = new THREE.PerspectiveCamera(
                75,
                window.innerWidth / window.innerHeight,
                0.1,
                1000
            );
            this.camera.position.z = 5;

            // Renderer setup
            this.renderer = new THREE.WebGLRenderer({
                alpha: true,
                antialias: true
            });
            this.renderer.setSize(window.innerWidth, window.innerHeight);
            this.renderer.setClearColor(0x000000, 0);
            
            // Add to container
            const container = document.querySelector('.floating-elements-3d');
            if (container) {
                container.appendChild(this.renderer.domElement);
            }

            this.create3DElements();
        } catch (error) {
            console.log('3D not available, using fallback animations');
            this.addFallbackAnimations();
        }
    }

    create3DElements() {
        // Create floating botanical elements
        for (let i = 0; i < 15; i++) {
            const elementType = Math.random();
            let geometry, material, mesh;

            if (elementType < 0.4) {
                // Leaf shapes
                geometry = new THREE.SphereGeometry(0.1, 6, 6);
                material = new THREE.MeshBasicMaterial({
                    color: new THREE.Color().setHSL(0.3, 0.8, 0.6),
                    transparent: true,
                    opacity: 0.6
                });
            } else if (elementType < 0.7) {
                // Small circles
                geometry = new THREE.CircleGeometry(0.05, 8);
                material = new THREE.MeshBasicMaterial({
                    color: new THREE.Color().setHSL(0.35, 0.9, 0.5),
                    transparent: true,
                    opacity: 0.4
                });
            } else {
                // Line segments
                const points = [
                    new THREE.Vector3(0, -0.2, 0),
                    new THREE.Vector3(0, 0.2, 0)
                ];
                geometry = new THREE.BufferGeometry().setFromPoints(points);
                material = new THREE.LineBasicMaterial({
                    color: new THREE.Color().setHSL(0.32, 0.7, 0.7),
                    transparent: true,
                    opacity: 0.5
                });
                mesh = new THREE.Line(geometry, material);
            }

            if (!mesh) {
                mesh = new THREE.Mesh(geometry, material);
            }

            // Random positioning
            mesh.position.set(
                (Math.random() - 0.5) * 10,
                (Math.random() - 0.5) * 8,
                (Math.random() - 0.5) * 6
            );

            // Add random rotation
            mesh.rotation.set(
                Math.random() * Math.PI,
                Math.random() * Math.PI,
                Math.random() * Math.PI
            );

            // Store animation properties
            mesh.userData = {
                initialPosition: mesh.position.clone(),
                floatSpeed: 0.5 + Math.random() * 1.5,
                rotationSpeed: 0.2 + Math.random() * 0.8,
                amplitude: 0.5 + Math.random() * 1.0
            };

            this.floatingElements.push(mesh);
            this.scene.add(mesh);
        }
    }

    animate() {
        if (!this.renderer || !this.scene || !this.camera) {
            requestAnimationFrame(() => this.animate());
            return;
        }

        const time = Date.now() * 0.001;

        // Animate floating elements
        this.floatingElements.forEach((element, index) => {
            const userData = element.userData;
            
            // Floating motion
            element.position.y = userData.initialPosition.y + 
                Math.sin(time * userData.floatSpeed + index) * userData.amplitude;
            
            element.position.x = userData.initialPosition.x + 
                Math.cos(time * userData.floatSpeed * 0.7 + index) * 0.5;

            // Rotation
            element.rotation.x += userData.rotationSpeed * 0.01;
            element.rotation.y += userData.rotationSpeed * 0.015;
            element.rotation.z += userData.rotationSpeed * 0.008;
        });

        // Camera subtle movement
        this.camera.position.x = Math.sin(time * 0.2) * 0.1;
        this.camera.position.y = Math.cos(time * 0.3) * 0.1;

        this.renderer.render(this.scene, this.camera);
        requestAnimationFrame(() => this.animate());
    }

    addFallbackAnimations() {
        // Create enhanced CSS-based floating elements
        const container = document.querySelector('.floating-elements-3d') || document.body;
        
        // Create leaves
        for (let i = 0; i < 8; i++) {
            const leaf = document.createElement('div');
            leaf.className = 'floating-leaf';
            leaf.style.left = Math.random() * 100 + '%';
            leaf.style.top = Math.random() * 100 + '%';
            leaf.style.animationDelay = Math.random() * 12 + 's';
            leaf.style.animationDuration = (10 + Math.random() * 8) + 's';
            container.appendChild(leaf);
        }

        // Create circles
        for (let i = 0; i < 6; i++) {
            const circle = document.createElement('div');
            circle.className = 'floating-circle';
            circle.style.width = (8 + Math.random() * 15) + 'px';
            circle.style.height = circle.style.width;
            circle.style.left = Math.random() * 100 + '%';
            circle.style.top = Math.random() * 100 + '%';
            circle.style.animationDelay = Math.random() * 15 + 's';
            circle.style.animationDuration = (12 + Math.random() * 10) + 's';
            container.appendChild(circle);
        }

        // Create lines
        for (let i = 0; i < 4; i++) {
            const line = document.createElement('div');
            line.className = 'floating-line';
            line.style.height = (30 + Math.random() * 40) + 'px';
            line.style.left = Math.random() * 100 + '%';
            line.style.top = Math.random() * 100 + '%';
            line.style.animationDelay = Math.random() * 10 + 's';
            line.style.animationDuration = (8 + Math.random() * 6) + 's';
            container.appendChild(line);
        }

        // Create floating particles
        for (let i = 0; i < 10; i++) {
            const particle = document.createElement('div');
            particle.className = 'floating-particle';
            particle.style.width = (3 + Math.random() * 6) + 'px';
            particle.style.height = particle.style.width;
            particle.style.left = Math.random() * 100 + '%';
            particle.style.animationDelay = Math.random() * 20 + 's';
            particle.style.animationDuration = (15 + Math.random() * 10) + 's';
            container.appendChild(particle);
        }
    }

    handleResize() {
        window.addEventListener('resize', () => {
            if (this.camera && this.renderer) {
                this.camera.aspect = window.innerWidth / window.innerHeight;
                this.camera.updateProjectionMatrix();
                this.renderer.setSize(window.innerWidth, window.innerHeight);
            }
        });
    }
}

// Initialize animations when page loads
document.addEventListener('DOMContentLoaded', () => {
    new LumonPageAnimations();
    
    // Add entrance animations to page elements
    const pageContainer = document.querySelector('.page-container');
    if (pageContainer) {
        pageContainer.style.opacity = '0';
        pageContainer.style.transform = 'scale(0.9)';
        
        setTimeout(() => {
            pageContainer.style.transition = 'all 0.6s cubic-bezier(0.4, 0.0, 0.2, 1)';
            pageContainer.style.opacity = '1';
            pageContainer.style.transform = 'scale(1)';
        }, 100);
    }
});
