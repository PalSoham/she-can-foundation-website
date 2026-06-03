document.addEventListener("DOMContentLoaded", () => {
    // Theme Toggling Logic
    const body = document.body;
    const themeToggleBtn = document.getElementById("theme-toggle");
    
    // Check saved theme or default to light
    const savedTheme = localStorage.getItem("theme") || "light";
    if (savedTheme === "dark") {
        body.classList.remove("light-mode");
        body.classList.add("dark-mode");
        themeToggleBtn.textContent = "[ Light Mode ]";
    } else {
        body.classList.remove("dark-mode");
        body.classList.add("light-mode");
        themeToggleBtn.textContent = "[ Dark Mode ]";
    }

    themeToggleBtn.addEventListener("click", () => {
        if (body.classList.contains("light-mode")) {
            body.classList.remove("light-mode");
            body.classList.add("dark-mode");
            themeToggleBtn.textContent = "[ Light Mode ]";
            localStorage.setItem("theme", "dark");
        } else {
            body.classList.remove("dark-mode");
            body.classList.add("light-mode");
            themeToggleBtn.textContent = "[ Dark Mode ]";
            localStorage.setItem("theme", "light");
        }
    });

    // Form Handling Logic
    const contactForm = document.getElementById("contact-form");
    const nameInput = document.getElementById("name");
    const emailInput = document.getElementById("email");
    const messageInput = document.getElementById("message");
    
    const nameError = document.getElementById("name-error");
    const emailError = document.getElementById("email-error");
    const messageError = document.getElementById("message-error");
    
    const formSuccess = document.getElementById("form-success");
    const formErrorGeneral = document.getElementById("form-error-general");
    const errorGeneralText = document.getElementById("error-general-text");
    
    const submitBtn = document.getElementById("submit-btn");
    const submitBtnText = document.getElementById("submit-btn-text");
    const submitLoader = document.getElementById("submit-loader");

    contactForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        
        // Reset feedback states
        clearErrors();
        formSuccess.classList.add("hidden");
        formErrorGeneral.classList.add("hidden");
        
        // Client-side Validation
        let isValid = true;
        
        const nameVal = nameInput.value.trim();
        const emailVal = emailInput.value.trim();
        const messageVal = messageInput.value.trim();
        
        // Validate Name
        if (!nameVal) {
            showFieldError(nameInput, nameError, "Name is required.");
            isValid = false;
        } else if (nameVal.length < 2) {
            showFieldError(nameInput, nameError, "Name must be at least 2 characters.");
            isValid = false;
        }
        
        // Validate Email
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailVal) {
            showFieldError(emailInput, emailError, "Email is required.");
            isValid = false;
        } else if (!emailRegex.test(emailVal)) {
            showFieldError(emailInput, emailError, "Please enter a valid email address.");
            isValid = false;
        }
        
        // Validate Message
        if (!messageVal) {
            showFieldError(messageInput, messageError, "Message is required.");
            isValid = false;
        } else if (messageVal.length < 10) {
            showFieldError(messageInput, messageError, "Message must be at least 10 characters.");
            isValid = false;
        }
        
        if (!isValid) return;
        
        // Set loading state
        setLoading(true);
        
        try {
            const response = await fetch("/api/submit", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    name: nameVal,
                    email: emailVal,
                    message: messageVal
                })
            });
            
            const result = await response.json();
            
            if (response.ok && result.success) {
                // Success
                formSuccess.classList.remove("hidden");
                contactForm.reset();
                // Smooth scroll to top of form section so they see the success message
                document.getElementById("contact").scrollIntoView({ behavior: 'smooth' });
            } else {
                // Server validation failed or other errors
                if (result.errors) {
                    if (result.errors.name) showFieldError(nameInput, nameError, result.errors.name);
                    if (result.errors.email) showFieldError(emailInput, emailError, result.errors.email);
                    if (result.errors.message) showFieldError(messageInput, messageError, result.errors.message);
                } else {
                    errorGeneralText.textContent = result.error || "Form submission failed. Please try again.";
                    formErrorGeneral.classList.remove("hidden");
                }
            }
        } catch (error) {
            errorGeneralText.textContent = "Network error. Please make sure the server is running and try again.";
            formErrorGeneral.classList.remove("hidden");
        } finally {
            setLoading(false);
        }
    });

    // Helper functions for validation
    function showFieldError(inputElement, errorElement, message) {
        inputElement.parentElement.classList.add("invalid");
        errorElement.textContent = message;
    }

    function clearErrors() {
        const groups = document.querySelectorAll(".form-group");
        groups.forEach(group => group.classList.remove("invalid"));
        
        const errors = document.querySelectorAll(".error-msg");
        errors.forEach(err => err.textContent = "");
    }

    function setLoading(isLoading) {
        if (isLoading) {
            submitBtn.disabled = true;
            submitBtnText.textContent = "Submitting Message";
            submitLoader.classList.remove("hidden");
        } else {
            submitBtn.disabled = false;
            submitBtnText.textContent = "Submit Message";
            submitLoader.classList.add("hidden");
        }
    }
});
