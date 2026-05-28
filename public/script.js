// script.js – optional interactivity

document.addEventListener('DOMContentLoaded', () => {
  const btn = document.getElementById('btn-participar');

  btn.addEventListener('click', () => {
    btn.textContent = 'Registered! 🎉';
    btn.style.backgroundColor = '#00c170';
    btn.style.color = '#fff';
    btn.disabled = true;
  });
});
