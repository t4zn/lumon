// Flora Landing Page - Fixed Implementation

class FloraLanding {
    constructor() {
        this.initializeElements();
        this.createSimpleAnimations();
    }

    initializeElements() {
        this.particles = [];
        this.animationId = null;
    }

    createSimpleAnimations() {
        // Simple CSS-based animations are already handled by CSS
        // No complex JavaScript animations needed
        
        // Add entrance animations
        this.addEntranceAnimations();
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
    window.location.href = '/app';
}