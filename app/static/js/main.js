// CineVault global frontend behaviour: navbar shadow on scroll + toast auto-dismiss.

document.addEventListener("DOMContentLoaded", () => {
  const navbar = document.getElementById("mainNavbar");
  if (navbar) {
    const onScroll = () => {
      if (window.scrollY > 40) {
        navbar.style.backgroundColor = "rgba(10,10,15,0.97)";
      } else {
        navbar.style.background = "linear-gradient(180deg, rgba(10,10,15,0.95) 0%, rgba(10,10,15,0.4) 100%)";
      }
    };
    window.addEventListener("scroll", onScroll);
    onScroll();
  }

  document.querySelectorAll(".cv-toast").forEach((toastEl) => {
    setTimeout(() => {
      toastEl.classList.remove("show");
      toastEl.remove();
    }, 4500);
  });
});
