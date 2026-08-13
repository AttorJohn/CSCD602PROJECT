document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("form").forEach((form) => {
    form.addEventListener("submit", (event) => {
      if (form.dataset.confirm && !window.confirm(form.dataset.confirm)) {
        event.preventDefault();
        return;
      }

      const submitButton = form.querySelector("button[type='submit']");
      if (submitButton && submitButton.dataset.submitLabel) {
        submitButton.disabled = true;
        submitButton.textContent = submitButton.dataset.submitLabel || "Working…";
      }
    });
  });
});
