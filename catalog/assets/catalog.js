(() => {
  const grid = document.querySelector('#project-grid');
  const filters = document.querySelector('#filters');
  const search = document.querySelector('#search');
  const count = document.querySelector('#project-count');
  const resultsNote = document.querySelector('#results-note');
  const emptyState = document.querySelector('#empty-state');
  const emptyTitle = document.querySelector('#empty-title');
  const emptyDescription = document.querySelector('#empty-description');
  const loadError = document.querySelector('#load-error');
  const template = document.querySelector('#project-card-template');

  let projects = [];
  let category = 'all';

  const text = (value) => typeof value === 'string' ? value.trim() : '';
  const pad = (value) => String(value).padStart(2, '0');

  function makeFilter(label, value, active = false) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = `filter${active ? ' is-active' : ''}`;
    button.dataset.category = value;
    button.setAttribute('aria-pressed', String(active));
    button.textContent = label;
    button.addEventListener('click', () => {
      category = value;
      filters.querySelectorAll('.filter').forEach((item) => {
        const selected = item.dataset.category === category;
        item.classList.toggle('is-active', selected);
        item.setAttribute('aria-pressed', String(selected));
      });
      render();
    });
    return button;
  }

  function buildFilters() {
    filters.replaceChildren(makeFilter('全部', 'all', true));
    const categories = [...new Set(projects.map((project) => text(project.category)).filter(Boolean))]
      .sort((a, b) => a.localeCompare(b, 'zh-CN'));
    categories.forEach((name) => filters.append(makeFilter(name, name)));
  }

  function safeLocalPath(value) {
    const path = text(value);
    if (!path || path.startsWith('//') || /^[a-z][a-z\d+.-]*:/i.test(path)) return '';
    const parts = path.replaceAll('\\', '/').split('/');
    if (parts.includes('..')) return '';
    return path;
  }

  function createCard(project) {
    const card = template.content.firstElementChild.cloneNode(true);
    const link = card.querySelector('.project-card__link');
    const href = safeLocalPath(project.href);
    link.href = href || '#';
    if (!href) {
      link.removeAttribute('href');
      link.setAttribute('aria-disabled', 'true');
    }

    const title = text(project.title) || '未命名项目';
    const cover = safeLocalPath(project.cover);
    const image = card.querySelector('.project-card__cover');
    if (cover) {
      image.src = cover;
      image.alt = `${title}全景项目封面`;
      image.addEventListener('load', () => image.parentElement.classList.add('has-cover'), { once: true });
      image.addEventListener('error', () => image.removeAttribute('src'), { once: true });
    } else {
      image.remove();
    }

    card.querySelector('.project-card__category').textContent = text(project.category) || '全景项目';
    card.querySelector('.project-card__location').textContent = text(project.location);
    card.querySelector('.project-card__title').textContent = title;
    card.querySelector('.project-card__year').textContent = project.year ? String(project.year) : '';
    card.querySelector('.project-card__description').textContent = text(project.description);
    const scenes = Number(project.scenes);
    card.querySelector('.project-card__scenes').textContent = Number.isFinite(scenes) && scenes > 0 ? `${scenes} 个空间` : '全景漫游';
    if (!href) card.querySelector('.project-card__enter').textContent = '网页待添加';
    return card;
  }

  function render() {
    const query = text(search.value).toLocaleLowerCase('zh-CN');
    const visible = projects.filter((project) => {
      const matchesCategory = category === 'all' || text(project.category) === category;
      const haystack = [project.title, project.location, project.category, project.description, ...(Array.isArray(project.tags) ? project.tags : [])]
        .map(text).join(' ').toLocaleLowerCase('zh-CN');
      return matchesCategory && (!query || haystack.includes(query));
    });

    count.textContent = pad(projects.length);
    resultsNote.textContent = query || category !== 'all'
      ? `找到 ${visible.length} 个匹配项目`
      : `共 ${projects.length} 个全景项目`;
    grid.replaceChildren(...visible.map(createCard));
    emptyState.hidden = visible.length > 0;

    if (!projects.length) {
      emptyTitle.textContent = '第一段空间漫游，正等待被收入。';
      emptyDescription.textContent = '完成导览导出后，将网页文件放入项目库并登记项目信息，即可在这里浏览。';
    } else if (!visible.length) {
      emptyTitle.textContent = '没有找到匹配的项目。';
      emptyDescription.textContent = '试试其他关键词或项目类型。';
    }
  }

  async function start() {
    try {
      const response = await fetch('data/projects.json', { cache: 'no-store' });
      if (!response.ok) throw new Error(`Project data returned ${response.status}`);
      const data = await response.json();
      projects = Array.isArray(data.projects) ? data.projects.filter((project) => project && typeof project === 'object') : [];
      projects.sort((a, b) => Number(b.year || 0) - Number(a.year || 0) || text(a.title).localeCompare(text(b.title), 'zh-CN'));
      buildFilters();
      render();
    } catch (error) {
      grid.replaceChildren();
      emptyState.hidden = true;
      loadError.hidden = false;
      resultsNote.textContent = '项目档案无法读取';
      console.error('Unable to load project catalog:', error);
    }
  }

  search.addEventListener('input', render);
  document.addEventListener('keydown', (event) => {
    if (event.key === '/' && !event.ctrlKey && !event.metaKey && !event.altKey && !['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) {
      event.preventDefault();
      search.focus();
    }
    if (event.key === 'Escape' && document.activeElement === search) {
      search.value = '';
      render();
      search.blur();
    }
  });

  start();
})();
