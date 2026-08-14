# WO-005 — Marketing And SEO Conversion Layer

Status: `IN_PROGRESS`

## Outcome

Мобильный первый экран объясняет результат и ведёт к установке без текстового
полотна; подробности остаются доступными через disclosures и вторичные страницы.

## Acceptance

- H1: `YouTube, TikTok и ChatGPT — одной кнопкой`;
- subtitle: Android/Windows, 5 дней без карты;
- primary CTA direct/platform-aware download, secondary `Как работает`;
- first trust strip: 5 дней, без автосписаний, GitHub Releases + SHA-256, не
  храним историю посещённых сайтов;
- allowed audit-backed claim: без рекламных SDK и сторонних маркетинговых
  трекеров; never claim zero collection or absolute anonymity;
- homepage renders catalog-driven `start_99`, 6m, 12m and `Все тарифы`; all six
  remain in checkout; 99 ₽ copy states first full month/one device/once and next
  normal month 239 ₽;
- bonus mechanics no longer compete with the cold primary purchase decision;
- absolute `лучший VPN*` claims become descriptive intent copy without deleting
  useful indexed pages;
- 320/360/390/768/desktop checks show no clipped CTA, tariff or disclosure.

## No-regression

Do not rebuild the public checkout, remove FAQ/details, introduce fabricated
speed/privacy claims or add third-party analytics dependencies.

## Checks

Copy/release/catalog guards, SEO/schema checks, lint/build, responsive route
matrix and current-run mobile screenshots for visual assertions.

## Current Evidence

- `PASS_LOCAL`: Browser current-run DOM proves the exact H1/subtitle, compact
  trust strip, platform-aware primary action, three homepage plans and the
  separate `Все тарифы` action after a fresh static build.
- `PASS_LOCAL`: homepage no longer promotes the bonus program in the cold
  decision layer; intent pages no longer claim absolute `лучший VPN` status.
- `PASS_LOCAL`: marketing lint/build, SEO and story-contract checks passed on
  the working candidate before final combined gates.
- `PENDING`: repeat responsive matrix and production current-origin Browser
  proof after WO-011 deploy.
