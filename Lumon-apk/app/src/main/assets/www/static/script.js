// Lumon Plant Identifier - Mobile Chatbot Interface

class LumonApp {
    constructor() {
        this.initializeElements();
        this.attachEventListeners();
        this.initializeTime();
        this.initializeTheme();
        this.setupCamera();
        this.init3DBackground();
        this.initAnimations();
        this.messageCounter = 0;
        this.showInitialMessage();
    }

    initializeElements() {
        // Helper function to safely get elements
        const safeGetElement = (id) => {
            const element = document.getElementById(id);
            if (!element) {
                console.warn(`Element with id '${id}' not found`);
            }
            return element;
        };

        // Chat elements
        this.chatContainer = safeGetElement('chat-container');
        this.welcomeMessage = safeGetElement('welcome-message');
        
        // Camera elements
        this.cameraInterface = safeGetElement('camera-interface');
        this.cameraVideo = safeGetElement('camera-video');
        this.cameraCanvas = safeGetElement('camera-canvas');
        this.focusRing = safeGetElement('focus-ring');
        
        // Control buttons
        this.cameraTriggerBtn = safeGetElement('camera-trigger-btn');
        this.galleryTriggerBtn = safeGetElement('gallery-trigger-btn');
        this.cameraCloseBtn = safeGetElement('camera-close');
        this.cameraDoneBtn = safeGetElement('camera-done');
        this.captureBtn = safeGetElement('capture-btn');
        this.galleryBtn = safeGetElement('gallery-btn');
        this.flashBtn = safeGetElement('flash-btn');
        
        // Chat input elements
        this.textInput = safeGetElement('text-input');
        this.sendBtn = safeGetElement('send-btn');
        this.attachBtn = safeGetElement('attach-btn');
        this.attachOptions = safeGetElement('attach-options');
        this.inputSuggestions = safeGetElement('input-suggestions');
        
        // Theme and settings
        this.themeToggle = safeGetElement('theme-toggle');
        this.settingsBtn = safeGetElement('settings-btn');
        this.settingsModal = safeGetElement('settings-modal');
        this.settingsClose = safeGetElement('settings-close');
        
        // Form and loading
        this.uploadForm = safeGetElement('upload-form');
        this.imageInput = safeGetElement('image-input');
        this.loadingOverlay = safeGetElement('loading-overlay');
        
        // Status bar
        this.currentTime = safeGetElement('current-time');
        
        // Camera stream
        this.cameraStream = null;
        this.flashEnabled = false;
    }

    attachEventListeners() {
        // Helper function to safely add event listeners
        const safeAddListener = (element, event, handler) => {
            if (element) {
                element.addEventListener(event, handler);
            }
        };

        // Menu functionality
        this.menuBtn = document.getElementById('menu-btn');
        this.sideMenu = document.getElementById('side-menu');
        this.menuOverlay = document.getElementById('menu-overlay');
        this.menuClose = document.getElementById('menu-close');
        this.continueChat = document.getElementById('continue-chat');
        this.newChat = document.getElementById('new-chat');
        this.clearHistory = document.getElementById('clear-history');

        safeAddListener(this.menuBtn, 'click', () => {
            this.openMenu();
        });

        safeAddListener(this.menuClose, 'click', () => {
            this.closeMenu();
        });

        safeAddListener(this.menuOverlay, 'click', () => {
            this.closeMenu();
        });

        safeAddListener(this.continueChat, 'click', () => {
            this.closeMenu();
        });

        safeAddListener(this.newChat, 'click', () => {
            this.startNewChat();
            this.closeMenu();
        });

        safeAddListener(this.clearHistory, 'click', () => {
            this.clearChatHistory();
            this.closeMenu();
        });

        // Camera trigger buttons - Fix mobile gallery issue
        safeAddListener(this.cameraTriggerBtn, 'click', () => {
            this.hideAttachOptions();
            this.openCamera();
        });
        
        safeAddListener(this.galleryTriggerBtn, 'click', () => {
            this.hideAttachOptions();
            // Use separate input for gallery to avoid camera opening
            const galleryInput = document.createElement('input');
            galleryInput.type = 'file';
            galleryInput.accept = 'image/*';
            galleryInput.style.display = 'none';
            galleryInput.onchange = (e) => {
                if (e.target.files && e.target.files[0]) {
                    this.handleImageUpload(e.target.files[0]);
                }
                document.body.removeChild(galleryInput);
            };
            document.body.appendChild(galleryInput);
            galleryInput.click();
        });
        
        // Camera interface controls
        safeAddListener(this.cameraCloseBtn, 'click', () => {
            this.closeCamera();
        });
        
        safeAddListener(this.cameraDoneBtn, 'click', () => {
            this.closeCamera();
        });
        
        safeAddListener(this.captureBtn, 'click', () => {
            this.capturePhoto();
        });
        
        safeAddListener(this.galleryBtn, 'click', () => {
            this.closeCamera();
            if (this.imageInput) this.imageInput.click();
        });
        
        safeAddListener(this.flashBtn, 'click', () => {
            this.toggleFlash();
        });
        
        // Theme toggle
        safeAddListener(this.themeToggle, 'click', () => {
            this.toggleTheme();
        });
        
        // Settings
        safeAddListener(this.settingsBtn, 'click', () => {
            this.openSettings();
        });
        
        safeAddListener(this.settingsClose, 'click', () => {
            this.closeSettings();
        });
        
        // Theme options in settings
        document.querySelectorAll('.theme-option').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.changeTheme(e.target.dataset.theme);
            });
        });
        
        // File input change
        safeAddListener(this.imageInput, 'change', (e) => {
            if (e.target.files && e.target.files[0]) {
                this.handleImageSelection(e.target.files[0]);
            }
        });
        
        // Camera viewfinder tap to focus
        safeAddListener(this.cameraVideo, 'click', (e) => {
            this.focusCamera(e);
        });
        
        // Form submission
        safeAddListener(this.uploadForm, 'submit', (e) => {
            e.preventDefault();
        });
        
        // Text input events
        safeAddListener(this.textInput, 'input', () => {
            this.handleTextInput();
        });
        
        safeAddListener(this.textInput, 'keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendTextMessage();
            }
        });
        
        safeAddListener(this.textInput, 'focus', () => {
            this.showSuggestions();
        });
        
        safeAddListener(this.textInput, 'blur', () => {
            setTimeout(() => this.hideSuggestions(), 150);
        });
        
        safeAddListener(this.sendBtn, 'click', () => {
            this.sendTextMessage();
        });
        
        safeAddListener(this.attachBtn, 'click', () => {
            this.toggleAttachOptions();
        });
        
        // Suggestion clicks
        document.querySelectorAll('.suggestion').forEach(suggestion => {
            suggestion.addEventListener('click', () => {
                this.textInput.value = suggestion.dataset.text;
                this.handleTextInput();
                this.hideSuggestions();
                this.textInput.focus();
            });
        });
    }

    initializeTime() {
        this.updateTime();
        setInterval(() => this.updateTime(), 1000);
    }
    
    updateTime() {
        const now = new Date();
        const timeString = now.toLocaleTimeString('en-US', { 
            hour: 'numeric', 
            minute: '2-digit',
            hour12: false 
        });
        if (this.currentTime) {
            this.currentTime.textContent = timeString;
        }
    }
    
    initializeTheme() {
        const savedTheme = localStorage.getItem('Lumon-theme') || 'dark';
        this.setTheme(savedTheme);
    }
    
    toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        this.setTheme(newTheme);
    }
    
    changeTheme(theme) {
        this.setTheme(theme);
        this.closeSettings();
    }
    
    setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('Lumon-theme', theme);
        
        // Update active theme option
        document.querySelectorAll('.theme-option').forEach(btn => {
            btn.classList.remove('active');
            if (btn.dataset.theme === theme) {
                btn.classList.add('active');
            }
        });
    }
    
    openSettings() {
        if (!this.settingsModal) return;
        this.settingsModal.style.display = 'flex';
        if (window.gsap) {
            gsap.fromTo(this.settingsModal, 
                { opacity: 0 },
                { opacity: 1, duration: 0.3 }
            );
        }
    }
    
    closeSettings() {
        if (!this.settingsModal) return;
        if (window.gsap) {
            gsap.to(this.settingsModal, {
                opacity: 0,
                duration: 0.3,
                onComplete: () => {
                    this.settingsModal.style.display = 'none';
                }
            });
        } else {
            this.settingsModal.style.display = 'none';
        }
    }

    setupCamera() {
        this.cameraSupported = 'mediaDevices' in navigator && 'getUserMedia' in navigator.mediaDevices;
        
        if (!this.cameraSupported) {
            console.log('Camera not supported');
            this.cameraTriggerBtn.style.opacity = '0.5';
        }
    }
    
    async openCamera() {
        if (!this.cameraSupported) {
            this.addBotMessage('Camera is not supported on this device. Please use the gallery option instead.');
            return;
        }
        
        try {
            this.cameraStream = await navigator.mediaDevices.getUserMedia({
                video: { 
                    facingMode: 'environment',
                    width: { ideal: 1920 },
                    height: { ideal: 1080 }
                }
            });
            
            this.cameraVideo.srcObject = this.cameraStream;
            this.cameraInterface.style.display = 'flex';
            
            // Animate camera interface
            gsap.fromTo(this.cameraInterface,
                { opacity: 0, scale: 0.9 },
                { opacity: 1, scale: 1, duration: 0.4, ease: "power2.out" }
            );
            
        } catch (error) {
            console.error('Error accessing camera:', error);
            this.addBotMessage('Unable to access camera. Please check permissions and try again.');
        }
    }
    
    closeCamera() {
        if (this.cameraStream) {
            this.cameraStream.getTracks().forEach(track => track.stop());
            this.cameraStream = null;
        }
        
        gsap.to(this.cameraInterface, {
            opacity: 0,
            scale: 0.9,
            duration: 0.3,
            onComplete: () => {
                this.cameraInterface.style.display = 'none';
            }
        });
    }
    
    capturePhoto() {
        if (!this.cameraStream) return;
        
        const canvas = this.cameraCanvas;
        const video = this.cameraVideo;
        const context = canvas.getContext('2d');
        
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        
        context.drawImage(video, 0, 0);
        
        // Convert to blob and process
        canvas.toBlob((blob) => {
            this.closeCamera();
            this.handleImageSelection(blob);
        }, 'image/jpeg', 0.8);
        
        // Visual feedback
        this.focusRing.classList.add('active');
        setTimeout(() => {
            this.focusRing.classList.remove('active');
        }, 1000);
    }
    
    focusCamera(event) {
        const rect = this.cameraVideo.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;
        
        this.focusRing.style.left = `${x - 50}px`;
        this.focusRing.style.top = `${y - 50}px`;
        this.focusRing.classList.add('active');
        
        setTimeout(() => {
            this.focusRing.classList.remove('active');
        }, 1000);
    }
    
    toggleFlash() {
        this.flashEnabled = !this.flashEnabled;
        this.flashBtn.style.color = this.flashEnabled ? '#fbbf24' : '';
        
        // Flash functionality would require advanced camera API
        // This is a visual toggle for now
    }
    
    handleImageSelection(file) {
        if (!file) return;
        
        // Validate file type for uploaded files
        if (file.type && !this.isValidImageType(file)) {
            this.addBotMessage('Please select a valid image file (PNG, JPG, JPEG, GIF, WEBP).');
            return;
        }
        
        // Validate file size (16MB limit)
        if (file.size > 16 * 1024 * 1024) {
            this.addBotMessage('File size must be less than 16MB. Please choose a smaller image.');
            return;
        }
        
        // Add user message with image
        this.addUserMessage(file);
        
        // Process the image
        this.processImage(file);
    }
    
    isValidImageType(file) {
        const validTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp'];
        return validTypes.includes(file.type);
    }

    addUserMessage(file) {
        if (!this.chatContainer) return;
        
        const messageId = `user-msg-${++this.messageCounter}`;
        const time = new Date().toLocaleTimeString('en-US', { 
            hour: 'numeric', 
            minute: '2-digit' 
        });
        
        const messageHtml = `
            <div class="chat-message user-message" id="${messageId}">
                <div class="message-content">
                    <div class="message-bubble">
                        <img src="${URL.createObjectURL(file)}" alt="Plant image" class="plant-image">
                        <p>Can you identify this plant?</p>
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
    
    addBotMessage(text, plantResult = null) {
        if (!this.chatContainer) return;
        
        const messageId = `bot-msg-${++this.messageCounter}`;
        const time = new Date().toLocaleTimeString('en-US', { 
            hour: 'numeric', 
            minute: '2-digit' 
        });
        
        let resultHtml = '';
        if (plantResult) {
            const careList = plantResult.care_tips ? 
                plantResult.care_tips.map(tip => `<li>${tip}</li>`).join('') : '';
            
            resultHtml = `
                <div class="plant-result">
                    <div class="plant-name">${plantResult.plant}</div>
                    <div class="plant-description">${plantResult.description}</div>
                    ${careList ? `
                        <div class="care-tips">
                            <h4>Care Tips:</h4>
                            <ul>${careList}</ul>
                        </div>
                    ` : ''}
                    <a href="${plantResult.wiki_url}" target="_blank" class="read-more-btn">
                        <i class="fas fa-external-link-alt"></i>
                        Read More on Wikipedia
                    </a>
                </div>
            `;
        }
        
        const messageHtml = `
            <div class="chat-message bot-message" id="${messageId}">
                <div class="message-avatar">
                    <i class="fas fa-seedling"></i>
                </div>
                <div class="message-content">
                    <div class="message-bubble">
                        <p>${text}</p>
                        ${resultHtml}
                    </div>
                    <div class="message-time">${time}</div>
                </div>
            </div>
        `;
        
        this.chatContainer.insertAdjacentHTML('beforeend', messageHtml);
        this.scrollToBottom();
    }
    
    scrollToBottom() {
        if (!this.chatContainer) return;
        setTimeout(() => {
            this.chatContainer.scrollTop = this.chatContainer.scrollHeight;
        }, 100);
    }
    
    async processImage(file) {
        // Show loading
        this.showLoading();
        
        // Add bot typing message
        this.addBotMessage('Analyzing your plant image...');

        try {
            const formData = new FormData();
            formData.append('image', file);

            const response = await fetch('/predict', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to identify plant');
            }

            // Hide loading
            this.hideLoading();
            
            // Remove typing message
            const lastMessage = this.chatContainer.lastElementChild;
            if (lastMessage && lastMessage.textContent.includes('Analyzing')) {
                lastMessage.remove();
            }

            // Show results with enhanced styling
            this.addBotMessage('Great! I was able to identify your plant:', data);

        } catch (error) {
            console.error('Error:', error);
            this.hideLoading();
            
            // Remove typing message
            const lastMessage = this.chatContainer.lastElementChild;
            if (lastMessage && lastMessage.textContent.includes('Analyzing')) {
                lastMessage.remove();
            }
            
            this.addBotMessage('Sorry, I had trouble identifying this plant. Please try another image or make sure the plant is clearly visible.');
        }
    }

    showLoading() {
        this.loadingOverlay.style.display = 'flex';
        gsap.fromTo(this.loadingOverlay,
            { opacity: 0 },
            { opacity: 1, duration: 0.3 }
        );
    }

    hideLoading() {
        gsap.to(this.loadingOverlay, {
            opacity: 0,
            duration: 0.3,
            onComplete: () => {
                this.loadingOverlay.style.display = 'none';
            }
        });
    }

    // Helper methods for transitions and animations
    fadeIn(element, duration = 0.3) {
        gsap.fromTo(element,
            { opacity: 0, y: 20 },
            { opacity: 1, y: 0, duration: duration }
        );
    }
    
    fadeOut(element, duration = 0.3) {
        return new Promise(resolve => {
            gsap.to(element, {
                opacity: 0,
                y: -20,
                duration: duration,
                onComplete: resolve
            });
        });
    }
    
    // Show initial typing message
    showInitialMessage() {
        setTimeout(() => {
            document.getElementById('initial-typing').style.display = 'none';
            document.getElementById('initial-message').style.display = 'block';
            
            if (window.gsap) {
                gsap.fromTo('#initial-message',
                    { opacity: 0, y: 20 },
                    { opacity: 1, y: 0, duration: 0.5 }
                );
            }
        }, 2000);
    }
    
    // Text input handling
    handleTextInput() {
        const value = this.textInput.value.trim();
        this.sendBtn.disabled = value.length === 0;
        
        if (value.length === 0) {
            this.showSuggestions();
        } else {
            this.hideSuggestions();
        }
    }
    
    showSuggestions() {
        if (this.inputSuggestions && this.textInput.value.trim().length === 0) {
            this.inputSuggestions.classList.add('show');
        }
    }
    
    hideSuggestions() {
        if (this.inputSuggestions) {
            this.inputSuggestions.classList.remove('show');
        }
    }
    
    toggleAttachOptions() {
        if (!this.attachOptions) return;
        
        const isVisible = this.attachOptions.style.display === 'block';
        
        if (isVisible) {
            this.hideAttachOptions();
        } else {
            this.showAttachOptions();
        }
    }
    
    showAttachOptions() {
        if (!this.attachOptions) return;
        this.attachOptions.style.display = 'block';
        this.attachBtn.classList.add('active');
        
        // Auto-hide after image selection or 5 seconds
        setTimeout(() => {
            this.hideAttachOptions();
        }, 5000);
    }
    
    hideAttachOptions() {
        if (!this.attachOptions) return;
        this.attachOptions.style.display = 'none';
        this.attachBtn.classList.remove('active');
    }
    
    async sendTextMessage() {
        const message = this.textInput.value.trim();
        if (!message) return;
        
        // Add user message
        this.addUserTextMessage(message);
        
        // Clear input
        this.textInput.value = '';
        this.handleTextInput();
        this.hideSuggestions();
        
        // Show typing indicator
        const typingId = this.addBotTyping();
        
        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message })
            });
            
            const data = await response.json();
            
            // Remove typing indicator
            this.removeBotTyping(typingId);
            
            if (response.ok) {
                this.addBotMessage(data.response);
            } else {
                this.addBotMessage('Sorry, I encountered an error. Please try again.');
            }
        } catch (error) {
            console.error('Error:', error);
            this.removeBotTyping(typingId);
            this.addBotMessage('Sorry, I had trouble processing your message. Please check your connection and try again.');
        }
    }
    
    addUserTextMessage(text) {
        if (!this.chatContainer) return;
        
        const messageId = `user-msg-${++this.messageCounter}`;
        const time = new Date().toLocaleTimeString('en-US', { 
            hour: 'numeric', 
            minute: '2-digit' 
        });
        
        const messageHtml = `
            <div class="chat-message user-message" id="${messageId}">
                <div class="message-content">
                    <div class="message-bubble">
                        <p>${text}</p>
                    </div>
                    <div class="message-time">${time}</div>
                </div>
                <div class="message-avatar">
                    <div class="avatar-glow">
                        <i class="fas fa-user"></i>
                    </div>
                </div>
            </div>
        `;
        
        this.chatContainer.insertAdjacentHTML('beforeend', messageHtml);
        this.scrollToBottom();
    }
    
    addBotTyping() {
        if (!this.chatContainer) return null;
        
        const typingId = `typing-${Date.now()}`;
        const messageHtml = `
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
        
        this.chatContainer.insertAdjacentHTML('beforeend', messageHtml);
        this.scrollToBottom();
        return typingId;
    }
    
    removeBotTyping(typingId) {
        if (typingId) {
            const typingElement = document.getElementById(typingId);
            if (typingElement) {
                typingElement.remove();
            }
        }
    }
    
    // 3D Background initialization
    init3DBackground() {
        // Wait for Three.js to load if not immediately available
        if (!window.THREE) {
            setTimeout(() => {
                if (window.THREE) {
                    this.setupThreeJSScene();
                } else {
                    console.log('Three.js not available, using CSS animations only');
                }
            }, 1000);
            return;
        }
        this.setupThreeJSScene();
    }
    
    setupThreeJSScene() {
        try {
            const canvas = document.getElementById('bg-canvas');
            if (!canvas) {
                console.log('Canvas element not found');
                return;
            }

            this.scene = new THREE.Scene();
            this.camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
            this.renderer = new THREE.WebGLRenderer({ 
                canvas: canvas, 
                alpha: true,
                antialias: true 
            });
            this.renderer.setSize(window.innerWidth, window.innerHeight);
            this.renderer.setClearColor(0x000000, 0);

            this.createFloating3DElements();
            this.camera.position.z = 5;
            this.animate3D();
            
            // Handle window resize
            window.addEventListener('resize', () => this.onWindowResize());
            
        } catch (error) {
            console.log('3D background setup failed, using fallback animations');
            this.initFallbackAnimations();
        }
    }
    
    onWindowResize() {
        if (!this.camera || !this.renderer) return;
        
        this.camera.aspect = window.innerWidth / window.innerHeight;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(window.innerWidth, window.innerHeight);
    }

    onWindowResize() {
        if (!this.camera || !this.renderer) return;
        
        this.camera.aspect = window.innerWidth / window.innerHeight;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(window.innerWidth, window.innerHeight);
    }

    createFloating3DElements() {
        if (!this.scene) return;
        
        this.particles3D = [];
        
        // Create leaf-like geometries with more detail
        const leafGeometry = new THREE.PlaneGeometry(0.4, 0.6);
        const leafMaterial = new THREE.MeshBasicMaterial({ 
            color: 0x10b981, 
            transparent: true,
            opacity: 0.7,
            side: THREE.DoubleSide
        });

        // Create stem/branch geometries
        const stemGeometry = new THREE.CylinderGeometry(0.02, 0.02, 0.8);
        const stemMaterial = new THREE.MeshBasicMaterial({ 
            color: 0x059669, 
            transparent: true,
            opacity: 0.8
        });

        // Create pollen-like spheres
        const pollenGeometry = new THREE.SphereGeometry(0.08, 12, 8);
        const pollenMaterial = new THREE.MeshBasicMaterial({ 
            color: 0x34d399, 
            transparent: true,
            opacity: 0.9
        });

        // Create flower-like geometries
        const flowerGeometry = new THREE.ConeGeometry(0.15, 0.3, 6);
        const flowerMaterial = new THREE.MeshBasicMaterial({ 
            color: 0x50c878, 
            transparent: true,
            opacity: 0.8
        });

        // Add multiple floating botanical elements
        for (let i = 0; i < 25; i++) {
            let mesh, geometry, material;
            
            const elementType = i % 4;
            switch (elementType) {
                case 0: // Leaves
                    mesh = new THREE.Mesh(leafGeometry, leafMaterial);
                    break;
                case 1: // Stems
                    mesh = new THREE.Mesh(stemGeometry, stemMaterial);
                    break;
                case 2: // Pollen
                    mesh = new THREE.Mesh(pollenGeometry, pollenMaterial);
                    break;
                case 3: // Flowers
                    mesh = new THREE.Mesh(flowerGeometry, flowerMaterial);
                    break;
            }
            
            // Random positioning across the screen
            mesh.position.x = (Math.random() - 0.5) * 12;
            mesh.position.y = (Math.random() - 0.5) * 12;
            mesh.position.z = (Math.random() - 0.5) * 6;
            
            // Random initial rotation
            mesh.rotation.x = Math.random() * Math.PI * 2;
            mesh.rotation.y = Math.random() * Math.PI * 2;
            mesh.rotation.z = Math.random() * Math.PI * 2;
            
            // Animation properties
            mesh.rotationSpeed = {
                x: (Math.random() - 0.5) * 0.02,
                y: (Math.random() - 0.5) * 0.02,
                z: (Math.random() - 0.5) * 0.02
            };
            
            // Floating motion parameters
            mesh.floatSpeed = 0.0008 + Math.random() * 0.0012;
            mesh.floatAmplitude = 0.3 + Math.random() * 0.8;
            mesh.timeOffset = Math.random() * Math.PI * 2;
            mesh.driftSpeed = (Math.random() - 0.5) * 0.003;
            
            this.particles3D.push(mesh);
            this.scene.add(mesh);
        }
    }

    animate3D() {
        if (!this.renderer || !this.scene || !this.camera) return;
        
        requestAnimationFrame(() => this.animate3D());
        
        const time = Date.now() * 0.001;
        
        if (this.particles3D && this.particles3D.length > 0) {
            this.particles3D.forEach((particle, index) => {
                // Continuous rotation
                particle.rotation.x += particle.rotationSpeed.x;
                particle.rotation.y += particle.rotationSpeed.y;
                particle.rotation.z += particle.rotationSpeed.z;
                
                // Complex floating motion
                const floatY = Math.sin(time * particle.floatSpeed + particle.timeOffset) * particle.floatAmplitude * 0.02;
                const floatX = Math.cos(time * particle.floatSpeed * 0.7 + particle.timeOffset) * 0.01;
                const floatZ = Math.sin(time * particle.floatSpeed * 0.5 + particle.timeOffset) * 0.008;
                
                particle.position.y += floatY;
                particle.position.x += floatX;
                particle.position.z += floatZ;
                
                // Gentle drift
                particle.position.x += particle.driftSpeed;
                
                // Reset particles that drift too far
                if (particle.position.x > 8) particle.position.x = -8;
                if (particle.position.x < -8) particle.position.x = 8;
                if (particle.position.y > 8) particle.position.y = -8;
                if (particle.position.y < -8) particle.position.y = 8;
                
                // Subtle scaling animation for organic feel
                const scaleVariation = 1 + Math.sin(time * 0.5 + index) * 0.1;
                particle.scale.setScalar(scaleVariation);
            });
        }
        
        // Gentle camera movement
        this.camera.position.x = Math.sin(time * 0.1) * 0.5;
        this.camera.position.y = Math.cos(time * 0.08) * 0.3;
        this.camera.lookAt(0, 0, 0);
        
        this.renderer.render(this.scene, this.camera);
    }
    
    initAnimations() {
        if (!window.gsap) return;
        
        // Enhanced 2D floating animations
        gsap.to('.leaf-particle', {
            y: '+=20px',
            rotation: '+=10deg',
            duration: 4,
            ease: 'power2.inOut',
            stagger: 0.5,
            repeat: -1,
            yoyo: true
        });

        gsap.to('.pollen-particle', {
            y: '+=15px',
            x: '+=10px',
            scale: 1.2,
            duration: 3,
            ease: 'power2.inOut',
            stagger: 0.3,
            repeat: -1,
            yoyo: true
        });
        
        // Avatar glow animation
        gsap.to('.avatar-glow', {
            boxShadow: '0 0 30px rgba(16, 185, 129, 0.6), 0 0 50px rgba(16, 185, 129, 0.4)',
            duration: 2,
            ease: 'power2.inOut',
            repeat: -1,
            yoyo: true
        });
    }
    
    initFallbackAnimations() {
        // Enhanced CSS-only animations when 3D is not available
        if (!window.gsap) return;
        
        // Create additional floating elements
        const container = document.querySelector('.floating-3d-elements');
        if (container) {
            for (let i = 0; i < 10; i++) {
                const particle = document.createElement('div');
                particle.className = 'css-particle';
                particle.style.cssText = `
                    position: absolute;
                    width: ${4 + Math.random() * 8}px;
                    height: ${4 + Math.random() * 8}px;
                    background: radial-gradient(circle, rgba(16, 185, 129, 0.8), rgba(52, 211, 153, 0.4));
                    border-radius: 50%;
                    left: ${Math.random() * 100}%;
                    top: ${Math.random() * 100}%;
                `;
                container.appendChild(particle);
                
                gsap.to(particle, {
                    y: '+=30px',
                    x: '+=20px',
                    scale: 1.5,
                    opacity: 0.3,
                    duration: 6 + Math.random() * 4,
                    ease: 'power2.inOut',
                    repeat: -1,
                    yoyo: true,
                    delay: Math.random() * 2
                });
            }
        }
    }
    
    // Utility method for showing notifications
    showNotification(message, type = 'info') {
        console.log(`${type}: ${message}`);
    }

    // 3D Background initialization
    init3DBackground() {
        if (!window.THREE) return; // Fallback if Three.js doesn't load
        
        try {
            // Scene setup
            this.scene = new THREE.Scene();
            this.camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
            this.renderer = new THREE.WebGLRenderer({ canvas: this.bgCanvas, alpha: true });
            this.renderer.setSize(window.innerWidth, window.innerHeight);
            this.renderer.setClearColor(0x000000, 0);

            // Create floating geometric shapes
            this.createFloatingGeometry();
            
            // Position camera
            this.camera.position.z = 5;
            
            // Start animation loop
            this.animate3D();
        } catch (error) {
            console.log('3D background initialization failed, continuing without 3D effects');
        }
    }

    createFloatingGeometry() {
        const geometries = [
            new THREE.TetrahedronGeometry(0.5),
            new THREE.OctahedronGeometry(0.3),
            new THREE.IcosahedronGeometry(0.4)
        ];
        
        const material = new THREE.MeshBasicMaterial({ 
            color: 0x10b981, 
            wireframe: true,
            transparent: true,
            opacity: 0.3
        });

        for (let i = 0; i < 15; i++) {
            const geometry = geometries[Math.floor(Math.random() * geometries.length)];
            const mesh = new THREE.Mesh(geometry, material);
            
            // Random positioning
            mesh.position.x = (Math.random() - 0.5) * 20;
            mesh.position.y = (Math.random() - 0.5) * 20;
            mesh.position.z = (Math.random() - 0.5) * 10;
            
            // Random rotation speeds
            mesh.rotationSpeed = {
                x: (Math.random() - 0.5) * 0.02,
                y: (Math.random() - 0.5) * 0.02,
                z: (Math.random() - 0.5) * 0.02
            };
            
            this.particles.push(mesh);
            this.scene.add(mesh);
        }
    }

    animate3D() {
        if (!this.renderer) return;
        
        requestAnimationFrame(() => this.animate3D());
        
        // Rotate particles
        this.particles.forEach(particle => {
            particle.rotation.x += particle.rotationSpeed.x;
            particle.rotation.y += particle.rotationSpeed.y;
            particle.rotation.z += particle.rotationSpeed.z;
            
            // Gentle floating motion
            particle.position.y += Math.sin(Date.now() * 0.001 + particle.position.x) * 0.001;
        });
        
        this.renderer.render(this.scene, this.camera);
    }

    onWindowResize() {
        if (!this.camera || !this.renderer) return;
        
        this.camera.aspect = window.innerWidth / window.innerHeight;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(window.innerWidth, window.innerHeight);
    }

    // Animation utilities
    initAnimations() {
        // Stagger animation for floating particles
        gsap.to('.particle', {
            y: '20px',
            duration: 2,
            ease: 'power2.inOut',
            stagger: 0.2,
            repeat: -1,
            yoyo: true
        });

        // Logo 3D rotation enhancement
        gsap.to('.logo-3d', {
            rotationY: 360,
            duration: 10,
            ease: 'none',
            repeat: -1
        });
    }

    setupScrollAnimations() {
        // Smooth reveal animations on scroll
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    gsap.fromTo(entry.target,
                        { opacity: 0, y: 50 },
                        { opacity: 1, y: 0, duration: 0.8, ease: 'power2.out' }
                    );
                }
            });
        }, observerOptions);

        // Observe elements for scroll animations
        document.querySelectorAll('.glass-card').forEach(card => {
            observer.observe(card);
        });
    }

    // Utility method to show toast notifications
    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast-notification toast-${type}`;
        toast.innerHTML = `
            <i class="fas fa-info-circle me-2"></i>
            <span>${message}</span>
        `;
        
        // Add toast styles
        Object.assign(toast.style, {
            position: 'fixed',
            top: '20px',
            right: '20px',
            background: 'rgba(255, 255, 255, 0.1)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255, 255, 255, 0.2)',
            borderRadius: '12px',
            padding: '12px 20px',
            color: 'white',
            zIndex: '10000',
            transform: 'translateX(100%)',
            opacity: '0'
        });
        
        document.body.appendChild(toast);
        
        // Animate in
        gsap.to(toast, {
            x: 0,
            opacity: 1,
            duration: 0.5,
            ease: 'back.out(1.7)'
        });
        
        // Auto remove after 3 seconds
        setTimeout(() => {
            gsap.to(toast, {
                x: '100%',
                opacity: 0,
                duration: 0.3,
                onComplete: () => {
                    if (toast.parentNode) {
                        toast.remove();
                    }
                }
            });
        }, 3000);
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.LumonApp = new LumonApp();
    
    // Smooth page load animation
    gsap.fromTo('.mobile-app', 
        { opacity: 0, scale: 0.95 },
        { opacity: 1, scale: 1, duration: 0.6, ease: 'power2.out' }
    );
    
    // Animate welcome message
    setTimeout(() => {
        gsap.fromTo('#welcome-message',
            { opacity: 0, y: 30 },
            { opacity: 1, y: 0, duration: 0.5, ease: 'back.out(1.7)' }
        );
    }, 300);
    
    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        // Escape to close camera or settings
        if (e.key === 'Escape') {
            if (window.LumonApp.cameraInterface.style.display === 'flex') {
                window.LumonApp.closeCamera();
            }
            if (window.LumonApp.settingsModal.style.display === 'flex') {
                window.LumonApp.closeSettings();
            }
        }
        
        // Space or Enter to open camera
        if ((e.key === ' ' || e.key === 'Enter') && e.target === document.body) {
            e.preventDefault();
            window.LumonApp.openCamera();
        }
    });
    
    // Prevent zoom on double tap
    let lastTouchEnd = 0;
    document.addEventListener('touchend', (e) => {
        const now = (new Date()).getTime();
        if (now - lastTouchEnd <= 300) {
            e.preventDefault();
        }
        lastTouchEnd = now;
    }, false);
    
    // Handle back button for camera
    window.addEventListener('popstate', () => {
        if (window.LumonApp.cameraInterface.style.display === 'flex') {
            window.LumonApp.closeCamera();
        }
    });
});

// Global error handler
window.addEventListener('error', (e) => {
    console.error('Global error:', e.error);
    if (window.LumonApp) {
        window.LumonApp.addBotMessage('Sorry, something went wrong. Please try again.');
    }
});

// Handle online/offline status
window.addEventListener('online', () => {
    if (window.LumonApp) {
        window.LumonApp.showNotification('Connection restored', 'success');
    }
});

window.addEventListener('offline', () => {
    if (window.LumonApp) {
        window.LumonApp.addBotMessage('You appear to be offline. Please check your connection.');
    }
});

// Prevent zoom on inputs
document.addEventListener('gesturestart', (e) => {
    e.preventDefault();
});

// Add visual feedback for touch interactions
document.addEventListener('touchstart', (e) => {
    const target = e.target.closest('button');
    if (target) {
        target.style.transform = 'scale(0.95)';
    }
});

document.addEventListener('touchend', (e) => {
    const target = e.target.closest('button');
    if (target) {
        target.style.transform = '';
    }
});
