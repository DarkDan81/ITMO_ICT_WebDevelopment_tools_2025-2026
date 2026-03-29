const repoBase = "https://github.com/DarkDan81/ITMO_ICT_WebDevelopment_tools_2025-2026";

const labs = [
  {
    id: "lab-1",
    shortTitle: "ЛР1",
    title: "Лабораторная работа 1",
    subtitle: "FastAPI, SQLModel, PostgreSQL, Alembic и отчет по финальной версии кода",
    status: "Готово",
    semester: "2025-2026",
    theme: "Сервис управления личными финансами",
    summary:
      "Финальная версия лабораторной построена на FastAPI и PostgreSQL. В проекте есть ORM-модели на SQLModel, CRUD API, many-to-many связь между операциями и тегами, Alembic-миграции и подключение через .env.",
    metrics: [
      { label: "Практики", value: "3" },
      { label: "Эндпоинты", value: "21" },
      { label: "ORM-модели", value: "15+" },
      { label: "Миграции", value: "2" },
    ],
    sections: {
      summaryCards: [
        {
          kicker: "Тема",
          title: "Личный финансовый сервис",
          text: "Пользователь может создавать доходы и расходы, распределять операции по категориям и тегам, а также видеть вложенные связанные объекты через API.",
        },
        {
          kicker: "Финальная версия",
          title: "Практика 1.3",
          text: "В отчете показана только финальная версия кода, как и требует задание. При этом ниже есть ссылки на все этапы разработки: practice_1_1, practice_1_2 и practice_1_3.",
        },
        {
          kicker: "Стек",
          title: "FastAPI + SQLModel + Alembic",
          text: "Проект использует PostgreSQL, миграции Alembic, SQLModel для описания таблиц и связи one-to-many / many-to-many с ассоциативной сущностью.",
        },
      ],
      timeline: [
        {
          title: "Практика 1.1",
          text: "Базовый FastAPI-проект с временной БД, Pydantic-моделями и CRUD для главной сущности и вложенного объекта.",
          folder: `${repoBase}/tree/main/practice_1_1`,
          commit: `${repoBase}/commit/8516566`,
          commitLabel: "8516566",
        },
        {
          title: "Практика 1.2",
          text: "Переход на PostgreSQL и SQLModel, описание таблиц и ORM-связей, CRUD через настоящую базу данных.",
          folder: `${repoBase}/tree/main/practice_1_2`,
          commit: `${repoBase}/commit/c08e0d1`,
          commitLabel: "c08e0d1",
        },
        {
          title: "Практика 1.3",
          text: "Добавлены Alembic-миграции, .env-конфиг, передача DATABASE_URL в Alembic и история изменения ассоциативной таблицы.",
          folder: `${repoBase}/tree/main/practice_1_3`,
          commit: `${repoBase}/commit/ced87ac`,
          commitLabel: "ced87ac",
        },
      ],
      links: [
        {
          title: "GitHub ссылки",
          text: "Ссылки на папки и коммиты выполненных практик для отчета и сдачи лабораторной работы.",
          items: [
            { label: "Репозиторий", href: repoBase },
            { label: "Папка practice_1_1", href: `${repoBase}/tree/main/practice_1_1` },
            { label: "Папка practice_1_2", href: `${repoBase}/tree/main/practice_1_2` },
            { label: "Папка practice_1_3", href: `${repoBase}/tree/main/practice_1_3` },
            { label: "Коммит practice_1_1", href: `${repoBase}/commit/8516566` },
            { label: "Коммит practice_1_2", href: `${repoBase}/commit/c08e0d1` },
            { label: "Коммит practice_1_3", href: `${repoBase}/commit/ced87ac` },
          ],
        },
        {
          title: "Финальная структура",
          text: "Для отчета используется итоговая версия ЛР1 из practice_1_3, потому что в задании разрешено показывать только финальную версию кода.",
          items: [
            { label: "Финальный API", href: `${repoBase}/blob/main/practice_1_3/app/main.py` },
            { label: "Финальные модели", href: `${repoBase}/blob/main/practice_1_3/app/models.py` },
            { label: "Подключение к БД", href: `${repoBase}/blob/main/practice_1_3/app/db.py` },
            { label: "alembic.ini", href: `${repoBase}/blob/main/practice_1_3/alembic.ini` },
            { label: "env.py", href: `${repoBase}/blob/main/practice_1_3/migrations/env.py` },
          ],
        },
      ],
      endpointGroups: [
        {
          title: "Сервис и пользователи",
          text: "Базовый health endpoint и CRUD для пользователей.",
          routes: [
            ["GET", "/"],
            ["GET", "/users"],
            ["GET", "/users/{user_id}"],
            ["POST", "/users"],
            ["PATCH", "/users/{user_id}"],
            ["DELETE", "/users/{user_id}"],
          ],
        },
        {
          title: "Категории и теги",
          text: "CRUD для связанных справочников, которые используются внутри финансовых операций.",
          routes: [
            ["GET", "/categories"],
            ["GET", "/categories/{category_id}"],
            ["POST", "/categories"],
            ["PATCH", "/categories/{category_id}"],
            ["DELETE", "/categories/{category_id}"],
            ["GET", "/tags"],
            ["GET", "/tags/{tag_id}"],
            ["POST", "/tags"],
            ["PATCH", "/tags/{tag_id}"],
            ["DELETE", "/tags/{tag_id}"],
          ],
        },
        {
          title: "Финансовые операции",
          text: "CRUD для главной сущности проекта. В ответах вложенно возвращаются пользователь, категория и теги с метаданными связи.",
          routes: [
            ["GET", "/operations"],
            ["GET", "/operations/{operation_id}"],
            ["POST", "/operations"],
            ["PATCH", "/operations/{operation_id}"],
            ["DELETE", "/operations/{operation_id}"],
          ],
        },
      ],
      models: [
        {
          title: "User",
          text: "Пользователь системы и владелец категорий и операций.",
          fields: [
            "id: int | None",
            "email: str",
            "full_name: str",
            "categories: list[Category]",
            "operations: list[Operation]",
          ],
        },
        {
          title: "Category",
          text: "Категория расходов или доходов, связанная с пользователем.",
          fields: [
            "id: int | None",
            "name: str",
            "monthly_limit: float | None",
            "user_id: int | None",
            "operations: list[Operation]",
          ],
        },
        {
          title: "Tag",
          text: "Тег для маркировки операций и построения many-to-many связи.",
          fields: [
            "id: int | None",
            "name: str",
            "operations: list[Operation]",
          ],
        },
        {
          title: "Operation",
          text: "Главная таблица финансовых операций.",
          fields: [
            "id: int | None",
            "title: str",
            "amount: float",
            "operation_type: OperationType",
            "operation_date: datetime",
            "description: str | None",
            "user_id: int | None",
            "category_id: int | None",
            "tags: list[Tag]",
          ],
        },
        {
          title: "OperationTagLink",
          text: "Ассоциативная сущность для связи many-to-many между operation и tag.",
          fields: [
            "operation_id: int | None",
            "tag_id: int | None",
            "assigned_at: datetime",
            "priority: int | None",
          ],
        },
        {
          title: "Response / input models",
          text: "Отдельные модели используются для создания, обновления и сериализации вложенных ответов.",
          fields: [
            "UserCreate / UserUpdate / UserRead",
            "CategoryCreate / CategoryUpdate / CategoryRead",
            "TagCreate / TagUpdate / TagRead",
            "OperationCreate / OperationUpdate / OperationReadWithRelations",
            "OperationTagAssignment / TagReadWithMetadata",
          ],
        },
      ],
      codeFiles: [
        {
          title: "Подключение к БД",
          label: "app/db.py",
          path: "./code/lab1/db.py.txt",
        },
        {
          title: "ORM-модели",
          label: "app/models.py",
          path: "./code/lab1/models.py.txt",
        },
        {
          title: "Финальный API",
          label: "app/main.py",
          path: "./code/lab1/main.py.txt",
        },
        {
          title: "Начальная миграция",
          label: "migrations/versions/a83973acb777_initial_schema.py",
          path: "./code/lab1/migration_initial.py.txt",
        },
        {
          title: "Миграция с priority",
          label: "migrations/versions/b8d18406f516_add_priority_to_operation_tag_link.py",
          path: "./code/lab1/migration_priority.py.txt",
        },
      ],
    },
  },
  {
    id: "lab-2",
    shortTitle: "ЛР2",
    title: "Лабораторная работа 2",
    subtitle: "Threading, multiprocessing, asyncio и параллельный парсинг с сохранением в PostgreSQL",
    status: "Готово",
    semester: "2025-2026",
    theme: "Сравнение concurrency-подходов в Python",
    summary:
      "ЛР2 оформлена отдельной папкой lab_2 и содержит 6 программ: три для вычислительной задачи и три для параллельного парсинга веб-страниц. Результаты парсинга сохраняются в PostgreSQL, а в отчете собраны реальные замеры времени и выводы.",
    metrics: [
      { label: "Программы", value: "6" },
      { label: "URL в парсинге", value: "6" },
      { label: "Подходы", value: "3" },
      { label: "БД", value: "PostgreSQL" },
    ],
    sections: {
      summaryCards: [
        {
          kicker: "Часть 1",
          title: "Вычислительная задача",
          text: "Сделаны три реализации для подсчета суммы от 1 до 10000000000000: threading, multiprocessing и asyncio. Задача делится на диапазоны, а сама сумма считается функцией calculate_sum().",
        },
        {
          kicker: "Часть 2",
          title: "Параллельный парсинг",
          text: "Сделаны три отдельные программы для загрузки HTML-страниц, извлечения заголовка и сохранения результата в PostgreSQL через таблицу ParsedPage.",
        },
        {
          kicker: "Итог",
          title: "Реальные замеры",
          text: "В lab_2/REPORT.md уже внесены реальные результаты запуска на твоей машине. Для парсинга лучшим оказался async, а для формульной вычислительной задачи multiprocessing проиграл из-за накладных расходов.",
        },
      ],
      timeline: [
        {
          title: "Лабораторная работа 2",
          text: "Отдельный проект с общими модулями, 6 исполняемыми программами, PostgreSQL-сохранением и готовым отчетом по результатам.",
          folder: `${repoBase}/tree/main/lab_2`,
          commit: `${repoBase}/commit/4944971`,
          commitLabel: "4944971",
        },
      ],
      links: [
        {
          title: "GitHub ссылки",
          text: "Ссылки на папку лабораторной, коммит и основные файлы проекта.",
          items: [
            { label: "Папка lab_2", href: `${repoBase}/tree/main/lab_2` },
            { label: "Коммит lab_2", href: `${repoBase}/commit/4944971` },
            { label: "Отчет REPORT.md", href: `${repoBase}/blob/main/lab_2/REPORT.md` },
            { label: "README", href: `${repoBase}/blob/main/lab_2/README.md` },
          ],
        },
        {
          title: "Ключевые файлы",
          text: "Основные модули и программы для вычислений и парсинга.",
          items: [
            { label: "task1_threading.py", href: `${repoBase}/blob/main/lab_2/task1_threading.py` },
            { label: "task1_multiprocessing.py", href: `${repoBase}/blob/main/lab_2/task1_multiprocessing.py` },
            { label: "task1_async.py", href: `${repoBase}/blob/main/lab_2/task1_async.py` },
            { label: "task2_threading.py", href: `${repoBase}/blob/main/lab_2/task2_threading.py` },
            { label: "task2_multiprocessing.py", href: `${repoBase}/blob/main/lab_2/task2_multiprocessing.py` },
            { label: "task2_async.py", href: `${repoBase}/blob/main/lab_2/task2_async.py` },
          ],
        },
      ],
      endpointGroups: [
        {
          title: "Часть 1. Вычисления",
          text: "Сравнение подходов на задаче суммирования диапазона с разбиением на подзадачи.",
          routes: [
            ["RUN", "python task1_threading.py"],
            ["RUN", "python task1_multiprocessing.py"],
            ["RUN", "python task1_async.py"],
          ],
        },
        {
          title: "Часть 2. Парсинг",
          text: "Параллельная загрузка веб-страниц с сохранением URL, source_name, title, status_code и fetch_method в PostgreSQL.",
          routes: [
            ["RUN", "python task2_threading.py"],
            ["RUN", "python task2_multiprocessing.py"],
            ["RUN", "python task2_async.py"],
          ],
        },
      ],
      models: [
        {
          title: "ParsedPage",
          text: "Таблица для сохранения результатов парсинга в ту же PostgreSQL-среду, что использовалась в лабораторной 1.",
          fields: [
            "id: int | None",
            "url: str",
            "source_name: str",
            "title: str",
            "fetch_method: str",
            "status_code: int",
            "fetched_at: datetime",
          ],
        },
        {
          title: "Вычислительные модули",
          text: "Общая логика вычислений вынесена в compute_shared.py.",
          fields: [
            "calculate_sum(start, end)",
            "split_range(limit, chunks)",
            "timed_run(...)",
            "ComputeResult",
          ],
        },
        {
          title: "Парсинг и БД",
          text: "Общая логика парсинга вынесена в parse_shared.py и db.py.",
          fields: [
            "extract_title(html)",
            "save_page_result(...)",
            "reset_results(fetch_method)",
            "timed_parse_run(...)",
          ],
        },
        {
          title: "Результаты запуска",
          text: "В отчет уже включены реальные замеры времени.",
          fields: [
            "Task1 threading: 0.000901 s",
            "Task1 multiprocessing: 0.284765 s",
            "Task1 asyncio: 0.001184 s",
            "Task2 threading: 9.758948 s",
            "Task2 multiprocessing: 10.553567 s",
            "Task2 async: 8.307293 s",
          ],
        },
      ],
      codeFiles: [
        {
          title: "Подключение к БД",
          label: "lab_2/app/db.py",
          path: "./code/lab2/db.py.txt",
        },
        {
          title: "Модель ParsedPage",
          label: "lab_2/app/models.py",
          path: "./code/lab2/models.py.txt",
        },
        {
          title: "Multiprocessing вычисления",
          label: "lab_2/task1_multiprocessing.py",
          path: "./code/lab2/task1_multiprocessing.py.txt",
        },
        {
          title: "Async парсинг",
          label: "lab_2/task2_async.py",
          path: "./code/lab2/task2_async.py.txt",
        },
        {
          title: "Отчет по ЛР2",
          label: "lab_2/REPORT.md",
          path: "./code/lab2/report.md.txt",
        },
      ],
    },
  },
];

const futureLabs = [
  "Добавлять новые лабораторные отдельными объектами в массив labs.",
  "Для каждой новой ЛР прикладывать финальные кодовые файлы в docs/code/labN.",
  "В карточках timeline хранить ссылки на папки, коммиты или ветки с этапами выполнения.",
  "В блоках codeFiles указывать только финальную версию кода, как требует задание.",
];

const state = {
  activeLabId: labs[0]?.id,
};

function methodClass(method) {
  return `method-badge method-${method.toLowerCase()}`;
}

function renderHero() {
  const hero = document.getElementById("hero");
  const totalEndpoints = labs.reduce(
    (sum, lab) => sum + lab.sections.endpointGroups.reduce((acc, item) => acc + item.routes.length, 0),
    0,
  );
  const totalPractices = labs.reduce((sum, lab) => sum + lab.sections.timeline.length, 0);

  hero.innerHTML = `
    <div class="hero-grid">
      <div>
        <p class="section-kicker">Темный GitHub Pages отчет</p>
        <h2>Лабораторные по вебу в одной аккуратной структуре</h2>
        <p>
          Это универсальная страница отчета для публикации через GitHub Pages.
          Сейчас она уже заполнена по ЛР1 и рассчитана на дальнейшее расширение:
          сюда можно добавлять следующие лабораторные без переделки дизайна и общей архитектуры отчета.
        </p>
      </div>
      <div class="hero-metrics">
        <div class="metric-card">
          <span class="metric-label">Лабораторные в отчете</span>
          <span class="metric-value">${labs.length}</span>
        </div>
        <div class="metric-card">
          <span class="metric-label">Практики с ссылками</span>
          <span class="metric-value">${totalPractices}</span>
        </div>
        <div class="metric-card">
          <span class="metric-label">Эндпоинты в описании</span>
          <span class="metric-value">${totalEndpoints}</span>
        </div>
        <div class="metric-card">
          <span class="metric-label">Публикация</span>
          <span class="metric-value">/docs</span>
        </div>
      </div>
    </div>
  `;
}

function renderNavigation() {
  const nav = document.getElementById("lab-navigation");
  nav.innerHTML = labs
    .map(
      (lab) => `
        <a class="nav-link ${lab.id === state.activeLabId ? "active" : ""}" href="#${lab.id}" data-lab-id="${lab.id}">
          <span>${lab.shortTitle}</span>
          <span>${lab.status}</span>
        </a>
      `,
    )
    .join("");

  nav.querySelectorAll("[data-lab-id]").forEach((link) => {
    link.addEventListener("click", (event) => {
      event.preventDefault();
      state.activeLabId = link.dataset.labId;
      render();
      document.getElementById("lab-content").scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });
}

function renderSelector() {
  const selector = document.getElementById("lab-selector");
  selector.innerHTML = `
    <div class="selector-panel">
      ${labs
        .map(
          (lab) => `
            <button type="button" class="selector-button ${lab.id === state.activeLabId ? "active" : ""}" data-lab-id="${lab.id}">
              ${lab.shortTitle}: ${lab.title}
            </button>
          `,
        )
        .join("")}
    </div>
  `;

  selector.querySelectorAll("[data-lab-id]").forEach((button) => {
    button.addEventListener("click", () => {
      state.activeLabId = button.dataset.labId;
      render();
    });
  });
}

function renderLinks(cards) {
  return `
    <section class="glass-card">
      <p class="section-kicker">GitHub</p>
      <h3>Ссылки на папки, коммиты и финальный код</h3>
      <div class="links-grid">
        ${cards
          .map(
            (card) => `
              <article class="summary-card">
                <p class="section-kicker">Links</p>
                <h3>${card.title}</h3>
                <p>${card.text}</p>
                <ul class="link-list">
                  ${card.items
                    .map((item) => `<li><a href="${item.href}" target="_blank" rel="noreferrer">${item.label}</a></li>`)
                    .join("")}
                </ul>
              </article>
            `,
          )
          .join("")}
      </div>
    </section>
  `;
}

function renderLab(lab) {
  return `
    <div class="lab-layout" id="${lab.id}">
      <section class="glass-card">
        <p class="section-kicker">${lab.semester}</p>
        <h3>${lab.title}</h3>
        <p>${lab.summary}</p>
        <div class="tag-row">
          <span class="tag">${lab.theme}</span>
          <span class="tag">${lab.subtitle}</span>
          <span class="tag">${lab.status}</span>
        </div>
      </section>

      <section class="summary-grid">
        ${lab.sections.summaryCards
          .map(
            (card) => `
              <article class="summary-card">
                <p class="section-kicker">${card.kicker}</p>
                <h3>${card.title}</h3>
                <p>${card.text}</p>
              </article>
            `,
          )
          .join("")}
      </section>

      <section class="glass-card">
        <p class="section-kicker">Практики</p>
        <h3>Этапы выполнения ЛР</h3>
        <div class="timeline-grid">
          ${lab.sections.timeline
            .map(
              (item) => `
                <article class="timeline-card">
                  <p class="section-kicker">Practice</p>
                  <h3>${item.title}</h3>
                  <p>${item.text}</p>
                  <ul class="link-list">
                    <li><a href="${item.folder}" target="_blank" rel="noreferrer">Открыть папку</a></li>
                    <li><a href="${item.commit}" target="_blank" rel="noreferrer">Открыть коммит ${item.commitLabel}</a></li>
                  </ul>
                </article>
              `,
            )
            .join("")}
        </div>
      </section>

      ${renderLinks(lab.sections.links)}

      <section class="glass-card">
        <p class="section-kicker">Эндпоинты</p>
        <h3>Все реализованные маршруты</h3>
        <div class="endpoint-grid">
          ${lab.sections.endpointGroups
            .map(
              (group) => `
                <article class="endpoint-card">
                  <p class="section-kicker">API</p>
                  <h3>${group.title}</h3>
                  <p>${group.text}</p>
                  <ul class="endpoint-list">
                    ${group.routes
                      .map(
                        ([method, route]) => `
                          <li>
                            <span class="${methodClass(method)}">${method}</span>
                            <span class="endpoint-route">${route}</span>
                          </li>
                        `,
                      )
                      .join("")}
                  </ul>
                </article>
              `,
            )
            .join("")}
        </div>
      </section>

      <section class="glass-card">
        <p class="section-kicker">Модели</p>
        <h3>Модели и сущности финальной версии</h3>
        <div class="models-grid">
          ${lab.sections.models
            .map(
              (model) => `
                <article class="model-card">
                  <p class="section-kicker">Model</p>
                  <h3>${model.title}</h3>
                  <p>${model.text}</p>
                  <ul class="field-list">
                    ${model.fields.map((field) => `<li>${field}</li>`).join("")}
                  </ul>
                </article>
              `,
            )
            .join("")}
        </div>
      </section>

      <section class="glass-card">
        <p class="section-kicker">Финальный код</p>
        <h3>Подключение к БД, модели, API и миграции</h3>
        <p class="muted">
          Ниже показана финальная версия кода, используемая в итоговой реализации лабораторной работы.
        </p>
        <div class="code-grid" id="code-grid"></div>
      </section>

      <section class="empty-state">
        <p class="section-kicker">Следующие лабораторные</p>
        <h3>Каркас уже готов для расширения</h3>
        <ul class="future-list">
          ${futureLabs.map((item) => `<li>${item}</li>`).join("")}
        </ul>
      </section>
    </div>
  `;
}

async function renderCodeBlocks(lab) {
  const codeGrid = document.getElementById("code-grid");
  const template = document.getElementById("code-card-template");
  codeGrid.innerHTML = "";

  for (const file of lab.sections.codeFiles) {
    const node = template.content.firstElementChild.cloneNode(true);
    node.querySelector(".code-label").textContent = "Final code";
    node.querySelector(".code-title").textContent = file.title;
    const codeElement = node.querySelector("code");

    try {
      let text = null;
      if (typeof CODE_FILES !== "undefined" && CODE_FILES[file.path]) {
        text = CODE_FILES[file.path];
      } else {
        const response = await fetch(file.path);
        text = await response.text();
      }
      codeElement.textContent = text;
      node.querySelector(".copy-button").addEventListener("click", async () => {
        await navigator.clipboard.writeText(text);
        const button = node.querySelector(".copy-button");
        const initial = button.textContent;
        button.textContent = "Copied";
        setTimeout(() => {
          button.textContent = initial;
        }, 1200);
      });
    } catch (error) {
      codeElement.textContent = "Не удалось загрузить кодовый файл.";
    }

    codeGrid.appendChild(node);
  }
}

async function render() {
  renderHero();
  renderNavigation();
  renderSelector();

  const activeLab = labs.find((lab) => lab.id === state.activeLabId);
  const content = document.getElementById("lab-content");
  content.innerHTML = renderLab(activeLab);
  await renderCodeBlocks(activeLab);
}

render();
