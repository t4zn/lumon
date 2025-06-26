// Flora Landing Page - Fixed Implementation

class FloraLanding {
    constructor() {
        this.initializeElements();
        this.createSimpleAnimations();
        this.init3DParticles();
        this.addMouseInteraction();
    }

    initializeElements() {
        this.particles = [];
        this.animationId = null;
        this.mouseX = 0;
        this.mouseY = 0;
        this.floatingElements = document.querySelectorAll('.float-leaf, .float-pollen, .float-stem');
    }

    createSimpleAnimations() {
        // Add entrance animations
        this.addEntranceAnimations();
        
        // Enhanced floating animations
        this.enhanceFloatingElements();
    }

    init3DParticles() {
        // Create additional floating particles
        const particleContainer = document.querySelector('.floating-elements');
        
        for (let i = 0; i < 15; i++) {
            const particle = document.createElement('div');
            particle.className = 'dynamic-particle';
            particle.style.cssText = `
                position: fixed;
                width: ${Math.random() * 8 + 4}px;
                height: ${Math.random() * 8 + 4}px;
                background: rgba(16, 185, 129, ${Math.random() * 0.6 + 0.3});
                border-radius: 50%;
                pointer-events: none;
                z-index: 1;
                top: ${Math.random() * 100}%;
                left: ${Math.random() * 100}%;
                animation: dynamicFloat ${Math.random() * 20 + 10}s ease-in-out infinite;
                animation-delay: ${Math.random() * 5}s;
                box-shadow: 0 0 ${Math.random() * 20 + 10}px rgba(16, 185, 129, 0.5);
            `;
            particleContainer.appendChild(particle);
        }
    }

    addMouseInteraction() {
        document.addEventListener('mousemove', (e) => {
            this.mouseX = (e.clientX / window.innerWidth - 0.5) * 2;
            this.mouseY = (e.clientY / window.innerHeight - 0.5) * 2;
            
            // Apply subtle parallax effect to floating elements
            this.floatingElements.forEach((element, index) => {
                const speed = (index % 3 + 1) * 0.5;
                const x = this.mouseX * speed * 10;
                const y = this.mouseY * speed * 10;
                
                element.style.transform += ` translate(${x}px, ${y}px)`;
            });
        });
    }

    enhanceFloatingElements() {
        // Add random wind effect
        setInterval(() => {
            this.floatingElements.forEach(element => {
                const windStrength = Math.random() * 20 - 10;
                element.style.filter = `blur(${Math.abs(windStrength) * 0.1}px)`;
                
                setTimeout(() => {
                    element.style.filter = 'none';
                }, 1000);
            });
        }, 8000);
    }

    addEntranceAnimations() {
        const heroContent = document.querySelector('.hero-content');
        const features = document.querySelectorAll('.feature-card');
        
        if (heroContent) {
            heroContent.style.opacity = '0';
            heroContent.style.transform = 'translateY(30px)';
            
            setTimeout(() => {
                heroContent.style.transition = 'all 0.8s ease';
                heroContent.style.opacity = '1';
                heroContent.style.transform = 'translateY(0)';
            }, 100);
        }

        features.forEach((feature, index) => {
            if (feature) {
                feature.style.opacity = '0';
                feature.style.transform = 'translateY(20px)';
                
                setTimeout(() => {
                    feature.style.transition = 'all 0.6s ease';
                    feature.style.opacity = '1';
                    feature.style.transform = 'translateY(0)';
                }, 300 + (index * 150));
            }
        });
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new FloraLanding();
});

// Simple enter app function
function enterApp() {
    window.location.href = '/page0';
}