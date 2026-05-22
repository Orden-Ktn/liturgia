// Auto-hide alerts after 5 seconds
setTimeout(function() {
    let alerts = document.querySelectorAll('.alert-container');
    alerts.forEach(function(alert) {
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-20px)';
        alert.style.transition = 'all 0.5s cubic-bezier(0.16, 1, 0.3, 1)';
        setTimeout(() => alert.remove(), 500);
    });
}, 5000);

// Password toggle function
function togglePassword(fieldId) {
    const passwordField = document.getElementById(fieldId);
    const toggleIcon = document.getElementById('password-toggle-' + fieldId);
    
    if (passwordField.type === 'password') {
        passwordField.type = 'text';
        toggleIcon.classList.remove('ri-eye-line');
        toggleIcon.classList.add('ri-eye-off-line');
    } else {
        passwordField.type = 'password';
        toggleIcon.classList.remove('ri-eye-off-line');
        toggleIcon.classList.add('ri-eye-line');
    }
}

// Form submission loader
document.getElementById('login-form').addEventListener('submit', function() {
    document.getElementById('loader').style.display = 'flex';
});

document.getElementById('register-form').addEventListener('submit', function() {
    document.getElementById('loader').style.display = 'flex';
});

document.getElementById('profile-form').addEventListener('submit', function() {
    document.getElementById('loader').style.display = 'flex';
});

// Add ripple effect on button click
document.querySelector('.btn-submit').addEventListener('click', function(e) {
    let ripple = document.createElement('span');
    let rect = this.getBoundingClientRect();
    let size = Math.max(rect.width, rect.height);
    let x = e.clientX - rect.left - size / 2;
    let y = e.clientY - rect.top - size / 2;
    
    ripple.style.width = ripple.style.height = size + 'px';
    ripple.style.left = x + 'px';
    ripple.style.top = y + 'px';
    ripple.classList.add('ripple');
    
    this.appendChild(ripple);
    
    setTimeout(() => ripple.remove(), 600);
});