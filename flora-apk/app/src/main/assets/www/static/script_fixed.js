// Flora Plant Identifier - Fixed Implementation

class FloraApp {
    constructor() {
        this.messageCounter = 0;
        this.initializeElements();
        this.attachEventListeners();
        this.initializeTime();
        this.initializeTheme();
        this.init3DBackground();
        this.showInitialMessage();
    }

    initializeElements() {
        // Chat elements
        this.chatContainer = document.getElementById('chat-container');
        this.textInput = document.getElementById('text-input');
        this.sendBtn = document.getElementById('send-btn');
        this.attachBtn = document.getElementById('attach-btn');
        this.attachOptions = document.getElementById('attach-options');
        this.loadingOverlay = document.getElementById('loading-overlay');
        
        // Menu elements
        this.menuBtn = document.getElementById('menu-btn');
        this.sideMenu = document.getElementById('side-menu');
        this.menuOverlay = document.getElementById('menu-overlay');
        this.menuClose = document.getElementById('menu-close');
        this.continueChat = document.getElementById('continue-chat');
        this.newChat = document.getElementById('new-chat');
        this.clearHistory = document.getElementById('clear-history');
        
        // Camera elements
        this.cameraTriggerBtn = document.getElementById('camera-trigger-btn');
        this.galleryTriggerBtn = document.getElementById('gallery-trigger-btn');
        this.imageInput = document.getElementById('image-input');
        this.currentTime = document.getElementById('current-time');
        
        // Theme toggle
        this.themeToggle = document.getElementById('theme-toggle');
        
        console.log('Theme toggle element:', this.themeToggle);
    }

    attachEventListeners() {
        // Menu functionality
        if (this.menuBtn) {
            this.menuBtn.addEventListener('click', () => this.openMenu());
        }
        
        if (this.menuClose) {
            this.menuClose.addEventListener('click', () => this.closeMenu());
        }
        
        if (this.menuOverlay) {
            this.menuOverlay.addEventListener('click', () => this.closeMenu());
        }
        
        if (this.newChat) {
            this.newChat.addEventListener('click', () => {
                this.startNewChat();
                this.closeMenu();
            });
        }
        
        if (this.clearHistory) {
            this.clearHistory.addEventListener('click', () => {
                this.clearChatHistory();
                this.closeMenu();
            });
        }

        // Text input and send
        if (this.textInput) {
            this.textInput.addEventListener('input', () => this.updateSendButton());
            this.textInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });
        }
        
        if (this.sendBtn) {
            this.sendBtn.addEventListener('click', () => this.sendMessage());
        }
        
        // Attach button
        if (this.attachBtn) {
            this.attachBtn.addEventListener('click', () => this.toggleAttachOptions());
        }
        
        // Camera and gallery buttons
        if (this.cameraTriggerBtn) {
            this.cameraTriggerBtn.addEventListener('click', () => {
                this.hideAttachOptions();
                this.triggerImageUpload();
            });
        }
        
        if (this.galleryTriggerBtn) {
            this.galleryTriggerBtn.addEventListener('click', () => {
                this.hideAttachOptions();
                this.triggerImageUpload();
            });
        }
        
        // Image input
        if (this.imageInput) {
            this.imageInput.addEventListener('change', (e) => {
                if (e.target.files && e.target.files[0]) {
                    this.handleImageUpload(e.target.files[0]);
                }
            });
        }
        
        // Suggestions
        document.querySelectorAll('.suggestion').forEach(suggestion => {
            suggestion.addEventListener('click', () => {
                if (this.textInput) {
                    this.textInput.value = suggestion.getAttribute('data-text');
                    this.updateSendButton();
                }
            });
        });
        
        // Theme toggle
        if (this.themeToggle) {
            this.themeToggle.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.toggleTheme();
            });
            console.log('Theme toggle event listener attached');
        } else {
            console.log('Theme toggle element not found');
        }
        
        // Click outside to close
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.attach-btn') && !e.target.closest('.attach-options')) {
                this.hideAttachOptions();
            }
        });
    }

    // Menu functions
    openMenu() {
        if (this.sideMenu) this.sideMenu.classList.add('open');
        if (this.menuOverlay) this.menuOverlay.classList.add('show');
    }

    closeMenu() {
        if (this.sideMenu) this.sideMenu.classList.remove('open');
        if (this.menuOverlay) this.menuOverlay.classList.remove('show');
    }

    startNewChat() {
        if (this.chatContainer) {
            const messages = this.chatContainer.querySelectorAll('.chat-message:not(#welcome-message)');
            messages.forEach(msg => msg.remove());
        }
        this.messageCounter = 0;
        this.showInitialMessage();
    }

    clearChatHistory() {
        this.startNewChat();
    }

    // Input functions
    updateSendButton() {
        if (this.sendBtn && this.textInput) {
            const hasText = this.textInput.value.trim().length > 0;
            this.sendBtn.disabled = !hasText;
            this.sendBtn.style.opacity = hasText ? '1' : '0.5';
        }
    }

    toggleAttachOptions() {
        if (this.attachOptions) {
            const isVisible = this.attachOptions.style.display === 'flex';
            this.attachOptions.style.display = isVisible ? 'none' : 'flex';
        }
    }

    hideAttachOptions() {
        if (this.attachOptions) {
            this.attachOptions.style.display = 'none';
        }
    }

    triggerImageUpload() {
        if (this.imageInput) {
            this.imageInput.click();
        }
    }

    // Time update
    initializeTime() {
        this.updateTime();
        setInterval(() => this.updateTime(), 1000);
    }
    
    updateTime() {
        if (this.currentTime) {
            const now = new Date();
            const timeString = now.toLocaleTimeString('en-US', { 
                hour: 'numeric', 
                minute: '2-digit',
                hour12: false 
            });
            this.currentTime.textContent = timeString;
        }
    }

    // Initial message
    showInitialMessage() {
        const initialTyping = document.getElementById('initial-typing');
        const initialMessage = document.getElementById('initial-message');
        
        if (initialTyping && initialMessage) {
            initialTyping.style.display = 'flex';
            initialMessage.style.display = 'none';
            
            setTimeout(() => {
                initialTyping.style.display = 'none';
                initialMessage.style.display = 'block';
                initialMessage.style.opacity = '0';
                initialMessage.style.transform = 'translateY(10px)';
                
                setTimeout(() => {
                    initialMessage.style.transition = 'all 0.3s ease';
                    initialMessage.style.opacity = '1';
                    initialMessage.style.transform = 'translateY(0)';
                }, 50);
            }, 2000);
        }
    }

    // Message handling
    async sendMessage() {
        const message = this.textInput?.value.trim();
        if (!message) return;

        this.addMessage(message, 'user');
        
        if (this.textInput) this.textInput.value = '';
        this.updateSendButton();

        const typingId = this.addTypingIndicator();

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message })
            });

            const data = await response.json();
            this.removeTypingIndicator(typingId);

            if (data.error) {
                this.addMessage('I apologize, but I encountered an error. Please try rephrasing your botanical question.', 'bot');
            } else {
                this.addMessage(data.response, 'bot');
            }
        } catch (error) {
            console.error('Error sending message:', error);
            this.removeTypingIndicator(typingId);
            this.addMessage('I\'m having trouble connecting. Please check your internet and try again.', 'bot');
        }
    }

    // Image upload
    async handleImageUpload(file) {
        if (!file) return;

        const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];
        if (!allowedTypes.includes(file.type)) {
            this.addMessage('Please upload a valid image file (JPEG, PNG, GIF, or WebP).', 'bot');
            return;
        }

        if (file.size > 16 * 1024 * 1024) {
            this.addMessage('Please upload an image smaller than 16MB.', 'bot');
            return;
        }

        this.addImageMessage(file);
        this.showLoading();

        try {
            const formData = new FormData();
            formData.append('image', file);

            const response = await fetch('/predict', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            this.hideLoading();

            if (data.error) {
                this.addMessage(`I couldn't analyze your image: ${data.error}. Please try a clearer photo.`, 'bot');
            } else {
                this.addPlantIdentificationResult(data);
            }
        } catch (error) {
            console.error('Error uploading image:', error);
            this.hideLoading();
            this.addMessage('I\'m having trouble analyzing your image. Please try again.', 'bot');
        }
    }

    // UI helper functions
    addMessage(text, sender) {
        if (!this.chatContainer) return;

        const messageId = `${sender}-msg-${++this.messageCounter}`;
        const time = new Date().toLocaleTimeString('en-US', { 
            hour: 'numeric', 
            minute: '2-digit' 
        });

        const messageHtml = `
            <div class="chat-message ${sender}-message" id="${messageId}">
                ${sender === 'bot' ? `
                    <div class="message-avatar">
                        <div class="avatar-glow">
                            <i class="fas fa-seedling"></i>
                        </div>
                    </div>
                ` : ''}
                <div class="message-content">
                    <div class="message-bubble">
                        <div class="message-text">${text}</div>
                    </div>
                    <div class="message-time">${time}</div>
                </div>
                ${sender === 'user' ? `
                    <div class="message-avatar">
                        <i class="fas fa-user"></i>
                    </div>
                ` : ''}
            </div>
        `;

        this.chatContainer.insertAdjacentHTML('beforeend', messageHtml);
        this.scrollToBottom();
    }

    addImageMessage(file) {
        if (!this.chatContainer) return;

        const messageId = `user-msg-${++this.messageCounter}`;
        const time = new Date().toLocaleTimeString('en-US', { 
            hour: 'numeric', 
            minute: '2-digit' 
        });

        const imageUrl = URL.createObjectURL(file);
        const messageHtml = `
            <div class="chat-message user-message" id="${messageId}">
                <div class="message-content">
                    <div class="message-bubble">
                        <img src="${imageUrl}" alt="Plant image" style="max-width: 200px; border-radius: 10px; margin-bottom: 10px;">
                        <div class="message-text">Can you identify this plant?</div>
                    </div>
                    <div class="message-time">${time}</div>
                </div>
                <div class="message-avatar">
                    <i class="fas fa-user"></i>
                </div>
            </div>
        `;

        this.chatContainer.insertAdjacentHTML('beforeend', messageHtml);
        this.scrollToBottom();
    }

    addTypingIndicator() {
        if (!this.chatContainer) return null;

        const typingId = `typing-${Date.now()}`;
        const typingHtml = `
            <div class="chat-message bot-message" id="${typingId}">
                <div class="message-avatar">
                    <div class="avatar-glow">
                        <i class="fas fa-seedling"></i>
                    </div>
                </div>
                <div class="message-content">
                    <div class="message-bubble">
                        <div class="typing-animation">
                            <span></span>
                            <span></span>
                            <span></span>
                        </div>
                    </div>
                </div>
            </div>
        `;

        this.chatContainer.insertAdjacentHTML('beforeend', typingHtml);
        this.scrollToBottom();
        return typingId;
    }

    removeTypingIndicator(typingId) {
        if (typingId) {
            const element = document.getElementById(typingId);
            if (element) element.remove();
        }
    }

    addPlantIdentificationResult(data) {
        if (!this.chatContainer) return;

        const messageId = `bot-msg-${++this.messageCounter}`;
        const time = new Date().toLocaleTimeString('en-US', { 
            hour: 'numeric', 
            minute: '2-digit' 
        });

        // Create care tips HTML
        let careTipsHtml = '';
        if (data.care_tips && data.care_tips.length > 0) {
            careTipsHtml = `
                <div class="care-tips">
                    <h4>Essential Care Tips:</h4>
                    <ul>
                        ${data.care_tips.map(tip => `<li>${tip}</li>`).join('')}
                    </ul>
                </div>
            `;
        }

        // Create Wikipedia link (only if data has wiki_url)
        let wikiLinkHtml = '';
        if (data.wiki_url) {
            wikiLinkHtml = `
                <div class="wiki-link">
                    <a href="${data.wiki_url}" target="_blank" class="read-more-btn">
                        <i class="fas fa-external-link-alt"></i>
                        Read more on Wikipedia
                    </a>
                </div>
            `;
        }

        const messageHtml = `
            <div class="chat-message bot-message plant-result-message" id="${messageId}">
                <div class="message-avatar">
                    <div class="avatar-glow">
                        <i class="fas fa-seedling"></i>
                    </div>
                </div>
                <div class="message-content">
                    <div class="message-bubble">
                        <div class="plant-identification-result">
                            <div class="plant-title">🌿 ${data.plant}</div>
                            ${data.scientific_name && data.scientific_name !== data.plant ? 
                                `<div class="scientific-name">${data.scientific_name}</div>` : ''
                            }
                            ${data.confidence ? 
                                `<div class="confidence">Confidence: ${Math.round(data.confidence * 100)}%</div>` : ''
                            }
                            <div class="plant-description">${data.description || ''}</div>
                            ${careTipsHtml}
                            ${wikiLinkHtml}
                        </div>
                    </div>
                    <div class="message-time">${time}</div>
                </div>
            </div>
        `;

        this.chatContainer.insertAdjacentHTML('beforeend', messageHtml);
        this.scrollToBottom();
    }

    scrollToBottom() {
        if (this.chatContainer) {
            setTimeout(() => {
                this.chatContainer.scrollTop = this.chatContainer.scrollHeight;
            }, 100);
        }
    }

    showLoading() {
        if (this.loadingOverlay) {
            this.loadingOverlay.style.display = 'flex';
        }
    }

    hideLoading() {
        if (this.loadingOverlay) {
            this.loadingOverlay.style.display = 'none';
        }
    }

    // Theme functionality
    toggleTheme() {
        console.log('Toggle theme called');
        const body = document.body;
        const currentTheme = body.getAttribute('data-theme') || 'dark';
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        body.setAttribute('data-theme', newTheme);
        document.documentElement.setAttribute('data-bs-theme', newTheme);
        localStorage.setItem('flora-theme', newTheme);
        
        console.log('Theme changed to:', newTheme);
        
        // Update theme toggle icon
        if (this.themeToggle) {
            const lightIcon = this.themeToggle.querySelector('.theme-icon-light');
            const darkIcon = this.themeToggle.querySelector('.theme-icon-dark');
            
            if (newTheme === 'light') {
                if (lightIcon) lightIcon.style.display = 'none';
                if (darkIcon) darkIcon.style.display = 'block';
            } else {
                if (lightIcon) lightIcon.style.display = 'block';
                if (darkIcon) darkIcon.style.display = 'none';
            }
        }
    }

    initializeTheme() {
        const savedTheme = localStorage.getItem('flora-theme') || 'dark';
        document.body.setAttribute('data-theme', savedTheme);
        document.documentElement.setAttribute('data-bs-theme', savedTheme);
        
        console.log('Theme initialized to:', savedTheme);
        
        // Set initial icon state
        if (this.themeToggle) {
            const lightIcon = this.themeToggle.querySelector('.theme-icon-light');
            const darkIcon = this.themeToggle.querySelector('.theme-icon-dark');
            
            if (savedTheme === 'light') {
                if (lightIcon) lightIcon.style.display = 'none';
                if (darkIcon) darkIcon.style.display = 'block';
            } else {
                if (lightIcon) lightIcon.style.display = 'block';
                if (darkIcon) darkIcon.style.display = 'none';
            }
        }
    }

    // 3D Background
    init3DBackground() {
        if (typeof THREE === 'undefined') return;

        try {
            const canvas = document.getElementById('bg-canvas');
            if (!canvas) return;

            this.scene = new THREE.Scene();
            this.camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
            this.renderer = new THREE.WebGLRenderer({ canvas: canvas, alpha: true });
            
            this.renderer.setSize(window.innerWidth, window.innerHeight);
            this.renderer.setClearColor(0x000000, 0);

            this.camera.position.z = 5;
            this.particles3D = [];

            this.create3DParticles();
            this.animate3D();

            window.addEventListener('resize', () => {
                this.camera.aspect = window.innerWidth / window.innerHeight;
                this.camera.updateProjectionMatrix();
                this.renderer.setSize(window.innerWidth, window.innerHeight);
            });
        } catch (error) {
            console.warn('3D background initialization failed:', error);
        }
    }

    create3DParticles() {
        // Create various botanical elements
        const geometries = [
            new THREE.PlaneGeometry(0.3, 0.4), // Leaves
            new THREE.SphereGeometry(0.1, 8, 6), // Pollen
            new THREE.CylinderGeometry(0.02, 0.02, 0.8, 8), // Stems
            new THREE.RingGeometry(0.1, 0.15, 6), // Flowers
        ];

        const materials = [
            new THREE.MeshBasicMaterial({ color: 0x10b981, transparent: true, opacity: 0.7 }),
            new THREE.MeshBasicMaterial({ color: 0x34d399, transparent: true, opacity: 0.8 }),
            new THREE.MeshBasicMaterial({ color: 0x059669, transparent: true, opacity: 0.6 }),
            new THREE.MeshBasicMaterial({ color: 0x6ee7b7, transparent: true, opacity: 0.5 }),
        ];

        for (let i = 0; i < 25; i++) {
            const geometry = geometries[Math.floor(Math.random() * geometries.length)];
            const material = materials[Math.floor(Math.random() * materials.length)];
            const mesh = new THREE.Mesh(geometry, material);
            
            // Random positioning in 3D space
            mesh.position.x = (Math.random() - 0.5) * 15;
            mesh.position.y = (Math.random() - 0.5) * 15;
            mesh.position.z = (Math.random() - 0.5) * 8;
            
            // Random rotation
            mesh.rotation.x = Math.random() * Math.PI * 2;
            mesh.rotation.y = Math.random() * Math.PI * 2;
            mesh.rotation.z = Math.random() * Math.PI * 2;
            
            // Random animation speeds
            mesh.rotationSpeed = {
                x: (Math.random() - 0.5) * 0.02,
                y: (Math.random() - 0.5) * 0.02,
                z: (Math.random() - 0.5) * 0.02
            };
            
            mesh.floatSpeed = (Math.random() - 0.5) * 0.01;
            mesh.originalY = mesh.position.y;
            
            this.particles3D.push(mesh);
            this.scene.add(mesh);
        }
    }

    animate3D() {
        if (!this.renderer || !this.scene || !this.camera) return;
        
        requestAnimationFrame(() => this.animate3D());
        
        const time = Date.now() * 0.001;
        
        if (this.particles3D) {
            this.particles3D.forEach((particle, index) => {
                // Rotation animation
                particle.rotation.x += particle.rotationSpeed.x;
                particle.rotation.y += particle.rotationSpeed.y;
                particle.rotation.z += particle.rotationSpeed.z;
                
                // Floating animation
                particle.position.y = particle.originalY + Math.sin(time + index) * 0.5;
                
                // Gentle swaying
                particle.position.x += Math.sin(time * 0.5 + index) * 0.002;
                particle.position.z += Math.cos(time * 0.3 + index) * 0.002;
                
                // Breathing effect (scale)
                const scale = 1 + Math.sin(time * 2 + index) * 0.1;
                particle.scale.set(scale, scale, scale);
            });
        }
        
        // Camera gentle movement
        this.camera.position.x = Math.sin(time * 0.1) * 0.5;
        this.camera.position.y = Math.cos(time * 0.15) * 0.3;
        this.camera.lookAt(0, 0, 0);
        
        this.renderer.render(this.scene, this.camera);
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new FloraApp();
});