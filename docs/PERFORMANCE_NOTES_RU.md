# Performance Notes PORTAL

Обновлено: 6 марта 2026

## Что изменено

- `marketing/src/app/page.tsx` переведён в server-first режим:
  - убран `use client`
  - убраны `useEffect/useState` только ради scroll-state
  - cold CTA больше не создают лишний client-side сценарий через `/checkout`
- `marketing/src/app/checkout/page.tsx`
  - clearer fallback UX без пустого перехода
  - кнопка оплаты блокируется без `checkout_ticket`
- `webapp/src/app/(dashboard)/support/legal/page.tsx`
  - page стала проще и без ненужного client runtime

## Практический эффект

- меньше клиентского JS на marketing home
- меньше ложных переходов в checkout без персональной привязки
- чище первая загрузка и меньше “лишней работы” браузера

## Измерения

### Marketing build
- До: home first load около `101 kB`, checkout около `92 kB`
- После: home `96.3 kB`, checkout `92.1 kB`
- Изменение: home стал легче примерно на `4.7 kB` за счёт server-first home и отказа от client-only scroll logic

### WebApp build
- static export проходит по 23 routes
- критичные страницы `/admin/*`, `/support/legal`, `/subscription/checkout` собираются без ошибок

## Что ещё стоит сделать следующей волной

- убрать внешнюю QR-зависимость из dashboard и перейти на локальную генерацию
- сократить `use client` на части экранов webapp
- вынести тяжёлые admin widgets в dynamic imports
