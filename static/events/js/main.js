document.addEventListener("DOMContentLoaded", () => {
    const alerts = document.querySelectorAll(".alert");
    alerts.forEach((alert) => {
        if (window.bootstrap && alert.classList.contains("alert-dismissible")) {
            new bootstrap.Alert(alert);
        }
    });
});
