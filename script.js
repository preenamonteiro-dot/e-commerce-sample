document.addEventListener("DOMContentLoaded", function () {
    console.log("E-Commerce website loaded successfully.");

    const buttons = document.querySelectorAll(".btn, button");

    buttons.forEach(function (button) {
        button.addEventListener("click", function () {
            console.log("Button clicked:", button.textContent);
        });
    });
});