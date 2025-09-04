document.getElementById("togglePassword").addEventListener("click", function() {
    let passwordField = document.getElementById("password");
    if (passwordField.type === "password") {
        passwordField.type = "text";
        this.innerText = "";
    } else {
        passwordField.type = "password";
        this.innerText = "";
    }
});

function validatePassword() {
    let password = document.getElementById("password").value;
    let passwordError = document.getElementById("passwordError");
    let strengthLabel = document.getElementById("strengthLabel");
    let strengthBar = document.getElementById("strengthBar");

    let hasLetter = /[A-Za-z]/.test(password);
    let hasDigit = /\d/.test(password);
    let hasSpecial = /[@$!%*?&]/.test(password);
    let isValidLength = password.length >= 8;

    let errorMessage = "";
    let strength = 0;

    if (!isValidLength) {
        errorMessage += "⚠ At least 8 characters required. ";
    } else {
        strength += 1;
    }
    if (!hasLetter) {
        errorMessage += "⚠ Must include at least one letter. ";
    } else {
        strength += 1;
    }
    if (!hasDigit) {
        errorMessage += "⚠ Must include at least one number. ";
    } else {
        strength += 1;
    }
    if (!hasSpecial) {
        errorMessage += "⚠ Must include at least one special symbol (@$!%*?&). ";
    } else {
        strength += 1;
    }

    passwordError.innerText = errorMessage;

    let strengthPercent = (strength / 4) * 100;
    strengthBar.style.width = strengthPercent + "%";

    if (strength === 0) {
        strengthBar.style.backgroundColor = "red";
        strengthLabel.innerText = "Weak";
    }
    else if (strength === 1) {
        strengthBar.style.backgroundColor = "red";
        strengthLabel.innerText = "Weak";
    } else if (strength === 2) {
        strengthBar.style.backgroundColor = "orange";
        strengthLabel.innerText = "Medium";
    } else if (strength >= 3) {
        strengthBar.style.backgroundColor = "green";
        strengthLabel.innerText = "Strong";
    }
}

function validateAge() {
    let age = document.getElementById("age").value;
    let ageError = document.getElementById("ageError");

    if (age < 0) {
        ageError.innerText = "⚠ Age cannot be negative!";
    } else {
        ageError.innerText = "";
    }
}