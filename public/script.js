// script.js – optional interactivity

document.addEventListener('DOMContentLoaded', () => {
  const btn = document.getElementById('btn-participar');

  btn.addEventListener('click', () => {
    btn.textContent = '¡Registrado! 🎉';
    btn.style.backgroundColor = '#00c170';
    btn.style.color = '#fff';
    btn.disabled = true;
  });
});
