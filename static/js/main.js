/* PhotoMarket - Main JavaScript */

document.addEventListener('DOMContentLoaded', function() {
    
    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            bsAlert.close();
        }, 5000);
    });
    
    // Tooltip initialization
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltipTriggerList.forEach(function(tooltipTriggerEl) {
        new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Popover initialization
    const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]');
    popoverTriggerList.forEach(function(popoverTriggerEl) {
        new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Image preview on file input
    const imageInputs = document.querySelectorAll('input[type="file"][accept*="image"]');
    imageInputs.forEach(function(input) {
        input.addEventListener('change', function(e) {
            const preview = document.querySelector(input.dataset.preview);
            if (preview && this.files && this.files[0]) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    preview.src = e.target.result;
                };
                reader.readAsDataURL(this.files[0]);
            }
        });
    });
    
    // Lazy loading for images
    if ('IntersectionObserver' in window) {
        const lazyImages = document.querySelectorAll('img[data-src]');
        const imageObserver = new IntersectionObserver(function(entries, observer) {
            entries.forEach(function(entry) {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.removeAttribute('data-src');
                    imageObserver.unobserve(img);
                }
            });
        });
        
        lazyImages.forEach(function(img) {
            imageObserver.observe(img);
        });
    }
    
    // Form validation
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
    
    // Loading button state
    const loadingButtons = document.querySelectorAll('button[data-loading-text]');
    loadingButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            if (!button.disabled) {
                const originalText = button.innerHTML;
                button.innerHTML = button.dataset.loadingText || '<span class="loading"></span>';
                button.disabled = true;
                
                // Re-enable after timeout (fallback)
                setTimeout(function() {
                    button.innerHTML = originalText;
                    button.disabled = false;
                }, 30000);
            }
        });
    });
    
    // Confirm dialogs
    const confirmLinks = document.querySelectorAll('[data-confirm]');
    confirmLinks.forEach(function(link) {
        link.addEventListener('click', function(e) {
            if (!confirm(this.dataset.confirm)) {
                e.preventDefault();
            }
        });
    });
    
    // Price formatting
    const priceInputs = document.querySelectorAll('input[data-type="price"]');
    priceInputs.forEach(function(input) {
        input.addEventListener('blur', function() {
            let value = parseFloat(this.value);
            if (!isNaN(value)) {
                this.value = value.toFixed(2);
            }
        });
    });
    
    // Phone number formatting
    const phoneInputs = document.querySelectorAll('input[type="tel"], input[name="phone"]');
    phoneInputs.forEach(function(input) {
        input.addEventListener('input', function() {
            let value = this.value.replace(/\D/g, '');
            if (value.length > 0) {
                if (value[0] === '7' || value[0] === '8') {
                    value = value.substring(1);
                }
                let formatted = '+7';
                if (value.length > 0) formatted += ' (' + value.substring(0, 3);
                if (value.length >= 3) formatted += ') ' + value.substring(3, 6);
                if (value.length >= 6) formatted += '-' + value.substring(6, 8);
                if (value.length >= 8) formatted += '-' + value.substring(8, 10);
                this.value = formatted;
            }
        });
    });
    
    // Bank card formatting
    const cardInputs = document.querySelectorAll('input[name="bank_card"]');
    cardInputs.forEach(function(input) {
        input.addEventListener('input', function() {
            let value = this.value.replace(/\D/g, '');
            let formatted = '';
            for (let i = 0; i < value.length && i < 16; i++) {
                if (i > 0 && i % 4 === 0) {
                    formatted += ' ';
                }
                formatted += value[i];
            }
            this.value = formatted;
        });
    });
    
    // Copy to clipboard
    const copyButtons = document.querySelectorAll('[data-copy]');
    copyButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            const text = this.dataset.copy;
            navigator.clipboard.writeText(text).then(function() {
                const originalText = button.innerHTML;
                button.innerHTML = '<i class="bi bi-check"></i> Скопировано';
                setTimeout(function() {
                    button.innerHTML = originalText;
                }, 2000);
            });
        });
    });
    
    // Selfie status check (for clients)
    const selfieStatusEl = document.getElementById('selfie-status');
    if (selfieStatusEl) {
        checkSelfieStatus();
        setInterval(checkSelfieStatus, 5000);
    }
    
    function checkSelfieStatus() {
        fetch('/api/recognition/selfie-status/')
            .then(response => response.json())
            .then(data => {
                if (data.processed) {
                    selfieStatusEl.innerHTML = '<i class="bi bi-check-circle text-success"></i> Лицо распознано';
                    selfieStatusEl.classList.remove('text-warning');
                    selfieStatusEl.classList.add('text-success');
                } else if (data.error) {
                    selfieStatusEl.innerHTML = '<i class="bi bi-exclamation-circle text-danger"></i> ' + data.error;
                } else if (data.has_selfie) {
                    selfieStatusEl.innerHTML = '<i class="bi bi-hourglass-split text-warning"></i> Обрабатывается...';
                }
            })
            .catch(err => console.error('Error checking selfie status:', err));
    }
    
    // Infinite scroll for photo galleries (optional)
    const infiniteScrollContainer = document.querySelector('[data-infinite-scroll]');
    if (infiniteScrollContainer) {
        let loading = false;
        let page = 1;
        
        window.addEventListener('scroll', function() {
            if (loading) return;
            
            const scrollHeight = document.documentElement.scrollHeight;
            const scrollTop = document.documentElement.scrollTop;
            const clientHeight = document.documentElement.clientHeight;
            
            if (scrollTop + clientHeight >= scrollHeight - 500) {
                loading = true;
                page++;
                
                const url = new URL(window.location.href);
                url.searchParams.set('page', page);
                
                fetch(url.toString(), { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
                    .then(response => response.text())
                    .then(html => {
                        if (html.trim()) {
                            infiniteScrollContainer.insertAdjacentHTML('beforeend', html);
                            loading = false;
                        }
                    })
                    .catch(err => {
                        console.error('Error loading more photos:', err);
                        loading = false;
                    });
            }
        });
    }
});

// Camera capture for selfie
function initCameraCapture(videoId, canvasId, inputId) {
    const video = document.getElementById(videoId);
    const canvas = document.getElementById(canvasId);
    const input = document.getElementById(inputId);
    
    if (!video || !canvas) return;
    
    navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' } })
        .then(function(stream) {
            video.srcObject = stream;
            video.play();
        })
        .catch(function(err) {
            console.error('Camera access denied:', err);
        });
    
    window.capturePhoto = function() {
        const context = canvas.getContext('2d');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        context.drawImage(video, 0, 0);
        
        canvas.toBlob(function(blob) {
            const file = new File([blob], 'selfie.jpg', { type: 'image/jpeg' });
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(file);
            input.files = dataTransfer.files;
            
            // Trigger change event
            input.dispatchEvent(new Event('change', { bubbles: true }));
        }, 'image/jpeg', 0.9);
    };
}

// Lightbox for photo viewing
function openLightbox(imageUrl) {
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.innerHTML = `
        <div class="modal-dialog modal-xl modal-dialog-centered">
            <div class="modal-content bg-transparent border-0">
                <div class="text-end p-2">
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body p-0 text-center">
                    <img src="${imageUrl}" class="img-fluid" style="max-height: 90vh;">
                </div>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
    
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
    
    modal.addEventListener('hidden.bs.modal', function() {
        modal.remove();
    });
}
