function showError(message) {
    const errorDiv = document.getElementById('error');
    const successDiv = document.getElementById('success');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
    successDiv.style.display = 'none';
}

function showSuccess(message) {
    const errorDiv = document.getElementById('error');
    const successDiv = document.getElementById('success');
    successDiv.textContent = message;
    successDiv.style.display = 'block';
    errorDiv.style.display = 'none';
}

function hideMessages() {
    document.getElementById('error').style.display = 'none';
    document.getElementById('success').style.display = 'none';
}


document.addEventListener('DOMContentLoaded', function() {
    // Login form handler
    document.getElementById('loginForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        hideMessages();
        
        const formData = new FormData(e.target);
        
        try {
            const response = await fetch('/auth/login', {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                window.location.href = '/chatbot';
            } else {
                const error = await response.text();
                showError(error || 'Login failed');
            }
        } catch (error) {
            showError('Network error. Please try again.');
        }
    });
});
