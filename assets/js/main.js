/**
 * Blog runtime.
 *
 * Every behaviour here is driven by markup emitted from _layouts/post.html,
 * _includes/*.html and the tokens in _data/blog_style.yml. If an element is
 * missing the corresponding pass exits quietly, so this file is safe to load
 * on the listing page and on plain pages too.
 */
(function () {
  'use strict';

  var CALLOUT_RE = /^\s*\[!(NOTE|TIP|WARNING|IMPORTANT|CAUTION)\][ \t]*/i;

  function each(list, fn) {
    Array.prototype.forEach.call(list || [], fn);
  }

  function slugify(text) {
    return (text || '')
      .toLowerCase()
      .replace(/[^\w\s-]/g, '')
      .trim()
      .replace(/\s+/g, '-');
  }

  /* ---------------------------------------------------------------------
   * Active nav link
   * ------------------------------------------------------------------- */
  function initActiveNavLink() {
    var base = document.body.getAttribute('data-baseurl') || '';
    var path = window.location.pathname;
    each(document.querySelectorAll('.nav-link'), function (link) {
      var href = link.getAttribute('href');
      if (!href) return;
      if (href === path || (href !== base + '/' && href !== '/' && path.indexOf(href) === 0)) {
        link.classList.add('active');
      }
    });
  }

  /* ---------------------------------------------------------------------
   * Table of contents
   *
   * Fills both the desktop left rail (#toc-list) and the narrow-screen
   * disclosure (#toc-list-mobile) from the same entry list. Heading ids come
   * from kramdown's auto_ids; anything still missing is slugged here with a
   * de-duplicating suffix so deep links are meaningful.
   * ------------------------------------------------------------------- */
  function initToc() {
    var prose = document.getElementById('post-content');
    var widget = document.getElementById('toc-widget');
    var mobile = document.getElementById('toc-mobile');
    if (!prose) return;

    var headings = prose.querySelectorAll('h2, h3');

    if (!headings.length) {
      if (widget) widget.style.display = 'none';
      if (mobile) mobile.style.display = 'none';
      return;
    }

    var used = Object.create(null);
    var entries = [];

    each(headings, function (h) {
      if (!h.id) {
        var base = slugify(h.textContent) || 'section';
        var id = base;
        var n = 2;
        while (used[id]) { id = base + '-' + n; n += 1; }
        h.id = id;
      }
      used[h.id] = true;
      entries.push({ id: h.id, text: h.textContent, level: h.tagName === 'H3' ? 3 : 2 });
    });

    each([document.getElementById('toc-list'), document.getElementById('toc-list-mobile')], function (list) {
      if (!list) return;
      list.textContent = '';
      each(entries, function (entry) {
        var li = document.createElement('li');
        li.className = 'toc-h' + entry.level;
        var a = document.createElement('a');
        a.href = '#' + entry.id;
        a.textContent = entry.text;
        li.appendChild(a);
        list.appendChild(li);
      });
    });

    // Scroll-spy on the desktop rail only; it is the one that stays visible.
    var links = widget ? widget.querySelectorAll('a') : [];
    if (widget && links.length && 'IntersectionObserver' in window) {
      var observer = new IntersectionObserver(function (items) {
        each(items, function (item) {
          if (!item.isIntersecting) return;
          each(links, function (l) { l.classList.remove('active'); });
          var active = widget.querySelector('a[href="#' + item.target.id + '"]');
          if (!active) return;
          active.classList.add('active');
          var top = active.offsetTop;
          if (top > widget.scrollTop + widget.clientHeight - 60 || top < widget.scrollTop + 20) {
            widget.scrollTo({ top: Math.max(0, top - 40), behavior: 'smooth' });
          }
        });
      }, { rootMargin: '-20% 0% -70% 0%' });

      each(headings, function (h) { observer.observe(h); });
    }

    if (mobile) {
      mobile.addEventListener('click', function (e) {
        if (e.target && e.target.tagName === 'A') mobile.open = false;
      });
    }
  }

  /* ---------------------------------------------------------------------
   * Callouts
   *
   * Promotes `> [!NOTE]`-style GitHub Alerts to a styled callout. The marker
   * is stripped from the text, so nothing reads "[!NOTE]" to the visitor.
   * Runs client-side precisely so existing posts need no content edits.
   *
   * Both forms are handled, because both are easy to write and only one used
   * to work. structure.callout_syntax in _data/blog_style.yml documents the
   * marker as `[!NOTE]` without saying it must be inside a blockquote, so a
   * bare paragraph marker used to fall through and ship the literal text
   * "[!IMPORTANT]" to the reader.
   * ------------------------------------------------------------------- */
  function initCallouts() {
    var prose = document.getElementById('post-content');
    if (!prose) return;

    each(prose.querySelectorAll('blockquote'), function (bq) {
      if (bq.classList.contains('callout')) return;

      var walker = document.createTreeWalker(bq, NodeFilter.SHOW_TEXT, null);
      var node = walker.nextNode();
      if (!node) return;

      var match = node.nodeValue.match(CALLOUT_RE);
      if (!match) return;

      node.nodeValue = node.nodeValue.replace(CALLOUT_RE, '');
      bq.classList.add('callout');
      bq.setAttribute('data-callout', match[1].toLowerCase());

      // A marker on its own line leaves an empty paragraph behind.
      var firstPara = bq.querySelector('p');
      if (firstPara && !firstPara.textContent.trim()) firstPara.remove();
    });

    // Bare marker on its own paragraph, with no surrounding blockquote.
    each(prose.querySelectorAll('p'), function (para) {
      if (para.classList.contains('callout')) return;
      if (para.parentNode !== prose) return; // only top-level prose paragraphs

      var paraWalker = document.createTreeWalker(para, NodeFilter.SHOW_TEXT, null);
      var paraNode = paraWalker.nextNode();
      if (!paraNode) return;

      var paraMatch = paraNode.nodeValue.match(CALLOUT_RE);
      if (!paraMatch) return;

      paraNode.nodeValue = paraNode.nodeValue.replace(CALLOUT_RE, '');
      para.classList.add('callout');
      para.setAttribute('data-callout', paraMatch[1].toLowerCase());
    });
  }

  /* ---------------------------------------------------------------------
   * Code boxes
   *
   * Frames each block in a .code-box with a header bar carrying the language
   * on the left and a copy button on the right. Horizontal scrolling moves
   * from the bare <pre> onto .code-box-body so the header stays put.
   * ------------------------------------------------------------------- */
  function initCodeBoxes() {
    var prose = document.getElementById('post-content');
    if (!prose) return;

    var LANG_RE = /language-([\w+#-]+)/;

    function detectLanguage(host, pre) {
      var code = pre.querySelector('code');
      var m = code && code.className ? code.className.match(LANG_RE) : null;
      if (m) return m[1];
      m = pre.className ? pre.className.match(LANG_RE) : null;
      if (m) return m[1];
      if (host.getAttribute('data-lang')) return host.getAttribute('data-lang');
      return '';
    }

    each(prose.querySelectorAll('pre'), function (pre) {
      if (pre.closest('.code-box') || pre.closest('.mermaid')) return;

      var host = pre;
      var parent = pre.parentElement;
      if (parent && (parent.classList.contains('highlight') ||
                     parent.classList.contains('highlighter-rouge') ||
                     parent.classList.contains('codehilite'))) {
        host = parent;
      }
      if (!host.parentNode) return;

      var box = document.createElement('div');
      box.className = 'code-box';

      var head = document.createElement('div');
      head.className = 'code-box-head';

      var label = document.createElement('span');
      label.className = 'code-box-lang';
      label.textContent = detectLanguage(host, pre) || 'code';

      var button = document.createElement('button');
      button.className = 'copy-code-btn';
      button.type = 'button';
      button.setAttribute('data-copy', '');
      button.setAttribute('aria-label', 'Copy code to clipboard');
      button.textContent = 'Copy';

      head.appendChild(label);
      head.appendChild(button);

      var body = document.createElement('div');
      body.className = 'code-box-body';

      host.parentNode.insertBefore(box, host);
      body.appendChild(host);
      box.appendChild(head);
      box.appendChild(body);
    });
  }

  function initCopyButtons() {
    document.addEventListener('click', function (e) {
      var button = e.target.closest ? e.target.closest('[data-copy]') : null;
      if (!button) return;

      var box = button.closest('.code-box');
      var body = box ? box.querySelector('.code-box-body') : null;
      if (!body) return;

      var text = body.innerText.replace(/\n$/, '');

      function done() {
        button.textContent = 'Copied';
        button.classList.add('copied');
        setTimeout(function () {
          button.textContent = 'Copy';
          button.classList.remove('copied');
        }, 1600);
      }

      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done, function () { /* clipboard denied */ });
      }
    });
  }

  /* ---------------------------------------------------------------------
   * Reading progress bar
   *
   * Measures the article body rather than the document, so the bar reaches
   * 100% at the end of the prose instead of at the end of the footer.
   * ------------------------------------------------------------------- */
  function initReadingProgress() {
    var bar = document.getElementById('reading-progress-bar');
    var content = document.getElementById('post-content');
    if (!bar || !content) return;

    function update() {
      var rect = content.getBoundingClientRect();
      var travel = rect.height - window.innerHeight;
      var pct;

      if (rect.bottom <= window.innerHeight) {
        pct = 1;
      } else if (travel <= 0) {
        pct = Math.min(1, Math.max(0, -rect.top / rect.height));
      } else {
        pct = Math.min(1, Math.max(0, -rect.top / travel));
      }

      bar.style.transform = 'scaleX(' + pct + ')';
    }

    update();
    window.addEventListener('scroll', update, { passive: true });
    window.addEventListener('resize', update);
  }

  /* ---------------------------------------------------------------------
   * Share
   * ------------------------------------------------------------------- */
  function initShare() {
    var root = document.querySelector('[data-share]');
    if (!root) return;

    var url = window.location.href.split('#')[0];
    var title = document.title;

    root.addEventListener('click', function (e) {
      var button = e.target.closest ? e.target.closest('[data-share-target]') : null;
      if (!button) return;

      var target = button.getAttribute('data-share-target');

      if (target === 'copy') {
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(url).then(function () {
            var original = button.getAttribute('title');
            button.setAttribute('title', 'Link copied');
            button.classList.add('copied');
            setTimeout(function () {
              button.setAttribute('title', original);
              button.classList.remove('copied');
            }, 1600);
          }, function () { /* clipboard denied */ });
        }
        return;
      }

      var dest;
      if (target === 'x') {
        dest = 'https://x.com/intent/tweet?text=' + encodeURIComponent(title) +
               '&url=' + encodeURIComponent(url);
      } else if (target === 'linkedin') {
        dest = 'https://www.linkedin.com/sharing/share-offsite/?url=' + encodeURIComponent(url);
      } else {
        return;
      }

      window.open(dest, '_blank', 'noopener,width=600,height=500');
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    initActiveNavLink();
    initToc();
    initCallouts();
    initCodeBoxes();
    initCopyButtons();
    initReadingProgress();
    initShare();
  });
})();
