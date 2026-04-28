# POKROV UI/UX Master Plan для агента

**Цель:** превратить текущий сайт, веб-кабинет и админку POKROV из “джунского интерфейса” в цельный, сочный, дорогой, быстрый и честный digital-продукт.  
**Формат:** orchestration brief для 10 агентов: 5 исследователей + 5 воркеров.  
**Референсы от владельца:** Neuform Capital Overview Dashboard и NovaEstate Dashboard. Их использовать как ощущение: premium dashboard, мягкие карточки, воздух, стекло, круглость, аккуратная типографика, но не копировать композиции, сетки, цвета или конкретные блоки.

---

## 0. Главный диагноз

Сейчас проблема не только в “некрасиво”. Продукт визуально и поведенчески не совпадает с обещанием POKROV как спокойного, премиального, app-first сервиса.

### Что видно по репозиторию и текущему продукту

1. **В веб-кабинете есть реальный mojibake в пользовательском тексте.**  
   В `webapp/src/app/loading.tsx` лежит текст вида `РѕС‚РєСЂС‹РІР°РµРј РєР°Р±РёРЅРµС‚`, то есть сломанная кодировка русского текста. Похожий мусор есть и в контентных страницах, например downloads. Это не косметика, это instant trust-breaker.

2. **Текущий loading выглядит как fake progress / fake care.**  
   Пользователь видит экран “Подтягиваем кабинет / Проверяем сессию…”, но это не честный прогресс, а общий экран ожидания. Он повторяется при переходах и создает ощущение медленного продукта.

3. **Оболочка уже есть, но нужно сделать ее настоящим persistent shell.**  
   В `cabinet-shell.tsx` уже есть сайдбар, навигация, состояние loading/error, mobile menu, профильный статус. Это хорошая база, но UX должен измениться: shell должен оставаться на месте, а грузиться должны только зоны контента.

4. **Стек уже позволяет сделать современно без полного переписывания.**  
   `webapp` использует Next, React, Tailwind, Framer Motion, Playwright. `marketing` использует Next, Framer Motion и GSAP. Значит, задача — не “добавить магии”, а правильно собрать дизайн-систему, motion-систему и loading/performance-поведение.

5. **В `globals.css` уже есть попытки depth/effects, но они частично заглушены.**  
   Есть переменные, glass, shadows, animations, а ниже есть flattening overrides: часть декоративности отключается. Вероятно, дизайн когда-то пытались сделать “сочным”, потом упростили. Нужно вернуть глубину контролируемо, не превращая все в шум.

6. **В корневом `DESIGN.md` уже задана правильная тональность.**  
   Brand direction: calm, premium, reliable, practical. Light canvas, white surfaces, mint accents, deep green, restrained motion. Это надо не менять, а довести до уровня продукта.

7. **В публичной коммуникации есть ограничение по формулировкам.**  
   На public/marketing не надо прямолинейно упираться в слово `VPN` и raw transport-jargon. Язык должен быть consumer-first, app-first, без неподтвержденных обещаний.

8. **Admin и consumer cabinet нельзя делать одинаковыми.**  
   Кабинет пользователя — мягкий, ориентированный на next action. Админка — плотная, операционная, честная, с таблицами, фильтрами, статусами, risk badges, быстрыми действиями.

9. **Визуальный “вау” должен появиться уже с нулевой точки.**  
   С первого экрана: premium canvas, мягкая глубина, чистый язык, приятный skeleton, аккуратный route transition. Не заставлять пользователя ждать, пока “красота” появится после загрузки.

10. **Главное правило: честность состояния.**  
    Никакого fake progress. Если данные грузятся — показываем shell, skeleton соответствующей формы, cached/stale snapshot, microcopy “обновляем данные”. Если есть реальный этап — показываем реальный этап. Если этапа нет — не притворяемся.

---

## 1. North Star: POKROV Atlas Glass

Рабочее название направления: **POKROV Atlas Glass**.

Это не “кислотный SaaS-дэшборд” и не “банковская скука”. Это ощущение:

- светлый premium dashboard;
- белые и молочные поверхности;
- глубокий зеленый как брендовая опора;
- mint/emerald glow как сигнал защищенности;
- большие радиусы;
- soft elevation вместо грубых теней;
- crisp typography;
- микроанимации, которые делают продукт живым, но не мешают;
- мобильная версия не “сжатый десктоп”, а app-like shell.

### Визуальная формула

```txt
POKROV = calm security + app-first clarity + premium glass dashboard + honest operational states
```

### Не копировать Neuform

Референсы Neuform использовать так:

- взять ощущение “дорого / аккуратно / modern dashboard”;
- взять принцип rounded cards + air + strong hierarchy;
- взять идею визуального центра, где есть один главный статус и несколько supporting cards;
- не копировать layout, цвета, карточки, типографику, иконки или конкретные композиции.

---

## 2. Product truth, который агент обязан держать в голове

### POKROV как продукт

- Это consumer-first сервис, где пользователь должен быстро понять: доступ активен, что делать дальше, как подключить устройство, когда продлевать.
- Продукт app-first: Android/Windows-клиент важен, браузерный кабинет — продолжение и управление.
- Public marketing и web cabinet — разные поверхности.
- User cabinet должен быть спокойным и понятным.
- Admin должен быть плотным и операционным.

### Поверхности

- **Marketing:** `https://pokrov.space/` — public acquisition, оффер, доверие, onboarding, checkout handoff.
- **WebApp:** `https://app.pokrov.space/` — браузерный кабинет, redeem, checkout continuation, admin.
- **Client App:** Android/Windows, app-first experience.

### Важные продуктовые факты, которые нельзя исказить

- Trial: 5 дней.
- Telegram reward: +10 дней.
- Нужно аккуратно относиться к состояниям Android/Windows релиза, не обещать неподтвержденный production.
- Default transport/runtime детали не вываливать пользователю в лицо.
- Диагностику, raw config, low-level details — в “подробнее”, не на главный экран.

---

## 3. Главные UX-проблемы, которые надо исправить первыми

### P0. Mojibake / сломанная кодировка

Найти и заменить весь текст вида:

```txt
РѕС‚РєСЂС‹РІР°РµРј РєР°Р±РёРЅРµС‚
РџРѕРґС‚СЏРіРёРІР°РµРј...
РћР±С‰Р°СЏ...
```

Команды для воркера:

```bash
rg "Р[А-Яа-я]" webapp/src marketing/src
rg "С[А-Яа-я]" webapp/src marketing/src
rg "Рџ|Рѕ|Рґ|СЏ|СЃ|С‚|СЂ|С‹|С†|Сѓ|С‰" webapp/src marketing/src
```

После замены прогнать snapshot/manual QA всех экранов. Наличие mojibake в интерфейсе = блокер релиза.

### P0. Loading и route transitions

Убрать full-screen loader при каждом переходе внутри кабинета. Сделать:

- cold start screen только для первого входа, максимум один раз за session;
- persistent shell, который не исчезает при переходах;
- content skeleton внутри страницы;
- top route activity bar без процентов;
- cached snapshot, если есть старые данные;
- no fake progress.

### P0. Design tokens

Сейчас нельзя “рисовать каждый экран заново”. Сначала собрать:

- цветовые токены;
- радиусы;
- shadows;
- typography scale;
- spacing scale;
- motion tokens;
- компонентные variants.

### P1. Dashboard IA

Главная кабинета должна отвечать на 4 вопроса за 5 секунд:

1. У меня доступ активен?
2. До какого числа / сколько осталось?
3. Что мне сделать сейчас?
4. Как подключить или проверить устройство?

### P1. Marketing ↔ Cabinet continuity

Переход с сайта в кабинет не должен выглядеть как попадание в другой продукт. Нужны общие токены и общий визуальный язык, но разная плотность.

### P1. Admin density

Админка не должна быть “красивая пустота”. Для оператора ценны:

- таблицы;
- фильтры;
- статусы;
- быстрые действия;
- badges;
- audit trail;
- search;
- error/retry states.

---

## 4. План для 10 агентов

## 4.1 Researcher 1 — Reference Atlas / Moodboard

**Миссия:** собрать визуальную карту без копирования.

### Изучить

- Neuform Capital Overview Dashboard.
- Neuform NovaEstate Dashboard.
- Mobbin dashboard/web app screenshots.
- Linear-style SaaS interfaces.
- shadcn/ui blocks and design-system examples.
- Modern fintech/security dashboards.
- Premium mobile app settings/profile screens.

### Что искать

- Как выглядят premium dashboard cards.
- Как строится first screen.
- Как карточки группируются в bento/grid.
- Как делается soft glass без “дешевого blur”.
- Как показывают subscription, status, devices, support.
- Как выглядят empty/error/loading states.
- Как выглядит современный mobile shell.

### Deliverables

1. `reference-atlas.md`:
   - 20–40 референсов;
   - 1–2 скрина на каждый, если можно;
   - что берем;
   - что не берем;
   - почему подходит POKROV.

2. `pattern-inventory.md`:
   - status hero;
   - subscription card;
   - device card;
   - checkout panel;
   - support panel;
   - admin table;
   - mobile navigation;
   - loading/skeleton.

3. `visual-direction-v1.md`:
   - 3 возможных направления;
   - recommended direction: `POKROV Atlas Glass`;
   - риски каждого направления.

### Вопросы от Researcher 1 владельцу

- POKROV должен ощущаться ближе к **банку**, **Apple-сервису**, **Linear**, **Nothing**, **Telegram Mini App**, **security console** или **premium lifestyle app**?
- Насколько допустим glassmorphism: едва заметный или прямо “вау-стекло”?
- Должен ли кабинет быть светлым по умолчанию? Нужна ли dark-тема сразу или вторым этапом?
- Что важнее: “дорого и спокойно” или “технологично и дерзко”?
- Какие 3 интерфейса владелец считает красивыми, кроме Neuform?
- Какие 3 интерфейса владелец ненавидит и почему?

---

## 4.2 Researcher 2 — Product IA / Copy / User Flows

**Миссия:** сделать продукт понятным, без технической каши и сломанной речи.

### Изучить

- Все routes webapp.
- Все marketing routes.
- `DESIGN.md`, `AGENTS.md`, `webapp/README.md`, `POKROV-app/DESIGN.md`.
- Тексты на текущем `pokrov.space` и `app.pokrov.space`.
- Все русские строки в коде.

### Сделать

1. `route-map.md`:
   - route;
   - кто пользователь;
   - задача пользователя;
   - primary CTA;
   - secondary CTA;
   - empty state;
   - error state;
   - loading state;
   - copy risks.

2. `copy-bank.md`:
   - все заголовки;
   - все подзаголовки;
   - CTA;
   - helper text;
   - errors;
   - loading text;
   - admin labels;
   - Telegram/login copy;
   - no mojibake.

3. `language-rules.md`:
   - public: no raw `VPN`, no transport jargon;
   - cabinet: можно говорить “доступ”, “подключение”, “устройства”, “ключ”, “сессия”, но без перегруза;
   - admin: можно technical labels;
   - никаких “мы почти закончили” если это не реальный этап.

### Вопросы от Researcher 2 владельцу

- Для кого главный пользователь: новичок, который ничего не понимает, или техничный пользователь?
- Что самое частое действие после входа: скачать приложение, продлить, подключить устройство, проверить статус, написать в поддержку?
- Нужно ли в кабинете объяснять “что такое POKROV” или пользователь уже всё знает?
- Какой тон: “вы” строго, “ты” дружелюбно, или микс нельзя?
- Нужно ли использовать слово “защита”, “доступ”, “подключение”, “маршрут”, “ключ”, “узел”? Какие слова запрещены?
- Что делать с пользователем без Telegram?
- Какой путь самый критичный: trial → app install → first connection или checkout → renew?
- Должны ли мы показывать пользователю технические причины ошибок или только человеческие формулировки?

---

## 4.3 Researcher 3 — Frontend Architecture / Performance / Loading

**Миссия:** убрать ощущение медленной вебаппы, не ломая auth/API.

### Изучить

- Next App Router loading behavior.
- `webapp/src/app/loading.tsx`.
- `webapp/src/components/cabinet-shell.tsx`.
- `webapp/src/components/route-transition.tsx`.
- `webapp/src/lib/session.tsx`.
- API calls during first load.
- Static export constraints.
- Current Playwright tests.

### Сделать

1. `loading-audit.md`:
   - где появляется full-screen loader;
   - сколько раз;
   - почему;
   - какие fetches последовательные;
   - какие можно параллелить;
   - где можно показать cached snapshot.

2. `performance-plan.md`:
   - route prefetch;
   - shell persistence;
   - session cache;
   - stale-while-refresh;
   - skeleton map;
   - bundle hotspots;
   - interaction budget.

3. `technical-risk-map.md`:
   - что можно менять безопасно;
   - что нельзя трогать без API тестов;
   - какие изменения требуют e2e.

### Вопросы от Researcher 3 владельцу/команде

- Можно ли хранить dashboard snapshot в `sessionStorage` на 5–10 минут?
- Какие данные считаются sensitive и не должны кешироваться в браузере?
- Есть ли endpoint, который возвращает весь dashboard одним payload?
- Сколько сейчас реально занимает `fetchAuthSession` + `fetchDashboard` + `fetchUser`?
- Можно ли включить server-side/proxy слой или `webapp` обязан оставаться static export?
- Можно ли менять структуру API calls или только UI вокруг них?
- Есть ли Sentry/analytics/perf logging?

---

## 4.4 Researcher 4 — Motion / Interaction / Accessibility

**Миссия:** сделать “живой” интерфейс без кринжа и motion sickness.

### Изучить

- Framer Motion / Motion for React в текущем webapp.
- GSAP в marketing.
- `prefers-reduced-motion`.
- Current `route-transition.tsx`.
- Hover/focus states.
- Keyboard navigation.
- Screen-reader states for loading/errors.

### Motion principles

- Motion должен объяснять структуру, а не просто “прыгать”.
- Любая анимация должна иметь reduced-motion вариант.
- Не анимировать layout слишком агрессивно на admin tables.
- Использовать transforms/opacity, избегать тяжелых blur-анимаций на слабых устройствах.
- Hero/marketing можно богаче; cabinet — спокойнее.

### Deliverables

1. `motion-spec.md`:
   - duration tokens;
   - easing tokens;
   - interaction patterns;
   - page transitions;
   - skeleton shimmer;
   - card hover;
   - nav indicator;
   - support thread animation;
   - reduced motion rules.

2. `accessibility-checklist.md`:
   - focus-visible;
   - contrast;
   - aria-live for loading;
   - keyboard nav;
   - reduced motion;
   - touch target size;
   - semantic headings.

### Вопросы от Researcher 4 владельцу

- Насколько “вау” можно делать на marketing: мягкая 3D/GSAP сцена или только subtle motion?
- Нужны ли scroll-based animations или лучше instant product clarity?
- Нужен ли animated background в кабинете или только на login/marketing?
- Должен ли dashboard ощущаться как “живой статус-центр”?
- Нормально ли использовать count-up/stat animations, или они выглядят дешево?

---

## 4.5 Researcher 5 — Design System / Tokens / Component Architecture

**Миссия:** собрать систему, чтобы воркеры не делали 20 разных красивостей.

### Изучить

- `shared/design-tokens.json`.
- `DESIGN.md`.
- `webapp/src/app/globals.css`.
- `marketing/src/app/globals.css`.
- `cabinet-primitives`, `shell-primitives`, `cabinet-page`.
- Tailwind v4 theme variables.
- shadcn/ui / Radix patterns as inspiration, not blind dependency dump.

### Сделать

1. `tokens-v1.md`:
   - color palette;
   - radius scale;
   - shadow scale;
   - typography scale;
   - spacing scale;
   - motion scale;
   - breakpoints;
   - density modes.

2. `component-contracts.md`:
   - props;
   - variants;
   - visual rules;
   - accessibility rules;
   - examples.

3. `migration-map.md`:
   - какие старые classes заменить;
   - какие компоненты оставить;
   - какие удалить;
   - какие wrappers создать.

### Вопросы от Researcher 5 владельцу/команде

- Можно ли добавить Radix/shadcn primitives или держим zero-extra dependency?
- Нужна ли полноценная dark-тема в v1?
- Какие брендовые цвета уже закреплены юридически/маркетингово?
- Можно ли менять логотип/wordmark usage или только UI вокруг?
- Нужно ли поддерживать старые браузеры или можно ориентироваться на современный mobile/desktop?

---

# 5. Worker lanes

## 5.1 Worker 1 — Tokens & Base UI

**Миссия:** заложить фундамент.

### Scope

- `shared/design-tokens.json`
- `webapp/src/app/globals.css`
- `marketing/src/app/globals.css`
- `webapp/src/components/cabinet-primitives.*`
- `webapp/src/components/shell-primitives.*`
- возможно новые `ui/*` компоненты

### Tasks

1. Ввести `POKROV Atlas Glass` tokens.
2. Синхронизировать webapp/marketing по базовым цветам, radius, typography.
3. Создать primitives:
   - `Surface`
   - `GlassPanel`
   - `BentoCard`
   - `MetricTile`
   - `ActionCard`
   - `StatusBadge`
   - `ProgressMeter`
   - `SkeletonBlock`
   - `PageHeader`
   - `EmptyState`
   - `ErrorState`
4. Удалить/переписать конфликтующие flattening overrides там, где они убивают premium depth.
5. Не делать “кашу из blur”: максимум 1–2 слоя стекла на экран.

### Acceptance

- Все новые компоненты используют токены, а не random hex.
- Нет визуального расхождения webapp/marketing на уровне базовых цветов.
- Тени мягкие, не грязные.
- Радиусы единые.
- Текст readable на русском.

---

## 5.2 Worker 2 — Shell, Loading, Route Transitions

**Миссия:** убрать раздражение от переходов и fake loading.

### Scope

- `webapp/src/app/loading.tsx`
- `webapp/src/app/template.tsx`
- `webapp/src/components/cabinet-shell.tsx`
- `webapp/src/components/route-transition.tsx`
- `webapp/src/lib/session.tsx`
- nav links / prefetch behavior

### Tasks

1. Исправить `loading.tsx` mojibake.
2. Превратить cold start loader в `InitialBootstrapScreen`:
   - красивый;
   - честный;
   - без fake percent;
   - показывается только когда нет shell/snapshot.
3. Внутри кабинета оставить shell на месте при переходах.
4. Для контента использовать page-specific skeletons.
5. Ввести route activity indicator:
   - top 2px bar;
   - indeterminate;
   - без процентов;
   - reduced-motion safe.
6. Реализовать `router.prefetch()` на hover/focus для cabinet nav, если безопасно.
7. Session snapshot:
   - `sessionStorage` TTL, если разрешено;
   - показывать “Обновляем данные…” chip;
   - не показывать old data как fresh.
8. Ошибки грузить через `ErrorState`, не через текстовый collapse.

### Acceptance

- При переходе `/dashboard` → `/devices` shell не исчезает.
- Нет full-screen loader на каждый route.
- На cold start loader выглядит premium и честно.
- В UI нет mojibake.
- Reduced motion отключает лишние анимации.

---

## 5.3 Worker 3 — Cabinet Redesign

**Миссия:** переделать все пользовательские страницы кабинета.

### Routes

- `/`
- `/dashboard/`
- `/subscription/`
- `/devices/`
- `/statistics/`
- `/downloads/`
- `/support/`
- `/settings/`
- `/redeem/`
- `/subscription/checkout/`

### Главная идея кабинета

Пользователь не должен “искать где что”. Он должен видеть:

- статус доступа;
- next action;
- приложения;
- устройства;
- оплату/продление;
- поддержку.

### Acceptance

- Каждый экран имеет strong heading + one primary action.
- Нет технического мусора на первом уровне.
- Empty/error/loading states сделаны красиво.
- Mobile-first не ломается.
- Страницы ощущаются как один продукт.

---

## 5.4 Worker 4 — Marketing, Checkout, Public Continuity

**Миссия:** сделать public site визуально совместимым с кабинетом, но более “вау”.

### Scope

- `marketing/src/app/page.tsx`
- `marketing/src/components/home/*`
- checkout/public routes
- install/devices/mobile pages
- shared visual assets

### Tasks

1. Hero: POKROV as calm app-first protection/access product.
2. Background: subtle atlas grid, glass cards, emerald/mint orbit, no heavy noise.
3. CTA: `Начать`, `Скачать`, `Открыть кабинет`, depending on route.
4. GSAP только там, где реально нужен вау:
   - hero glow/parallax;
   - device cards reveal;
   - trust strip;
   - but no scroll-jacking.
5. Checkout handoff должен выглядеть как продолжение сайта, не отдельная форма.
6. Public copy не нарушает ограничения по языку.

### Acceptance

- Marketing first screen выглядит дороже текущего кабинета.
- Но кабинет после перехода не выглядит “бедным братом”.
- Lighthouse/Perf не убит тяжелыми анимациями.
- Reduced motion supported.

---

## 5.5 Worker 5 — Admin, QA, Visual Regression

**Миссия:** сделать админку плотной, красивой и надежной, затем все проверить.

### Admin routes

- `/admin/`
- `/admin/dashboard/`
- `/admin/users/`
- `/admin/network/`
- `/admin/nodes/`
- `/admin/tickets/`
- `/admin/bonuses/`
- `/admin/promos/`
- `/admin/referrals/`
- `/admin/broadcast/`

### Tasks

1. Admin layout separate density mode.
2. Tables:
   - sticky header;
   - clear filters;
   - row density;
   - status badges;
   - empty/error states;
   - loading skeleton rows.
3. Операционные cards:
   - revenue/access/users/network/tickets;
   - risk indicators;
   - last updated.
4. Playwright visual smoke for key routes.
5. Accessibility smoke.
6. Performance smoke.
7. Mojibake scanner in CI/check script.

### Acceptance

- Admin не выглядит как consumer dashboard.
- Данные читаются быстро.
- Есть clear state hierarchy.
- Все critical routes открываются без visual breaks.

---

# 6. Page-by-page redesign spec

## 6.1 Entry / Login `/`

### Цель

Пользователь понимает, куда попал, как войти, и почему это безопасно/легко.

### UI

- Large soft glass login card.
- Background: light canvas + subtle radial mint glow + atlas grid.
- Left/top brand panel: “POKROV” + 1-line promise.
- Login methods:
  - Telegram primary, если это главный канал;
  - email/password secondary, если поддерживается;
  - magic link / future state не показывать как доступное, если не работает.
- Helper text human, not technical.

### Copy direction

```txt
Откройте кабинет POKROV
Управляйте доступом, устройствами и продлением в одном месте.
```

### Loading

- On submit: button-level loading.
- No full page reset.
- Error under relevant field.

---

## 6.2 Dashboard `/dashboard/`

### Цель

Главный экран как “Access Cockpit”.

### Above the fold

1. **Hero status card**
   - “Доступ активен” / “Нужно продлить” / “Ожидает активации”
   - date / remaining days
   - primary CTA
   - subtle animated status ring, reduced-motion safe

2. **Next action card**
   - “Скачайте приложение” / “Подключите устройство” / “Продлите доступ” / “Проверьте поддержку”

3. **Subscription runway**
   - meter with days left
   - renewal CTA

4. **Device quick cards**
   - Android
   - Windows
   - “добавить устройство”

### Layout

Desktop:

```txt
[Hero status 2 cols] [Subscription/Next action]
[Devices] [Downloads] [Support]
[Stats strip / recent activity]
```

Mobile:

```txt
Hero status
Next action
Install app
Subscription
Devices
Support
```

### Avoid

- Raw API status.
- Too many metrics.
- “VPN” as first word.
- Empty white boxes.

---

## 6.3 Subscription `/subscription/`

### Цель

Пользователь понимает свой план, срок, продление и оплату.

### Blocks

- Current plan card.
- Days left / renewal timeline.
- Plan options.
- Payment CTA.
- Telegram bonus reminder if applicable.
- Receipts/history if available.

### Copy

- Не давить тревогой.
- Если доступ истекает — clearly but calm.
- Если trial — объяснить trial and next step.

---

## 6.4 Devices `/devices/`

### Цель

Пользователь понимает, где POKROV подключен, и что делать с устройствами.

### Blocks

- Device limit meter.
- Device cards:
  - platform icon;
  - device name;
  - last seen;
  - status;
  - actions: rename/revoke/details.
- Add device CTA.
- Empty state: “Подключите первое устройство”.

### Design

- Cards with device silhouette/icon.
- Status dot but not screaming.
- Details hidden in accordion/drawer.

---

## 6.5 Statistics `/statistics/`

### Цель

Показать полезную активность без превращения в сетевой мониторинг.

### Blocks

- Usage overview if reliable.
- Last connection summary.
- Protected sessions / device activity.
- “Что значит этот показатель?” helper.

### Avoid

- Сырые transport metrics без объяснения.
- Графики ради графиков.
- Данные, которые могут быть неточными, без disclaimer.

---

## 6.6 Downloads `/downloads/`

### Цель

Пользователь быстро скачивает правильное приложение.

### Blocks

- Android card.
- Windows card.
- Version/status/release channel.
- Install steps.
- Browser fallback / Telegram support.

### Important

Сейчас эта зона особенно чувствительна: если Android/Windows имеют gated/beta status, текст должен быть честным.

### Empty/future states

```txt
Windows-сборка готовится
Мы покажем ссылку здесь, когда канал будет открыт для установки.
```

Не писать “готово”, если не готово.

---

## 6.7 Support `/support/`

### Цель

Снизить тревогу и дать быстрый контакт.

### Blocks

- Quick issue cards:
  - не подключается;
  - продление;
  - устройство;
  - другое.
- Ticket/thread area.
- Telegram/support CTA.
- “Что приложить к обращению” helper.

### Tone

Спокойный, без “мы уже всё чиним”, если это не факт.

---

## 6.8 Settings `/settings/`

### Blocks

- Account identity.
- Telegram link/reward.
- Security/session.
- Theme preference.
- Notifications if available.
- Danger zone hidden/collapsed.

---

## 6.9 Redeem `/redeem/`

### Goal

Очень простой activation funnel.

### UX

- Big input.
- One CTA.
- Clear valid/invalid state.
- Success state with next action.
- No technical error dump.

---

## 6.10 Checkout continuation `/subscription/checkout/`

### Goal

Пользователь не чувствует, что его выкинуло в чужой процесс.

### UX

- Plan summary.
- Payment step.
- Trust/safety note.
- Back to subscription.
- Loading state for payment status.

---

# 7. Loading & perceived performance spec

## 7.1 Правило

```txt
Full-screen loading is allowed only when no useful shell or cached content can be shown.
```

В остальных случаях:

- shell stays;
- content skeleton;
- top activity indicator;
- cached snapshot;
- local optimistic UI where safe.

## 7.2 Cold start loader

### Visual

- White/milk background.
- One glass card.
- Brand mark/wordmark.
- Three real-ish status lines, no fake progress:

```txt
Открываем кабинет
Проверяем сессию
Готовим данные доступа
```

Но если этапы не настоящие, не делать их как последовательную “галочку”. Лучше:

```txt
Открываем кабинет POKROV
Проверяем сессию и готовим ваш экран.
```

### Bad copy

```txt
Подтягиваем кабинет
Собираем ваши данные
Загрузка 73%
Почти готово
```

### Good copy

```txt
Открываем кабинет
Проверяем сессию и загружаем актуальные данные доступа.
```

## 7.3 Route transition inside cabinet

- No screen takeover.
- Nav item immediately shows active/pending intent.
- Top bar appears within 100ms if route transition takes longer than 150ms.
- Skeleton only for changed content region.
- Minimum skeleton display should be low; avoid forced delays.

## 7.4 Session snapshot

If allowed:

```ts
const SNAPSHOT_TTL_MS = 5 * 60 * 1000;
```

Store:

- user display name;
- subscription status;
- days left;
- devices summary;
- last updated timestamp.

Do not store:

- raw tokens;
- secrets;
- payment sensitive data;
- raw configs.

UI label:

```txt
Показываем сохранённые данные · обновляем
```

## 7.5 Prefetch strategy

- Use normal Next `<Link>` for route navigation.
- Prefetch likely next routes:
  - dashboard → downloads/devices/subscription;
  - subscription → checkout;
  - downloads → devices/support.
- Manual `router.prefetch()` on hover/focus for sidebar/mobile nav.
- Do not prefetch admin heavy routes unnecessarily.

## 7.6 Performance budgets

Targets:

- LCP: under 2.5s on reasonable mobile connection.
- INP: under 200ms.
- CLS: under 0.1.
- Route transition perceived response: visual feedback under 150ms.
- No skeleton-only screen longer than needed.

## 7.7 Diagnostics

Add a dev-only timing panel or console marks:

```ts
performance.mark('pokrov:session:start')
performance.mark('pokrov:session:ready')
performance.mark('pokrov:dashboard:ready')
```

Then measure:

- auth session fetch;
- dashboard fetch;
- user fetch;
- first paint after shell;
- route transition duration.

---

# 8. Motion system

## 8.1 Libraries

### Use Motion/Framer Motion for webapp

Good for:

- nav indicator;
- card entrance;
- hover/tap;
- modal/drawer;
- route content fade/slide;
- skeleton shimmer if not pure CSS.

### Use GSAP mostly for marketing

Good for:

- hero parallax;
- scroll-triggered reveal;
- premium background choreography;
- complex timeline.

Do not import GSAP into every cabinet page unless there is a clear reason.

## 8.2 Motion tokens

```txt
instant: 80ms
fast: 140ms
base: 220ms
slow: 360ms
hero: 700ms

standard ease: cubic-bezier(0.2, 0.8, 0.2, 1)
enter ease: cubic-bezier(0.16, 1, 0.3, 1)
exit ease: cubic-bezier(0.7, 0, 0.84, 0)
```

## 8.3 Patterns

### Card hover

```txt
translateY: -2px
shadow: elevated
border: slightly stronger mint/emerald alpha
scale: never above 1.01 in cabinet
```

### Page content enter

```txt
opacity 0 → 1
translateY 8px → 0
220ms
```

### Nav active pill

Use layout animation, but reduced-motion fallback = instant active style.

### Hero glow

Slow breathing glow is allowed on marketing and entry screen. In cabinet use static/subtle.

### Skeleton

Shimmer low contrast, 1.2–1.8s, disabled in reduced motion.

## 8.4 Reduced motion

If `prefers-reduced-motion`:

- disable parallax;
- disable shimmer movement;
- remove large translate/scale;
- keep opacity transitions or instant states;
- no endless animated background.

---

# 9. Visual design tokens draft

This is a starting point, not final brand law.

## 9.1 Color direction

```txt
canvas: warm white / green-tinted white
surface: pure/milk white
surface elevated: translucent white
ink: deep green-black
muted ink: gray-green
primary: deep emerald
accent: mint
success: emerald
warning: warm amber
danger: soft red
admin info: blue-gray, but restrained
```

## 9.2 Example CSS/Tailwind v4 theme draft

```css
@theme {
  --color-pokrov-canvas: oklch(98.4% 0.018 151);
  --color-pokrov-canvas-warm: oklch(97.8% 0.016 92);
  --color-pokrov-surface: oklch(99.2% 0.006 120);
  --color-pokrov-surface-glass: color-mix(in oklab, white 82%, transparent);

  --color-pokrov-ink: oklch(22% 0.038 164);
  --color-pokrov-muted: oklch(52% 0.035 160);
  --color-pokrov-faint: oklch(74% 0.028 155);

  --color-pokrov-primary: oklch(43% 0.118 160);
  --color-pokrov-primary-dark: oklch(30% 0.086 162);
  --color-pokrov-mint: oklch(84% 0.142 156);
  --color-pokrov-mint-soft: oklch(93% 0.07 154);
  --color-pokrov-gold: oklch(83% 0.09 86);

  --radius-pokrov-sm: 12px;
  --radius-pokrov-md: 16px;
  --radius-pokrov-lg: 22px;
  --radius-pokrov-xl: 28px;
  --radius-pokrov-2xl: 36px;

  --shadow-pokrov-soft: 0 14px 45px rgb(15 77 55 / 0.08);
  --shadow-pokrov-card: 0 20px 70px rgb(15 77 55 / 0.12);
  --shadow-pokrov-float: 0 28px 90px rgb(15 77 55 / 0.16);
}
```

## 9.3 Typography

### Direction

- Cyrillic must look excellent.
- Use system stack or a carefully chosen font with strong Cyrillic.
- Avoid overly “startup-generic” thin fonts.
- Headings: calm, strong, slightly tight.
- Body: high readability.

### Scale

```txt
Display: 44–56 desktop / 32–38 mobile
H1: 34–42 desktop / 28–32 mobile
H2: 26–32 desktop / 22–26 mobile
H3: 20–24
Body: 15–17
Small: 13–14
Caption: 12–13
```

### Rules

- No walls of center-aligned text in cabinet.
- Numbers use tabular alignment where needed.
- Admin tables use compact but readable density.
- Helper text max width 60–72 characters.

## 9.4 Radii

```txt
button: 14–16
input: 16
small card: 18–20
main card: 24–28
hero panel: 32–36
modal/drawer: 28–32
```

## 9.5 Shadows

Use layered soft shadows, not black heavy shadows.

```css
box-shadow:
  0 1px 1px rgb(15 77 55 / 0.03),
  0 16px 50px rgb(15 77 55 / 0.10);
```

## 9.6 Background system

Allowed:

- radial mint glow;
- subtle atlas grid;
- blurred orb behind hero;
- very low-opacity noise if it does not dirty text;
- glass edge highlight.

Not allowed:

- loud mesh gradients everywhere;
- blur over text;
- animated background behind dense tables;
- random decorative dots without purpose.

---

# 10. Component inventory

## AppShell

- Persistent layout.
- Sidebar desktop.
- Bottom/nav drawer mobile.
- User summary.
- Status badge.
- Theme/control area.

## PageHeader

Props:

```ts
type PageHeaderProps = {
  eyebrow?: string;
  title: string;
  description?: string;
  primaryAction?: ReactNode;
  secondaryAction?: ReactNode;
  status?: ReactNode;
};
```

## HeroStatusCard

Used on dashboard/subscription.

States:

- active;
- trial;
- expiring;
- expired;
- unknown/loading.

## BentoCard

Variants:

- default;
- glass;
- elevated;
- outline;
- admin;
- danger.

## MetricTile

- label;
- value;
- delta/helper;
- icon;
- status.

## ActionCard

- title;
- description;
- icon/illustration;
- CTA;
- secondary link.

## DeviceCard

- platform;
- name;
- status;
- last seen;
- actions;
- details drawer.

## SubscriptionMeter

- days left;
- total period;
- variant active/expiring/expired.

## DownloadCard

- platform;
- channel;
- availability;
- version;
- CTA;
- install steps.

## SupportIssueCard

- issue category;
- expected response path;
- CTA.

## AdminDataTable

- filters;
- search;
- density;
- sticky header;
- row actions;
- loading rows;
- empty state.

## SkeletonBlock

Shapes:

- page header;
- hero;
- card grid;
- table;
- form;
- device list.

---

# 11. Copy system

## 11.1 Tone

- Calm.
- Precise.
- Human.
- No clown energy.
- No fake cheerfulness.
- No technical dump on user pages.

## 11.2 Good phrases

```txt
Доступ активен
Осталось 12 дней
Подключите первое устройство
Скачайте приложение для Windows
Откройте кабинет
Обновляем данные
Показываем сохранённые данные
Нужна помощь с подключением?
```

## 11.3 Bad phrases

```txt
Подтягиваем кабинет
Собираем ваши данные
Почти готово
Магически защищаем всё
VPN супер быстрый без ограничений
Runtime core v3.1.8 active
```

## 11.4 Loading copy variants

Cold start:

```txt
Открываем кабинет
Проверяем сессию и загружаем актуальные данные доступа.
```

Route pending:

```txt
Обновляем экран…
```

Cached dashboard:

```txt
Показываем сохранённые данные · обновляем
```

Error:

```txt
Не удалось загрузить данные
Проверьте соединение или повторите попытку. Если ошибка сохранится, напишите в поддержку.
```

---

# 12. Concrete implementation plan

## Phase 0 — Safety & audit

1. Create branch:

```bash
git checkout -b design/atlas-glass-webapp-reset
```

2. Read in order:

```txt
AGENTS.md
DESIGN.md
webapp/README.md
POKROV-app/DESIGN.md
marketing/README.md if exists
```

3. Mojibake scan:

```bash
rg "Р|С" webapp/src marketing/src shared docs
```

4. Route inventory:

```bash
find webapp/src/app -maxdepth 3 -type f | sort
find webapp/src/components -maxdepth 2 -type f | sort
```

5. Baseline screenshots:

- marketing desktop/mobile;
- app entry;
- dashboard;
- subscription;
- devices;
- downloads;
- support;
- settings;
- redeem;
- admin dashboard/users.

6. Baseline perf:

- Lighthouse or equivalent;
- Web Vitals if available;
- Playwright route smoke.

## Phase 1 — Tokens and primitives

1. Update shared tokens.
2. Update CSS variables.
3. Add base background system.
4. Build UI primitives.
5. Replace ad-hoc cards/buttons gradually.
6. Verify no visual regression catastrophic.

## Phase 2 — Shell and loading

1. Replace `loading.tsx`.
2. Refactor `cabinet-shell` loading branch.
3. Implement route activity indicator.
4. Implement content skeletons.
5. Add prefetch on nav.
6. Add snapshot if permitted.
7. Test slow network manually.

## Phase 3 — Cabinet pages

Order:

1. dashboard;
2. subscription;
3. downloads;
4. devices;
5. support;
6. redeem;
7. settings;
8. statistics;
9. checkout.

Why this order: dashboard and downloads are highest perception impact.

## Phase 4 — Marketing continuity

1. Match base tokens.
2. Rebuild hero if necessary.
3. Add premium background/motion.
4. Improve device/install/public pages.
5. Make checkout continuation feel native.

## Phase 5 — Admin density

1. Admin shell density mode.
2. Tables and cards.
3. Loading rows.
4. Empty/error states.
5. Risk/status visual language.

## Phase 6 — QA and hardening

1. Build webapp.
2. Build marketing.
3. Run Playwright.
4. Run typecheck/lint if available.
5. Run mojibake scanner.
6. Manual mobile QA.
7. Reduced motion QA.
8. Keyboard QA.
9. Dark mode QA if present.

---

# 13. Worker prompts

## Prompt for Worker 1

```txt
Ты Worker 1 по POKROV UI reset. Твоя задача — tokens & primitives.

Сначала прочитай AGENTS.md, DESIGN.md, webapp/README.md, shared/design-tokens.json, webapp/src/app/globals.css, marketing/src/app/globals.css.

Не меняй бизнес-логику и API. Не трогай auth. Не добавляй случайные цвета.

Сделай POKROV Atlas Glass foundation:
- calm premium light canvas;
- white/milk surfaces;
- emerald/mint accent;
- large radii;
- soft shadows;
- readable Cyrillic typography;
- reduced motion compatibility.

Создай/обнови primitives: Surface, GlassPanel, BentoCard, MetricTile, ActionCard, StatusBadge, ProgressMeter, SkeletonBlock, PageHeader, EmptyState, ErrorState.

После изменений дай diff summary, список измененных файлов, и что осталось для Worker 2.
```

## Prompt for Worker 2

```txt
Ты Worker 2 по POKROV UI reset. Твоя задача — shell, loading, route transitions.

Изучи:
- webapp/src/app/loading.tsx
- webapp/src/app/template.tsx
- webapp/src/components/cabinet-shell.tsx
- webapp/src/components/route-transition.tsx
- webapp/src/lib/session.tsx

P0: исправь mojibake. Никаких строк вида РѕС... в UI.

Сделай так, чтобы при переходах внутри кабинета shell не исчезал. Full-screen loader допускается только на cold start, когда нет полезного shell/snapshot.

Добавь:
- честный InitialBootstrapScreen;
- content skeletons;
- top route activity indicator без fake percent;
- reduced-motion safe behavior;
- prefetch на nav hover/focus, если безопасно;
- stale snapshot только если не хранит sensitive данные.

Не ломай auth/API. После изменений проверь dashboard/devices/subscription/downloads/support/settings/redeem.
```

## Prompt for Worker 3

```txt
Ты Worker 3 по POKROV UI reset. Твоя задача — redesign user cabinet pages.

Используй primitives от Worker 1 и loading model от Worker 2.

Переделай страницы:
/dashboard
/subscription
/devices
/statistics
/downloads
/support
/settings
/redeem
/subscription/checkout

Каждая страница должна иметь:
- clear heading;
- one primary action;
- premium card layout;
- responsive mobile layout;
- skeleton/empty/error state;
- no mojibake;
- no raw transport jargon on first level.

Dashboard сделать как Access Cockpit: status, days left, next action, devices, downloads, support.

Downloads делать честно по статусу Android/Windows. Не обещать release, если он gated/beta.
```

## Prompt for Worker 4

```txt
Ты Worker 4 по POKROV UI reset. Твоя задача — marketing and public continuity.

Изучи marketing app, current homepage, DESIGN.md and AGENTS.md.

Сделай public site визуально совместимым с webapp, но с большим вау:
- premium hero;
- subtle atlas grid;
- emerald/mint glass visuals;
- app-first language;
- GSAP только для реально полезных hero/scroll effects;
- reduced motion mandatory.

Не используй public copy, которая нарушает правило no raw VPN positioning. Не обещай неподтвержденные релизы Android/Windows.

Checkout/public continuation должен ощущаться как тот же продукт.
```

## Prompt for Worker 5

```txt
Ты Worker 5 по POKROV UI reset. Твоя задача — admin, QA, visual regression.

Сделай admin density mode:
- плотные tables;
- filters;
- status badges;
- sticky headers;
- row actions;
- skeleton rows;
- empty/error states;
- risk indicators.

Затем QA:
- build webapp;
- build marketing;
- Playwright smoke;
- route screenshots;
- mojibake scan;
- reduced motion check;
- mobile check;
- keyboard/focus check.

Сформируй финальный QA report: что работает, что сломано, что блокирует release.
```

---

# 14. Questions for owner — много, но по делу

## 14.1 Brand / вкус

1. POKROV должен ощущаться как **премиальный банк**, **Linear-like SaaS**, **Apple settings app**, **Telegram-native utility** или **security control center**?
2. Какая эмоция важнее: “я защищен”, “я контролирую”, “это красиво”, “это просто”, “это надежно”?
3. Насколько можно делать интерфейс “дорогим”: glass, blur, glow, gradients — low, medium, high?
4. Есть ли брендовые цвета, которые нельзя менять?
5. Нужно ли показывать POKROV как технологичный продукт или как спокойный бытовой сервис?
6. В кабинете должен быть “вау” или только на marketing?
7. Какая визуальная крайность запрещена: cyberpunk, crypto, banking, childish, gamer, corporate?
8. Нужна ли dark theme как обязательная часть v1?
9. Можно ли использовать abstract 3D/AI-generated assets?
10. Логотип/wordmark можно переработать в рамках UI или нельзя трогать?

## 14.2 Пользователь и сценарии

1. Кто чаще всего заходит в кабинет?
2. Откуда он приходит: Telegram, сайт, checkout, приложение, support?
3. Какой первый сценарий самый важный?
4. Что пользователь делает чаще: продлевает, скачивает, подключает, проверяет статус, пишет в поддержку?
5. Пользователь обычно на телефоне или десктопе?
6. Есть ли много неопытных пользователей?
7. Нужно ли объяснять, что такое “доступ”, “устройство”, “ключ”?
8. Есть ли пользователи без Telegram?
9. Нужно ли делать onboarding checklist?
10. Что должно быть на dashboard, если у пользователя нет активного доступа?

## 14.3 Подписка / деньги

1. Какие тарифы реально есть сейчас?
2. Есть ли автопродление?
3. Как показывать trial?
4. Как показывать Telegram +10 дней?
5. Есть ли история платежей?
6. Есть ли промокоды/redeem?
7. Какие ошибки оплаты бывают чаще всего?
8. Какой тон у истечения подписки: мягкий reminder или заметный warning?
9. Можно ли показывать “осталось X дней” крупно?
10. Нужна ли email/Telegram notification preference?

## 14.4 Devices / downloads

1. Какие платформы реально доступны публично на дату релиза?
2. Android — public, internal beta, gated или coming soon?
3. Windows — signed/unsigned/gated/beta?
4. Нужно ли показывать версии сборок?
5. Можно ли показывать release notes?
6. Какие device statuses есть в API?
7. Можно ли revoke device?
8. Можно ли rename device?
9. Есть ли device limit?
10. Как объяснять “подключить устройство” новичку?

## 14.5 Support

1. Где живет поддержка: Telegram, web tickets, email?
2. Какие 5 самых частых проблем?
3. Нужно ли собирать диагностику из приложения?
4. Можно ли показывать SLA/ожидание ответа?
5. Нужен ли support chatbot или только формы?
6. Что пользователь должен приложить при проблеме?
7. Нужна ли история обращений?
8. Какие статусы тикета?
9. Нужно ли отделять billing support от technical support?
10. Какие тексты нельзя писать в support?

## 14.6 Performance / loading

1. Можно ли кешировать dashboard snapshot в браузере?
2. Какие поля sensitive?
3. Есть ли endpoint для batch dashboard payload?
4. Почему сейчас загрузка 2–3 секунды: API, auth, JS bundle, route transition, static export?
5. Можно ли менять API sequence?
6. Нужно ли показывать offline state?
7. Можно ли сделать optimistic UI?
8. Есть ли analytics по long loading?
9. Какая максимальная приемлемая задержка для владельца?
10. Нужен ли dev timing overlay?

## 14.7 Admin

1. Кто пользуется админкой?
2. Какие действия самые частые?
3. Какая таблица самая важная?
4. Какие статусы критичны?
5. Какие действия опасны и требуют confirm?
6. Нужно ли audit log?
7. Нужна ли role-based visibility?
8. Нужно ли dark/compact mode для admin?
9. Какие метрики должны быть на admin dashboard?
10. Какие ошибки оператора сейчас самые частые?

## 14.8 Release / QA

1. Какие routes должны быть pixel-perfect в v1?
2. Где можно оставить legacy UI на время?
3. Какие страницы нельзя ломать ни при каких обстоятельствах?
4. Есть ли staging?
5. Кто принимает дизайн?
6. Есть ли screenshot review process?
7. Какие тесты обязательны перед merge?
8. Нужно ли обновлять docs после каждого UI change?
10. Что считается “вау” по мнению владельца: скрин, ощущение скорости, анимация, удобство?

---

# 15. Image generation prompts

Использовать для style tiles, декоративных ассетов, background elements. Не генерировать интерфейс целиком как финальный дизайн — только mood/visual assets.

## Prompt 1 — abstract atlas orb, transparent

```txt
Generate a premium abstract translucent glass orb for a calm cybersecurity app named POKROV. Emerald and mint inner glow, soft refractions, subtle atlas/grid reflections, rounded organic shape, no text, no logo, no UI, isolated object, transparent background, high-end product design, minimal, clean.
```

## Prompt 2 — white background hero visual

```txt
Create a clean premium hero background for a modern app dashboard: warm white canvas, subtle emerald and mint radial glow, faint atlas grid, soft glass panels floating in depth, no text, no logo, no people, no devices, lots of whitespace, elegant, calm, high-end SaaS aesthetic.
```

## Prompt 3 — device cards illustration

```txt
Generate a minimal premium illustration of two abstract devices represented as rounded glass cards, one mobile and one desktop, emerald/mint accents, soft shadows, white background, no text, no brand names, no UI details, calm secure feeling, modern product illustration.
```

## Prompt 4 — admin operational background

```txt
Create a subtle abstract background for an admin operations dashboard: light canvas, faint structured grid, very soft blue-green status lights, minimal depth, no text, no UI, no charts, clean and professional, suitable behind dense tables.
```

---

# 16. QA checklist

## Visual

- [ ] No mojibake anywhere.
- [ ] No random hex colors outside token layer unless justified.
- [ ] Consistent radius scale.
- [ ] Consistent shadows.
- [ ] Cyrillic typography looks good.
- [ ] Cards do not look like generic Tailwind boxes.
- [ ] Mobile layout is intentionally designed, not squeezed.
- [ ] Admin density differs from consumer cabinet.

## UX

- [ ] Dashboard answers status/days/action/device questions quickly.
- [ ] Every page has primary action.
- [ ] Empty states are useful.
- [ ] Error states have retry/help.
- [ ] Loading states match page shape.
- [ ] No fake progress.
- [ ] Route transitions do not reset shell.
- [ ] Checkout continuation feels native.

## Accessibility

- [ ] Keyboard navigation works.
- [ ] Focus visible.
- [ ] Reduced motion respected.
- [ ] Contrast acceptable.
- [ ] Loading status uses accessible text/aria-live where needed.
- [ ] Buttons/links have clear labels.
- [ ] Touch targets reasonable on mobile.

## Performance

- [ ] No heavy animated blur behind text.
- [ ] No unnecessary GSAP in cabinet.
- [ ] Route feedback under 150ms.
- [ ] LCP target under 2.5s.
- [ ] INP target under 200ms.
- [ ] CLS target under 0.1.
- [ ] No sequential fetch chain if avoidable.
- [ ] Prefetch strategy checked.

## Product truth

- [ ] No unsupported Android/Windows release claims.
- [ ] Public language does not drift into raw technical positioning.
- [ ] Trial/bonus copy accurate.
- [ ] Admin labels can be technical, user labels human.
- [ ] Sensitive data not cached accidentally.

## Build/test

- [ ] `npm run build` webapp passes.
- [ ] `npm run build` marketing passes.
- [ ] Playwright smoke passes.
- [ ] Manual route smoke passes.
- [ ] Mojibake scan passes.
- [ ] Screenshots captured before/after.

---

# 17. Definition of Done

Редизайн считается выполненным, если:

1. Первый вход в кабинет выглядит premium and calm.
2. Внутренние переходы не показывают full-screen fake loader.
3. Все русские тексты читаемые, без mojibake.
4. Dashboard дает понятный next action.
5. Downloads честно показывает состояние платформ.
6. Devices/subscription/support/settings выглядят как части одного продукта.
7. Admin стал плотнее и полезнее, а не просто “красивее”.
8. Motion работает мягко и уважает reduced motion.
9. Marketing и cabinet визуально совместимы.
10. Все critical routes проходят build/smoke.
11. Нет копирования Neuform — только самостоятельный POKROV direction.

---

# 18. Sources and references used for this brief

## Project sources

- `Kiwunaka/portal` GitHub repo — root workspace, product facts, package layout.
- `portal/DESIGN.md` — calm, premium, reliable, practical brand direction; tokens source of truth.
- `portal/AGENTS.md` — product rules, public wording constraints, must-read docs.
- `portal/webapp/README.md` — webapp route map, runtime contract, build verification.
- `portal/webapp/package.json` — Next/React/Tailwind/Motion/Playwright stack.
- `portal/webapp/src/app/loading.tsx` — current mojibake loading copy.
- `portal/webapp/src/components/cabinet-shell.tsx` — current shell/loading/error structure.
- `portal/webapp/src/lib/session.tsx` — current session loading/fetch logic.
- `portal/marketing/package.json` — marketing stack including GSAP.
- `Kiwunaka/POKROV-app/DESIGN.md` — client app design principles: calm, premium, operationally honest, reduced motion.
- `Kiwunaka/POKROV-app/docs/browser-frontend-map.md` — front-end rebuild and browser handoff context.

## External design / frontend references

- Neuform Capital Overview Dashboard — user-provided visual reference.
- Neuform NovaEstate Dashboard — user-provided visual reference.
- Next.js docs: loading UI and streaming.
- Next.js docs: Link/prefetch behavior.
- Motion docs: `useReducedMotion` and reduced-motion behavior.
- GSAP docs: `gsap.matchMedia()` and accessibility/reduced motion.
- Tailwind CSS v4 docs: theme variables and CSS variables.
- shadcn/ui docs: component distribution and design-system foundation.
- Radix UI docs: accessible primitives.
- web.dev Core Web Vitals: LCP, INP, CLS targets.
- Mobbin: dashboard/web app reference library.
- Linear: dashboard/data visualization best-practice inspiration.

---

# 19. Final taste rule

Before merging any UI change, ask:

```txt
Does this screen feel like a premium product that calmly protects the user’s access,
or like a generic Tailwind admin panel with green paint?
```

If the answer is the second — redo.
