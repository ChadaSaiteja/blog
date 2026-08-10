document.addEventListener('DOMContentLoaded', () => {
  initActiveNavLink();
  initReadingTime();
  initTableOfContents();
  initCopyCodeButtons();
});

function initActiveNavLink() {
  const currentPath = window.location.pathname;
  const navLinks = document.querySelectorAll('.nav-link');
  navLinks.forEach(link => {
    const href = link.getAttribute('href');
    if (href === currentPath || (href !== '/' && currentPath.startsWith(href))) {
      link.classList.add('active');
    }
  });
}

function initReadingTime() {
  const placeholder = document.getElementById('reading-time-placeholder');
  const postContent = document.getElementById('post-content');
  
  if (placeholder && postContent) {
    const text = postContent.innerText || postContent.textContent;
    const wordCount = text.trim().split(/\s+/).filter(w => w.length > 0).length;
    const wordsPerMinute = 200;
    const readingTime = Math.ceil(wordCount / wordsPerMinute);
    placeholder.innerText = `${readingTime} min read`;
  }
}

function initTableOfContents() {
  const tocContainer = document.getElementById('toc-container');
  const toc = document.getElementById('toc');
  const postContent = document.getElementById('post-content');
  
  if (!tocContainer || !toc || !postContent) return;

  const headings = postContent.querySelectorAll('h2, h3');
  if (headings.length === 0) {
    tocContainer.style.display = 'none';
    return;
  }

  tocContainer.style.display = 'block';
  const ul = document.createElement('ul');
  
  headings.forEach((heading, idx) => {
    if (!heading.id) {
      heading.id = heading.innerText
        .toLowerCase()
        .replace(/[^\w\s-]/g, '')
        .replace(/\s+/g, '-');
      if (document.querySelectorAll(`#${heading.id}`).length > 1) {
        heading.id += `-${idx}`;
      }
    }

    const li = document.createElement('li');
    li.classList.add(`toc-${heading.tagName.toLowerCase()}`);

    const a = document.createElement('a');
    a.href = `#${heading.id}`;
    a.textContent = heading.innerText;
    
    a.addEventListener('click', (e) => {
      e.preventDefault();
      document.getElementById(heading.id).scrollIntoView({
        behavior: 'smooth'
      });
      window.history.pushState(null, null, `#${heading.id}`);
    });

    li.appendChild(a);
    ul.appendChild(li);
  });

  toc.appendChild(ul);

  const tocLinks = toc.querySelectorAll('a');
  const observerOptions = {
    root: null,
    rootMargin: '0px 0px -60% 0px',
    threshold: 0
  };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const id = entry.target.getAttribute('id');
        tocLinks.forEach(link => {
          if (link.getAttribute('href') === `#${id}`) {
            link.classList.add('active');
          } else {
            link.classList.remove('active');
          }
        });
      }
    });
  }, observerOptions);

  headings.forEach(heading => observer.observe(heading));
}

function initCopyCodeButtons() {
  const blocks = document.querySelectorAll('.highlight');
  
  blocks.forEach(block => {
    const pre = block.querySelector('pre');
    if (!pre) return;

    const btn = document.createElement('button');
    btn.className = 'copy-code-btn';
    btn.textContent = 'Copy';
    
    btn.addEventListener('click', async () => {
      const codeText = pre.innerText || pre.textContent;
      try {
        await navigator.clipboard.writeText(codeText);
        btn.textContent = 'Copied!';
        btn.style.backgroundColor = 'rgba(56, 189, 248, 0.2)';
        btn.style.borderColor = 'rgba(56, 189, 248, 0.4)';
        setTimeout(() => {
          btn.textContent = 'Copy';
          btn.style.backgroundColor = '';
          btn.style.borderColor = '';
        }, 2000);
      } catch (err) {
        btn.textContent = 'Error';
      }
    });

    block.appendChild(btn);
  });
}
