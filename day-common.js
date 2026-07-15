/* TrustForge 開發記錄 — 每篇日誌的通用行為(客戶端,無後端):
   - 上一篇/下一篇 時間軸導覽
   - 文內目錄(TOC,由 <h3> 生成)
   - 相關文章(依共用標籤)
   資料全部來自 entries.json,故新增日誌時本檔自動適用,不必改 22 篇舊頁。 */
(function () {
  const file = location.pathname.split('/').pop();
  const SITE = 'https://cancleeric.github.io/trustforge-devlog';

  function navBar(prev, next) {
    const a = (e, label, dir) => e
      ? `<a class="dn-nav ${dir}" href="${e.file}"><span class="dn-dir">${dir === 'prev' ? '←' : '→'}</span><span class="dn-t">${label}<br><b>${e.title.replace(/^Day \d+[ ·—-]*/, '')}</b></span></a>`
      : '';
    return `<nav class="dn-navbar">${a(prev, '較新一篇', 'prev')}${a(next, '較舊一篇', 'next')}</nav>`;
  }

  function toc(article) {
    const hs = [...article.querySelectorAll('h3')];
    if (hs.length < 2) return '';
    let n = 0;
    const items = hs.map(h => {
      const id = 's' + (++n);
      h.id = id;
      return `<li><a href="#${id}">${h.textContent}</a></li>`;
    }).join('');
    return `<details class="toc" open><summary>本文目錄</summary><ol>${items}</ol></details>`;
  }

  function related(list, cur) {
    const tags = new Set(cur.tags || []);
    if (!tags.size) return '';
    const rel = list.filter(e => e.file !== cur.file && (e.tags || []).some(t => tags.has(t))).slice(0, 5);
    if (!rel.length) return '';
    const items = rel.map(e => `<li><a href="${e.file}">${e.title}</a> <span class="dn-cat">${e.category || ''}</span></li>`).join('');
    return `<section class="dn-related"><h3>相關文章（共用標籤）</h3><ul>${items}</ul></section>`;
  }

  fetch('../entries.json?_=' + Date.now()).then(r => r.json()).then(data => {
    const list = data.entries || [];
    const i = list.findIndex(e => e.file === file);
    if (i < 0) return;
    const cur = list[i];
    const prev = i > 0 ? list[i - 1] : null;        // 較新
    const next = i < list.length - 1 ? list[i + 1] : null; // 較舊

    const wrap = document.querySelector('.wrap');
    const back = document.querySelector('.back');
    if (back && (prev || next)) back.insertAdjacentHTML('afterend', navBar(prev, next));

    const article = document.querySelector('article');
    const h2 = article.querySelector('h2');
    if (h2) h2.insertAdjacentHTML('afterend', toc(article));
    article.insertAdjacentHTML('beforeend', related(list, cur));

    const footer = document.querySelector('footer');
    if (footer && (prev || next)) footer.insertAdjacentHTML('beforebegin', navBar(prev, next));
  }).catch(() => {});
})();
