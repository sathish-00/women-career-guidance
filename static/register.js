document.addEventListener('DOMContentLoaded', () => {
    // Password Strength Validation
    const passwordInput = document.getElementById('password');
    const strengthBar = document.getElementById('strengthBar');
    const strengthMeter = document.getElementById('strengthMeter');
    const strengthLabel = document.getElementById('strengthLabel');
    const passwordError = document.getElementById('passwordError');
    const togglePassword = document.getElementById('togglePassword');

    const validatePassword = () => {
        const password = passwordInput.value;
        let strength = 0;
        let feedback = '';
        let valid = true;
        
        // At least 8 characters required
        if (password.length >= 8) {
            strength += 1;
        } else {
            feedback = 'At least 8 characters required.';
            valid = false;
        }

        // Must include at least one letter
        if (password.match(/[a-zA-Z]/)) {
            strength += 1;
        } else {
            if (valid) feedback = 'Must include at least one letter.';
            valid = false;
        }

        // Must include at least one number
        if (password.match(/[0-9]/)) {
            strength += 1;
        } else {
            if (valid) feedback = 'Must include at least one number.';
            valid = false;
        }

        // Must include at least one special character
        if (password.match(/[^a-zA-Z0-9]/)) {
            strength += 1;
        } else {
            if (valid) feedback = 'Must include at least one special symbol (@$!%*?&).';
            valid = false;
        }
        
        // Update strength meter and label
        let width = (strength / 4) * 100;
        strengthBar.style.width = width + '%';

        strengthMeter.className = 'strength-meter';
        if (strength === 0) {
            strengthLabel.textContent = 'Weak';
        } else if (strength === 1 || strength === 2) {
            strengthLabel.textContent = 'Medium';
            strengthMeter.classList.add('medium');
        } else {
            strengthLabel.textContent = 'Strong';
            strengthMeter.classList.add('strong');
        }
        
        passwordError.textContent = feedback;
    };

    passwordInput.addEventListener('input', validatePassword);
    
    // Toggle Password Visibility
    togglePassword.addEventListener('click', () => {
        const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
        passwordInput.setAttribute('type', type);
        togglePassword.classList.toggle('hidden');
    });

    // Age Validation
    const ageInput = document.getElementById('age');
    const ageError = document.getElementById('ageError');

    const validateAge = () => {
        const age = parseInt(ageInput.value, 10);
        let feedback = '';

        if (age < 0) {
            feedback = 'Age cannot be a negative number.';
        } else if (isNaN(age) || age === 0) {
            feedback = 'Please enter a valid age.';
        }
        ageError.textContent = feedback;
    };

    ageInput.addEventListener('input', validateAge);

    // Initial validation on page load
    validatePassword();
    validateAge();
});