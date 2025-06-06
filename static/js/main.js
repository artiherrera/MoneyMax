// MoneyMax - JavaScript Principal

document.addEventListener('DOMContentLoaded', function() {
    console.log('💰 MoneyMax cargado correctamente');
    
    // Inicializar funciones
    initProductCards();
    initMobileMenu();
});

// Funciones para las cards de productos
function initProductCards() {
    const productCards = document.querySelectorAll('.product-card');
    
    productCards.forEach(card => {
        // Agregar efecto de hover mejorado
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-8px) scale(1.02)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
        
        // Efecto de click
        card.addEventListener('mousedown', function() {
            this.style.transform = 'translateY(-4px) scale(0.98)';
        });
        
        card.addEventListener('mouseup', function() {
            this.style.transform = 'translateY(-8px) scale(1.02)';
        });
    });
}

// Menú móvil (para futuro uso)
function initMobileMenu() {
    const mobileMenuButton = document.getElementById('mobile-menu-button');
    const mobileMenu = document.getElementById('mobile-menu');
    
    if (mobileMenuButton && mobileMenu) {
        mobileMenuButton.addEventListener('click', function() {
            mobileMenu.classList.toggle('hidden');
        });
    }
}

// Función para formatear moneda mexicana
function formatCurrency(amount) {
    return new Intl.NumberFormat('es-MX', {
        style: 'currency',
        currency: 'MXN',
        minimumFractionDigits: 2
    }).format(amount);
}

// Función para formatear porcentajes
function formatPercentage(value, decimals = 2) {
    return (value).toFixed(decimals) + '%';
}

// Función para animaciones suaves al hacer scroll
function smoothScrollTo(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    }
}

// Función para mostrar notificaciones
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    // Estilos básicos
    Object.assign(notification.style, {
        position: 'fixed',
        top: '20px',
        right: '20px',
        padding: '1rem 1.5rem',
        borderRadius: '8px',
        color: 'white',
        fontWeight: '500',
        zIndex: '9999',
        transform: 'translateX(100%)',
        transition: 'transform 0.3s ease'
    });
    
    // Colores según tipo
    switch(type) {
        case 'success':
            notification.style.background = '#48bb78';
            break;
        case 'error':
            notification.style.background = '#f56565';
            break;
        case 'warning':
            notification.style.background = '#ed8936';
            break;
        default:
            notification.style.background = '#4299e1';
    }
    
    document.body.appendChild(notification);
    
    // Animar entrada
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 100);
    
    // Remover después de 3 segundos
    setTimeout(() => {
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

// Función para validar formularios
function validateForm(formData) {
    const errors = [];
    
    // Validar monto
    if (!formData.monto || formData.monto <= 0) {
        errors.push('El monto debe ser mayor a cero');
    } else if (formData.monto < 100) {
        errors.push('El monto mínimo es $100 MXN');
    } else if (formData.monto > 50000000) {
        errors.push('El monto máximo es $50,000,000 MXN');
    }
    
    // Validar plazo
    if (!formData.plazo || formData.plazo <= 0) {
        errors.push('Debe seleccionar un plazo válido');
    }
    
    return {
        isValid: errors.length === 0,
        errors: errors
    };
}

// Función para hacer requests AJAX
async function makeRequest(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error en request:', error);
        showNotification('Error de conexión', 'error');
        throw error;
    }
}

// Funciones para cálculos (se usarán en calculator.html)
window.MoneyMaxUtils = {
    formatCurrency,
    formatPercentage,
    smoothScrollTo,
    showNotification,
    validateForm,
    makeRequest
};