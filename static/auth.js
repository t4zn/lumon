// Flora Authentication JavaScript

class FloraAuth {
    constructor() {
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.particles = [];
        this.canvas = null;
        
        this.init();
    }
    
    init() {
        this.init3DBackground();
        this.animate3D();
        this.initAnimations();
    }
    
    init3DBackground() {
        if (!window.THREE) {
            console.log('Three.js not available for 3D background');
            return;
        }
        
        this.canvas = document.getElementById('background-canvas');
        if (!this.canvas) return;
        
        // Scene setup
        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
        this.renderer = new THREE.WebGLRenderer({ 
            canvas: this.canvas, 
            alpha: true,
            antialias: true 
        });
        
        this.renderer.setSize(window.innerWidth, window.innerHeight);
        this.renderer.setClearColor(0x000000, 0);
        
        // Create floating particles
        this.createFloatingParticles();
        
        // Position camera
        this.camera.position.z = 5;
        
        // Handle window resize
        window.addEventListener('resize', () => {
            this.camera.aspect = window.innerWidth / window.innerHeight;
            this.camera.updateProjectionMatrix();
            this.renderer.setSize(window.innerWidth, window.innerHeight);
        });
    }
    
    createFloatingParticles() {
        const geometries = [
            new THREE.SphereGeometry(0.05, 8, 8),
            new THREE.BoxGeometry(0.08, 0.08, 0.08),
            new THREE.TetrahedronGeometry(0.07, 0)
        ];
        
        const colors = [0x10b981, 0x34d399, 0x059669, 0x50c878];
        
        for (let i = 0; i < 50; i++) {
            const geometry = geometries[Math.floor(Math.random() * geometries.length)];
            const material = new THREE.MeshBasicMaterial({ 
                color: colors[Math.floor(Math.random() * colors.length)],
                transparent: true,
                opacity: 0.6
            });
            
            const particle = new THREE.Mesh(geometry, material);
            
            // Random position
            particle.position.x = (Math.random() - 0.5) * 20;
            particle.position.y = (Math.random() - 0.5) * 20;
            particle.position.z = (Math.random() - 0.5) * 20;
            
            // Random rotation
            particle.rotation.x = Math.random() * Math.PI;
            particle.rotation.y = Math.random() * Math.PI;
            particle.rotation.z = Math.random() * Math.PI;
            
            // Animation properties
            particle.userData = {
                originalY: particle.position.y,
                speed: 0.5 + Math.random() * 1,
                amplitude: 0.5 + Math.random() * 1,
                rotationSpeed: 0.01 + Math.random() * 0.02
            };
            
            this.scene.add(particle);
            this.particles.push(particle);
        }
    }
    
    animate3D() {
        if (!this.renderer || !this.scene || !this.camera) return;
        
        const animate = () => {
            requestAnimationFrame(animate);
            
            const time = Date.now() * 0.001;
            
            // Animate particles
            this.particles.forEach((particle, index) => {
                const userData = particle.userData;
                
                // Floating motion
                particle.position.y = userData.originalY + 
                    Math.sin(time * userData.speed + index) * userData.amplitude;
                
                // Rotation
                particle.rotation.x += userData.rotationSpeed;
                particle.rotation.y += userData.rotationSpeed * 0.7;
                particle.rotation.z += userData.rotationSpeed * 0.5;
                
                // Gentle drift
                particle.position.x += Math.sin(time * 0.3 + index) * 0.001;
                particle.position.z += Math.cos(time * 0.2 + index) * 0.001;
            });
            
            this.renderer.render(this.scene, this.camera);
        };
        
        animate();
    }
    
    initAnimations() {
        // Entrance animations for elements
        const authOptions = document.getElementById('auth-options');
        if (authOptions) {
            authOptions.style.opacity = '0';
            authOptions.style.transform = 'translateY(30px)';
            
            setTimeout(() => {
                authOptions.style.transition = 'all 0.8s cubic-bezier(0.4, 0, 0.2, 1)';
                authOptions.style.opacity = '1';
                authOptions.style.transform = 'translateY(0)';
            }, 300);
        }
        
        // Stagger button animations
        const buttons = document.querySelectorAll('.auth-btn');
        buttons.forEach((btn, index) => {
            btn.style.opacity = '0';
            btn.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                btn.style.transition = 'all 0.6s cubic-bezier(0.4, 0, 0.2, 1)';
                btn.style.opacity = '1';
                btn.style.transform = 'translateY(0)';
            }, 500 + index * 100);
        });
    }
}

// Navigation functions
function showLogin() {
    const options = document.getElementById('auth-options');
    const loginForm = document.getElementById('login-form');
    
    options.style.opacity = '0';
    options.style.transform = 'translateX(-30px)';
    
    setTimeout(() => {
        options.style.display = 'none';
        loginForm.style.display = 'block';
        loginForm.style.opacity = '0';
        loginForm.style.transform = 'translateX(30px)';
        
        setTimeout(() => {
            loginForm.style.transition = 'all 0.5s cubic-bezier(0.4, 0, 0.2, 1)';
            loginForm.style.opacity = '1';
            loginForm.style.transform = 'translateX(0)';
        }, 50);
    }, 300);
}

function showSignup() {
    const options = document.getElementById('auth-options');
    const signupForm = document.getElementById('signup-form');
    
    options.style.opacity = '0';
    options.style.transform = 'translateX(-30px)';
    
    setTimeout(() => {
        options.style.display = 'none';
        signupForm.style.display = 'block';
        signupForm.style.opacity = '0';
        signupForm.style.transform = 'translateX(30px)';
        
        setTimeout(() => {
            signupForm.style.transition = 'all 0.5s cubic-bezier(0.4, 0, 0.2, 1)';
            signupForm.style.opacity = '1';
            signupForm.style.transform = 'translateX(0)';
        }, 50);
    }, 300);
}

function showOptions() {
    const loginForm = document.getElementById('login-form');
    const signupForm = document.getElementById('signup-form');
    const options = document.getElementById('auth-options');
    
    loginForm.style.opacity = '0';
    signupForm.style.opacity = '0';
    loginForm.style.transform = 'translateX(30px)';
    signupForm.style.transform = 'translateX(30px)';
    
    setTimeout(() => {
        loginForm.style.display = 'none';
        signupForm.style.display = 'none';
        options.style.display = 'flex';
        options.style.opacity = '0';
        options.style.transform = 'translateX(-30px)';
        
        setTimeout(() => {
            options.style.transition = 'all 0.5s cubic-bezier(0.4, 0, 0.2, 1)';
            options.style.opacity = '1';
            options.style.transform = 'translateX(0)';
        }, 50);
    }, 300);
}

// Placeholder functions for authentication (no actual functionality)
function continueWithGoogle() {
    showLoadingEffect();
    // Placeholder: Would integrate with Google OAuth
    setTimeout(() => {
        alert('Google OAuth integration placeholder - redirecting to app');
        window.location.href = '/app';
    }, 1500);
}

function continueAsGuest() {
    showLoadingEffect();
    // Direct redirect to app for testing
    setTimeout(() => {
        window.location.href = '/app';
    }, 1000);
}

function handleLogin(event) {
    event.preventDefault();
    showLoadingEffect();
    
    // Placeholder: Would validate credentials
    setTimeout(() => {
        alert('Login placeholder - redirecting to app');
        window.location.href = '/app';
    }, 1500);
}

function handleSignup(event) {
    event.preventDefault();
    showLoadingEffect();
    
    const password = event.target.querySelector('input[type="password"]').value;
    const confirmPassword = event.target.querySelectorAll('input[type="password"]')[1].value;
    
    if (password !== confirmPassword) {
        alert('Passwords do not match');
        return;
    }
    
    // Placeholder: Would create account
    setTimeout(() => {
        alert('Signup placeholder - redirecting to app');
        window.location.href = '/app';
    }, 1500);
}

function showLoadingEffect() {
    const buttons = document.querySelectorAll('button');
    buttons.forEach(btn => {
        btn.style.opacity = '0.6';
        btn.style.pointerEvents = 'none';
    });
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new FloraAuth();
});