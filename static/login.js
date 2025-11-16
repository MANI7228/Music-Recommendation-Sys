const form = document.querySelector(".login-form");
const lever = document.querySelector(".lever");
const robotHand = document.querySelector(".robot-hand");

form.addEventListener("submit", () => {
  // Lever animation
  lever.style.transform = "rotate(45deg)";
  setTimeout(() => {
    lever.style.transform = "rotate(0deg)";
  }, 1000);

  // Robot hand animation
  robotHand.style.right = "10px";
  setTimeout(() => {
    robotHand.style.right = "-40px";
  }, 1200);
});
