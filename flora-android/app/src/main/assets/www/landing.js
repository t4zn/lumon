// Flora Landing Page - Advanced 3D Experience

class FloraLanding {
    constructor() {
        this.init3DScene();
        this.initAnimations();
        this.initInteractions();
        this.createParticleSystem();
    }

    init3DScene() {
        if (!window.THREE) {
            console.log('Three.js not available');
            return;
        }

        try {
            const canvas = document.getElementById('landing-canvas');
            if (!canvas) return;

            // Scene setup
            this.scene = new THREE.Scene();
            this.camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
            this.renderer = new THREE.WebGLRenderer({ 
                canvas: canvas, 
                alpha: true,
                antialias: true 
            });
            
            this.renderer.setSize(window.innerWidth, window.innerHeight);
            this.renderer.setClearColor(0x000000, 0);

            // Create 3D botanical elements
            this.create3DBotanicalGarden();
            
            // Camera positioning
            this.camera.position.z = 8;
            this.camera.position.y = 2;
            this.camera.lookAt(0, 0, 0);

            // Start animation loop
            this.animate3D();

            // Handle window resize
            window.addEventListener('resize', () => this.onWindowResize());

        } catch (error) {
            console.log('3D scene initialization failed:', error);
        }
    }

    create3DBotanicalGarden() {
        this.botanicalElements = [];

        // Create various botanical 3D elements
        const elements = [
            { type: 'leaf', count: 30, size: 0.5, color: 0x10b981 },
            { type: 'flower', count: 20, size: 0.3, color: 0x34d399 },
            { type: 'stem', count: 25, size: 0.8, color: 0x059669 },
            { type: 'pollen', count: 40, size: 0.1, color: 0x50c878 },
            { type: 'branch', count: 15, size: 1.2, color: 0x064e3b }
        ];

        elements.forEach(element => {
            for (let i = 0; i < element.count; i++) {
                const mesh = this.createBotanicalElement(element.type, element.size, element.color);
                if (mesh) {
                    this.positionElement(mesh);
                    this.botanicalElements.push(mesh);
                    this.scene.add(mesh);
                }
            }
        });
    }

    createBotanicalElement(type, size, color) {
        let geometry, material, mesh;

        const baseMaterial = new THREE.MeshBasicMaterial({ 
            color: color,
            transparent: true,
            opacity: 0.7
        });

        switch (type) {
            case 'leaf':
                geometry = new THREE.PlaneGeometry(size, size * 1.5);
                mesh = new THREE.Mesh(geometry, baseMaterial);
                break;
                
            case 'flower':
                geometry = new THREE.ConeGeometry(size, size * 2, 8);
                material = new THREE.MeshBasicMaterial({ 
                    color: color,
                    transparent: true,
                    opacity: 0.8
                });
                mesh = new THREE.Mesh(geometry, material);
                break;
                
            case 'stem':
                geometry = new THREE.CylinderGeometry(size * 0.05, size * 0.05, size);
                mesh = new THREE.Mesh(geometry, baseMaterial);
                break;
                
            case 'pollen':
                geometry = new THREE.SphereGeometry(size, 12, 8);
                material = new THREE.MeshBasicMaterial({ 
                    color: color,
                    transparent: true,
                    opacity: 0.9
                });
                mesh = new THREE.Mesh(geometry, material);
                break;
                
            case 'branch':
                const group = new THREE.Group();
                
                // Main branch
                const branchGeom = new THREE.CylinderGeometry(size * 0.03, size * 0.03, size);
                const branchMesh = new THREE.Mesh(branchGeom, baseMaterial);
                group.add(branchMesh);
                
                // Sub-branches
                for (let i = 0; i < 3; i++) {
                    const subBranchGeom = new THREE.CylinderGeometry(size * 0.02, size * 0.02, size * 0.6);
                    const subBranchMesh = new THREE.Mesh(subBranchGeom, baseMaterial);
                    subBranchMesh.position.y = (i - 1) * size * 0.3;
                    subBranchMesh.rotation.z = (Math.random() - 0.5) * Math.PI * 0.5;
                    group.add(subBranchMesh);
                }
                
                mesh = group;
                break;
        }

        if (mesh) {
            // Add animation properties
            mesh.userData = {
                type: type,
                originalPosition: new THREE.Vector3(),
                rotationSpeed: {
                    x: (Math.random() - 0.5) * 0.02,
                    y: (Math.random() - 0.5) * 0.02,
                    z: (Math.random() - 0.5) * 0.02
                },
                floatSpeed: 0.001 + Math.random() * 0.002,
                floatAmplitude: 0.5 + Math.random() * 1.5,
                timeOffset: Math.random() * Math.PI * 2,
                driftSpeed: (Math.random() - 0.5) * 0.002
            };
        }

        return mesh;
    }

    positionElement(mesh) {
        // Position elements in a spherical distribution around the scene
        const radius = 15 + Math.random() * 10;
        const theta = Math.random() * Math.PI * 2;
        const phi = Math.random() * Math.PI;
        
        mesh.position.x = radius * Math.sin(phi) * Math.cos(theta);
        mesh.position.y = radius * Math.sin(phi) * Math.sin(theta);
        mesh.position.z = radius * Math.cos(phi);
        
        mesh.userData.originalPosition.copy(mesh.position);
        
        // Random rotation
        mesh.rotation.x = Math.random() * Math.PI * 2;
        mesh.rotation.y = Math.random() * Math.PI * 2;
        mesh.rotation.z = Math.random() * Math.PI * 2;
    }

    animate3D() {
        if (!this.renderer || !this.scene || !this.camera) return;

        requestAnimationFrame(() => this.animate3D());

        const time = Date.now() * 0.001;

        // Animate botanical elements
        if (this.botanicalElements) {
            this.botanicalElements.forEach((element, index) => {
                const userData = element.userData;
                
                // Rotation
                element.rotation.x += userData.rotationSpeed.x;
                element.rotation.y += userData.rotationSpeed.y;
                element.rotation.z += userData.rotationSpeed.z;
                
                // Floating motion
                const floatX = Math.sin(time * userData.floatSpeed + userData.timeOffset) * userData.floatAmplitude * 0.1;
                const floatY = Math.cos(time * userData.floatSpeed * 0.7 + userData.timeOffset) * userData.floatAmplitude * 0.1;
                const floatZ = Math.sin(time * userData.floatSpeed * 0.5 + userData.timeOffset) * userData.floatAmplitude * 0.05;
                
                element.position.x = userData.originalPosition.x + floatX;
                element.position.y = userData.originalPosition.y + floatY;
                element.position.z = userData.originalPosition.z + floatZ;
                
                // Gentle drift
                element.position.x += userData.driftSpeed;
                
                // Reset elements that drift too far
                if (element.position.x > 25) element.position.x = -25;
                if (element.position.x < -25) element.position.x = 25;
                
                // Scaling animation for organic feel
                const scaleVariation = 1 + Math.sin(time * 0.5 + index * 0.1) * 0.15;
                element.scale.setScalar(scaleVariation);
            });
        }

        // Dynamic camera movement
        this.camera.position.x = Math.sin(time * 0.1) * 2;
        this.camera.position.y = 2 + Math.cos(time * 0.08) * 1;
        this.camera.position.z = 8 + Math.sin(time * 0.05) * 2;
        this.camera.lookAt(0, 0, 0);

        this.renderer.render(this.scene, this.camera);
    }

    onWindowResize() {
        if (!this.camera || !this.renderer) return;
        
        this.camera.aspect = window.innerWidth / window.innerHeight;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(window.innerWidth, window.innerHeight);
    }

    initAnimations() {
        if (!window.gsap) return;

        // Hero entrance animation with persistent elements
        const tl = gsap.timeline();
        
        // Force visibility and prevent disappearing
        gsap.set('.floating-elements', { 
            opacity: 1, 
            scale: 1, 
            visibility: 'visible',
            display: 'block'
        });
        gsap.set('.float-leaf, .float-pollen, .float-stem', { 
            opacity: 1, 
            visibility: 'visible',
            display: 'block'
        });
        
        // Ensure start button remains visible and clickable
        gsap.set('.start-btn', {
            opacity: 1,
            visibility: 'visible',
            display: 'inline-flex',
            pointerEvents: 'auto',
            zIndex: 1000
        });
        
        tl.from('.logo-container', {
            duration: 1.5,
            scale: 0,
            rotation: 360,
            ease: 'back.out(1.7)'
        })
        .from('.title-word', {
            duration: 1,
            y: 50,
            opacity: 0,
            ease: 'power3.out'
        }, '-=0.5')
        .from('.title-subtitle', {
            duration: 0.8,
            y: 30,
            opacity: 0,
            ease: 'power2.out'
        }, '-=0.3')
        .from('.hero-description', {
            duration: 0.8,
            y: 30,
            opacity: 0,
            ease: 'power2.out'
        }, '-=0.2')
        .from('.feature-highlights .feature-item', {
            duration: 0.6,
            y: 30,
            opacity: 0,
            stagger: 0.2,
            ease: 'power2.out'
        }, '-=0.2')
        .from('.start-btn', {
            duration: 0.8,
            scale: 0,
            ease: 'back.out(1.7)',
            onComplete: function() {
                // Ensure button stays visible after animation
                gsap.set('.start-btn', {
                    opacity: 1,
                    visibility: 'visible',
                    display: 'inline-flex',
                    pointerEvents: 'auto',
                    zIndex: 1000
                });
            }
        }, '-=0.2')
        .from('.features-section .feature-card', {
            duration: 0.6,
            y: 50,
            opacity: 0,
            stagger: 0.1,
            ease: 'power2.out'
        }, '-=0.3');

        // Enhanced persistent animations that maintain visibility
        gsap.to('.float-leaf', {
            y: '+=20',
            rotation: '+=10',
            duration: 8,
            ease: 'power2.inOut',
            stagger: 1,
            repeat: -1,
            yoyo: true,
            force3D: true,
            onComplete: function() {
                gsap.set(this.targets(), { opacity: 1, visibility: 'visible' });
            }
        });

        gsap.to('.float-pollen', {
            y: '+=15',
            x: '+=10',
            scale: 1.2,
            duration: 6,
            ease: 'power2.inOut',
            stagger: 0.8,
            repeat: -1,
            yoyo: true,
            force3D: true,
            onComplete: function() {
                gsap.set(this.targets(), { opacity: 1, visibility: 'visible' });
            }
        });

        gsap.to('.float-stem', {
            rotation: '+=8',
            y: '+=12',
            duration: 10,
            ease: 'power2.inOut',
            stagger: 1.2,
            repeat: -1,
            yoyo: true,
            force3D: true,
            onComplete: function() {
                gsap.set(this.targets(), { opacity: 1, visibility: 'visible' });
            }
        });
    }

    initInteractions() {
        const startBtn = document.getElementById('start-btn');
        
        if (startBtn) {
            // Ensure button is always visible and clickable
            gsap.set(startBtn, {
                opacity: 1,
                visibility: 'visible',
                display: 'inline-flex',
                pointerEvents: 'auto',
                zIndex: 1000
            });
            
            startBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('Start button clicked!');
                this.transitionToApp();
            });
            
            // Add hover effects that maintain visibility
            startBtn.addEventListener('mouseenter', () => {
                gsap.to(startBtn, {
                    scale: 1.05,
                    duration: 0.3,
                    ease: 'power2.out'
                });
            });
            
            startBtn.addEventListener('mouseleave', () => {
                gsap.to(startBtn, {
                    scale: 1,
                    duration: 0.3,
                    ease: 'power2.out'
                });
            });
        }

        // Parallax effect on mouse move
        document.addEventListener('mousemove', (e) => {
            const x = (e.clientX / window.innerWidth) * 2 - 1;
            const y = -(e.clientY / window.innerHeight) * 2 + 1;
            
            gsap.to('.floating-elements', {
                x: x * 20,
                y: y * 20,
                duration: 2,
                ease: 'power2.out'
            });
            
            gsap.to('.logo-3d', {
                rotationY: x * 10,
                rotationX: y * 10,
                duration: 1,
                ease: 'power2.out'
            });
        });
    }

    createParticleSystem() {
        const particleContainer = document.getElementById('particle-system');
        if (!particleContainer) return;

        // Create persistent floating particles
        for (let i = 0; i < 30; i++) {
            const particle = document.createElement('div');
            particle.className = 'floating-particle';
            particle.style.cssText = `
                position: absolute;
                width: ${3 + Math.random() * 6}px;
                height: ${3 + Math.random() * 6}px;
                background: radial-gradient(circle, rgba(16, 185, 129, 0.9), rgba(52, 211, 153, 0.3));
                border-radius: 50%;
                left: ${Math.random() * 100}%;
                top: ${Math.random() * 100}%;
                pointer-events: none;
                z-index: 1;
            `;
            particleContainer.appendChild(particle);
            
            // Animate with GSAP for better control
            gsap.to(particle, {
                y: `+=${20 + Math.random() * 40}`,
                x: `+=${-20 + Math.random() * 40}`,
                scale: 0.5 + Math.random() * 1.5,
                opacity: 0.3 + Math.random() * 0.7,
                duration: 8 + Math.random() * 12,
                ease: 'power2.inOut',
                repeat: -1,
                yoyo: true,
                delay: Math.random() * 5
            });
        }

        // Add particle animation keyframes
        const style = document.createElement('style');
        style.textContent = `
            @keyframes particleFloat {
                0%, 100% { 
                    transform: translateY(0px) translateX(0px) scale(1);
                    opacity: 0.3;
                }
                25% {
                    transform: translateY(-30px) translateX(10px) scale(1.2);
                    opacity: 0.7;
                }
                50% {
                    transform: translateY(20px) translateX(-15px) scale(0.8);
                    opacity: 0.5;
                }
                75% {
                    transform: translateY(-10px) translateX(20px) scale(1.1);
                    opacity: 0.6;
                }
            }
        `;
        document.head.appendChild(style);
    }

    transitionToApp() {
        console.log('Transitioning to app...');
        
        // Simple immediate navigation - no fancy animations to avoid issues
        window.location.href = '/app';
        
        // Fallback in case location change fails
        setTimeout(() => {
            if (window.location.pathname === '/') {
                console.log('Fallback navigation');
                window.open('/app', '_self');
            }
        }, 1000);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new FloraLanding();
    
    // Fallback button fix - ensure it's always visible
    setTimeout(() => {
        const startBtn = document.getElementById('start-btn');
        if (startBtn) {
            startBtn.style.cssText += `
                opacity: 1 !important;
                visibility: visible !important;
                display: inline-flex !important;
                pointer-events: auto !important;
                z-index: 9999 !important;
                position: relative !important;
            `;
            
            // Add click handler as backup
            startBtn.onclick = function(e) {
                e.preventDefault();
                console.log('Button clicked - navigating to app');
                window.location.href = '/app';
            };
        }
    }, 100);
});