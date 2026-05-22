// Add smooth scroll behavior
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({ behavior: 'smooth' });
        }
    });
});

// Add parallax effect to background pattern
let scrollY = 0;
window.addEventListener('scroll', () => {
    scrollY = window.scrollY;
    document.querySelector('.background-pattern').style.transform = 
        `translate(${scrollY * 0.05}px, ${scrollY * 0.05}px)`;
});

const quotes = [
  "La prière, c'est le souffle de l'âme. Sans elle, on étouffe.",
  "Je ne promets pas de vous rendre heureux en ce monde, mais dans l'autre.",
  "L'humilité, c'est la vérité. Et la vérité, c'est que tout vient de Dieu.",
  "Confions-nous à la Vierge Marie, elle ne laisse jamais sans réponse ceux qui s'adressent à elle.",
  "Ma tâche est de vous le dire, la vôtre de le croire."
];

let cur = 0;
const qt = document.getElementById('quote-text');
const dotsEl = document.getElementById('quote-dots');

function showQuote(i) {
  cur = i;
  qt.style.opacity = 0;
  setTimeout(() => { qt.textContent = quotes[i]; qt.style.opacity = 1; }, 220);
  dotsEl.querySelectorAll('.dot').forEach((d, j) => d.classList.toggle('active', j === i));
}

quotes.forEach((_, i) => {
  const d = document.createElement('div');
  d.className = 'dot' + (i === 0 ? ' active' : '');
  d.onclick = () => { clearInterval(timer); showQuote(i); timer = setInterval(next, 5000); };
  dotsEl.appendChild(d);
});

const next = () => showQuote((cur + 1) % quotes.length);
showQuote(0);
let timer = setInterval(next, 5000);