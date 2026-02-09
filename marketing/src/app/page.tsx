"use client";

import { useEffect, useRef, useState } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

const TG_BOT_URL = "https://t.me/swazist_bot";

// ======= DATA =======
const FEATURES = [
  { icon: '⚡', title: 'Мгновенное подключение', desc: 'Получите ключ через Telegram-бота и подключитесь за 60 секунд. Никаких сложных настроек.', num: '01' },
  { icon: '🌍', title: '15+ локаций', desc: 'Переключайтесь между серверами в разных странах одним нажатием. Европа, Азия, Америка.', num: '02' },
  { icon: '🔒', title: 'Шифрование данных', desc: 'Военный уровень защиты. Ваш трафик невозможно перехватить или расшифровать.', num: '03' },
  { icon: '📱', title: 'До 5 устройств', desc: 'Один ключ работает на телефоне, планшете, компьютере. Вся семья под защитой.', num: '04' },
  { icon: '💬', title: 'Поддержка 24/7', desc: 'Быстрые ответы в Telegram. Диагностика, помощь с настройкой, решение проблем.', num: '05' },
  { icon: '🤖', title: 'Telegram-интеграция', desc: 'Управляйте подпиской, меняйте локации и получайте новые ключи прямо в мессенджере.', num: '06' }
];

const GLOW_ICONS = ['🔐', '🛡️', '⚡', '🌐', '🔒', '✨', '💠', '🚀'];

const PLANS = [
  { emoji: '🆓', name: 'Стартовый', desc: '1 страна, до 40 ГБ, базовый сценарий использования', price: '0 ⭐', note: 'Бесплатно навсегда', tag: '' },
  { emoji: '🔥', name: '3 месяца', desc: 'Полный доступ, все локации, до 5 устройств', price: '499 ⭐', note: '~166 ⭐/мес', tag: 'ХИТ' },
  { emoji: '💎', name: '12 месяцев', desc: 'Максимальная экономия, приоритетная стабильность', price: '1499 ⭐', note: '~125 ⭐/мес — ВЫГОДА', tag: 'ЭКОНОМИЯ' }
];

const TESTIMONIALS = [
  { stars: '★★★★★', text: '"Сервис работает стабильно, переключение стран без ручной рутины. Впечатление премиум-уровня."', author: 'Алексей', role: 'Product Lead' },
  { stars: '★★★★★', text: '"Отдельно нравится диагностика и понятный личный кабинет внутри Telegram."', author: 'Ирина', role: 'Founder' },
  { stars: '★★★★★', text: '"Подключил семью за вечер: единый ключ, быстрые инструкции, прозрачная оплата."', author: 'Михаил', role: 'CTO' },
  { stars: '★★★★★', text: '"Наконец-то нормальный сервис без VPN-лагов. Работает даже в Китае."', author: 'Дмитрий', role: 'Digital Nomad' },
  { stars: '★★★★★', text: '"Поддержка ответила за 5 минут и помогла настроить на всех устройствах."', author: 'Анна', role: 'Designer' },
  { stars: '★★★★☆', text: '"Использую полгода — ни одного разрыва соединения. Рекомендую."', author: 'Сергей', role: 'Developer' }
];

const FAQS = [
  { q: 'Как получить доступ?', a: 'Напишите нашему Telegram-боту @swazist_bot, выберите тариф и получите персональный ключ. Весь процесс занимает меньше минуты.' },
  { q: 'Какие устройства поддерживаются?', a: 'iOS, Android, Windows, macOS, Linux. Один ключ работает на всех ваших устройствах одновременно — до 5 штук.' },
  { q: 'Можно ли вернуть деньги?', a: 'Да, в течение 7 дней после оплаты вы можете запросить полный возврат через Telegram-бота без объяснения причин.' },
  { q: 'Сохраняются ли логи?', a: 'Мы не храним историю посещений и не ведём логи активности. Только минимум данных для работы сервиса.' },
  { q: 'Что если сервер не работает?', a: 'У нас 15+ локаций и автоматическое переключение. Если один узел недоступен — просто выберите другой в личном кабинете.' },
  { q: 'Есть ли пробный период?', a: 'Стартовый тариф бесплатен навсегда. Попробуйте сервис без риска и решите, нужен ли вам расширенный доступ.' }
];

const MARQUEE_ITEMS = [
  '🔒', 'ENCRYPTED', '⚡', 'FAST', '🛡️', 'SECURE', '🌐', 'GLOBAL', '🔐', 'PRIVATE',
  '💎', 'PREMIUM', '🚀', 'STABLE', '🔒', 'NO LOGS', '⚡', '24/7', '🛡️', 'PORTAL'
];

// ======= COMPONENTS =======

function Cursor() {
  const cursorRef = useRef<HTMLDivElement>(null);
  const dotRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cx = 0, cy = 0, dx = 0, dy = 0;

    const handleMouseMove = (e: MouseEvent) => {
      cx = e.clientX;
      cy = e.clientY;
    };

    const animate = () => {
      dx += (cx - dx) * 0.15;
      dy += (cy - dy) * 0.15;
      if (cursorRef.current) {
        cursorRef.current.style.left = dx + 'px';
        cursorRef.current.style.top = dy + 'px';
      }
      if (dotRef.current) {
        dotRef.current.style.left = cx + 'px';
        dotRef.current.style.top = cy + 'px';
      }
      requestAnimationFrame(animate);
    };

    document.addEventListener('mousemove', handleMouseMove);
    animate();

    // Hover effects
    const addHover = () => cursorRef.current?.classList.add('hover');
    const removeHover = () => cursorRef.current?.classList.remove('hover');

    document.querySelectorAll('a, button, .faq-item, .plan-card, .cta-btn, .feature-card').forEach(el => {
      el.addEventListener('mouseenter', addHover);
      el.addEventListener('mouseleave', removeHover);
    });

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
    };
  }, []);

  return (
    <>
      <div className="cursor" ref={cursorRef} />
      <div className="cursor-dot" ref={dotRef} />
    </>
  );
}

function Preloader({ onComplete }: { onComplete: () => void }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const textRef = useRef<HTMLDivElement>(null);
  const fillRef = useRef<HTMLDivElement>(null);
  const iconRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    gsap.registerPlugin(ScrollTrigger);

    const text = 'UNLOCKING SECURE NETWORK...';
    if (textRef.current) {
      textRef.current.innerHTML = text.split('').map(ch =>
        `<span>${ch === ' ' ? '\u00A0' : ch}</span>`
      ).join('');
    }

    const tl = gsap.timeline({
      onComplete: () => {
        gsap.to(containerRef.current, {
          yPercent: -100,
          duration: 0.8,
          ease: 'power4.inOut',
          onComplete: () => {
            if (containerRef.current) {
              containerRef.current.style.display = 'none';
            }
            onComplete();
          }
        });
      }
    });

    tl.to(iconRef.current, { opacity: 1, scale: 1, rotation: 360, duration: 0.6, ease: 'back.out(1.7)' })
      .to(textRef.current?.querySelectorAll('span') || [], { opacity: 1, y: 0, stagger: 0.02, duration: 0.25, ease: 'power2.out' }, 0.3)
      .to(fillRef.current, { width: '100%', duration: 1.2, ease: 'power2.inOut' }, 0.5)
      .to(iconRef.current, { rotation: 720, scale: 1.3, duration: 0.4, ease: 'power2.in' }, 1.5);
  }, [onComplete]);

  return (
    <div className="preloader" ref={containerRef}>
      <div className="preloader-icon" ref={iconRef}>🔐</div>
      <div className="preloader-text" ref={textRef} />
      <div className="preloader-bar">
        <div className="preloader-fill" ref={fillRef} />
      </div>
    </div>
  );
}

function Hero() {
  const word1Ref = useRef<HTMLSpanElement>(null);
  const word2Ref = useRef<HTMLSpanElement>(null);
  const word3Ref = useRef<HTMLSpanElement>(null);
  const subRef = useRef<HTMLDivElement>(null);
  const badgeRef = useRef<HTMLDivElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const floatingRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const splitIntoChars = (el: HTMLElement, text: string) => {
      el.innerHTML = text.split('').map((ch, i) =>
        `<span class="char" style="--i:${i}">${ch}</span>`
      ).join('');
    };

    const splitIntoWords = (el: HTMLElement, text: string) => {
      el.innerHTML = text.split(' ').map(w =>
        `<span class="word">${w}</span>`
      ).join('');
    };

    if (word1Ref.current) splitIntoChars(word1Ref.current, 'PRIVATE');
    if (word2Ref.current) splitIntoChars(word2Ref.current, 'ROUTING');
    if (word3Ref.current) splitIntoChars(word3Ref.current, 'NETWORK');
    if (subRef.current) splitIntoWords(subRef.current, 'Персональный защищенный канал · Быстрое переключение стран · Стабильная маршрутизация · Поддержка 24/7');

    const tl = gsap.timeline();

    tl.to('.hero-title .line-inner', { y: 0, duration: 1, ease: 'power4.out', stagger: 0.15 })
      .from('#heroWord1 .char', { y: 80, rotationZ: gsap.utils.wrap([-15, 15, -10, 20, -5, 10, -8]), opacity: 0, stagger: 0.06, duration: 0.8, ease: 'back.out(1.7)' }, 0.2)
      .from('#heroWord2 .char', { x: 60, opacity: 0, stagger: 0.05, duration: 0.6, ease: 'power3.out' }, 0.6)
      .from('#heroWord3 .char', { x: -60, opacity: 0, stagger: 0.05, duration: 0.6, ease: 'power3.out' }, 0.8)
      .to(badgeRef.current, { opacity: 1, y: 0, duration: 0.6, ease: 'power2.out' }, 1)
      .to('.hero-sub .word', { opacity: 1, y: 0, stagger: 0.04, duration: 0.5, ease: 'power2.out' }, 1.2)
      .to(scrollRef.current, { opacity: 1, duration: 0.5 }, 1.8);

    // Floating elements
    if (floatingRef.current) {
      for (let i = 0; i < 12; i++) {
        const span = document.createElement('span');
        span.textContent = GLOW_ICONS[i % GLOW_ICONS.length];
        span.style.left = Math.random() * 100 + '%';
        span.style.top = Math.random() * 100 + '%';
        span.style.fontSize = (15 + Math.random() * 30) + 'px';
        floatingRef.current.appendChild(span);

        gsap.to(span, { opacity: gsap.utils.random(0.06, 0.15), duration: 0 });
        gsap.to(span, {
          y: gsap.utils.random(-50, 50),
          x: gsap.utils.random(-30, 30),
          rotation: gsap.utils.random(-20, 20),
          duration: gsap.utils.random(4, 8),
          repeat: -1,
          yoyo: true,
          ease: 'sine.inOut',
          delay: Math.random() * 3
        });
      }
    }

    // Parallax
    gsap.to('#heroWord1', { y: -100, scrollTrigger: { trigger: '.hero', start: 'top top', end: 'bottom top', scrub: 1 } });
    gsap.to('#heroWord2', { y: -60, scrollTrigger: { trigger: '.hero', start: 'top top', end: 'bottom top', scrub: 1 } });
    gsap.to('#heroWord3', { y: -30, scrollTrigger: { trigger: '.hero', start: 'top top', end: 'bottom top', scrub: 1 } });
  }, []);

  return (
    <section className="hero">
      <div className="floating-elements" ref={floatingRef} />
      <div className="hero-badge" ref={badgeRef}>🚀 Доступ по всему миру</div>
      <div className="hero-title">
        <span className="line"><span className="line-inner hero-word-1" id="heroWord1" ref={word1Ref} /></span>
        <span className="line"><span className="line-inner hero-word-2" id="heroWord2" ref={word2Ref} /></span>
        <span className="line"><span className="line-inner hero-word-3" id="heroWord3" ref={word3Ref} /></span>
      </div>
      <div className="hero-sub" ref={subRef} />
      <div className="hero-scroll" ref={scrollRef}>
        <span>Прокрутите вниз</span>
        <div className="arrow" />
      </div>
    </section>
  );
}

function Marquee() {
  const items = [...MARQUEE_ITEMS, ...MARQUEE_ITEMS, ...MARQUEE_ITEMS, ...MARQUEE_ITEMS];

  return (
    <div className="marquee-section">
      <div className="marquee-track">
        {items.map((item, i) => {
          const isIcon = /[🔒⚡🛡️🌐🔐💎🚀]/.test(item);
          const isHighlight = ['ENCRYPTED', 'SECURE', 'PRIVATE', 'PORTAL', 'NO LOGS'].includes(item);
          const cls = isIcon ? 'icon' : (isHighlight ? 'highlight' : '');
          return <span key={i} className={cls}>{item}</span>;
        })}
      </div>
    </div>
  );
}

function ScrollScale() {
  useEffect(() => {
    const texts = ['#st1', '#st2', '#st3'];

    ScrollTrigger.create({
      trigger: '#scrollScale',
      start: 'top top',
      end: 'bottom bottom',
      pin: '#scrollPin',
      pinSpacing: false
    });

    texts.forEach((sel, i) => {
      const start = i * 33.33;
      const end = start + 33.33;

      gsap.timeline({
        scrollTrigger: {
          trigger: '#scrollScale',
          start: `${start}% top`,
          end: `${end}% top`,
          scrub: 0.5
        }
      })
        .fromTo(sel, { opacity: 0, scale: 0.3, y: 50 }, { opacity: 1, scale: 1, y: 0, duration: 0.5, ease: 'power2.out' })
        .to(sel, { opacity: 0, scale: 1.5, y: -50, duration: 0.5, ease: 'power2.in' }, 0.5);
    });
  }, []);

  return (
    <section className="scroll-scale" id="scrollScale">
      <div className="scroll-scale-pin" id="scrollPin">
        <div className="scroll-text t1" id="st1">ОДИН КЛЮЧ</div>
        <div className="scroll-text t2" id="st2">ВСЕ УСТРОЙСТВА</div>
        <div className="scroll-text t3" id="st3">БЕЗ ОГРАНИЧЕНИЙ</div>
      </div>
    </section>
  );
}

function Features() {
  useEffect(() => {
    gsap.utils.toArray<HTMLElement>('.feature-card.reveal').forEach(el => {
      gsap.to(el, {
        opacity: 1,
        y: 0,
        duration: 0.8,
        ease: 'power3.out',
        scrollTrigger: { trigger: el, start: 'top 85%', once: true },
        delay: parseFloat(el.style.getPropertyValue('--delay') || '0')
      });
    });
  }, []);

  return (
    <section className="features" id="features">
      <div className="features-header reveal">
        <h2>ЧТО <span className="stroke">ВНУТРИ</span></h2>
        <p>Полный контроль вашей сетевой безопасности</p>
      </div>
      <div className="features-grid">
        {FEATURES.map((f, i) => (
          <div key={i} className="feature-card reveal" style={{ '--delay': `${i * 0.1}s` } as React.CSSProperties}>
            <div className="feature-num">{f.num}</div>
            <span className="feature-icon">{f.icon}</span>
            <h3>{f.title}</h3>
            <p>{f.desc}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function PortalVisualization() {
  const statsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const stats = [
      { target: 99.9, suffix: '%', isFloat: true },
      { target: 15, suffix: '+', isFloat: false },
      { target: 0, suffix: '', isFloat: false }
    ];

    statsRef.current?.querySelectorAll('.stat-num').forEach((el, i) => {
      const stat = stats[i];
      ScrollTrigger.create({
        trigger: el,
        start: 'top 80%',
        once: true,
        onEnter: () => {
          gsap.to({ val: 0 }, {
            val: stat.target,
            duration: 2,
            ease: 'power2.out',
            onUpdate: function () {
              const v = this.targets()[0].val;
              (el as HTMLElement).textContent = (stat.isFloat ? v.toFixed(1) : Math.round(v)) + stat.suffix;
            }
          });
        }
      });
    });

    gsap.utils.toArray<HTMLElement>('.reveal-left, .reveal-right').forEach(el => {
      gsap.to(el, {
        opacity: 1,
        x: 0,
        duration: 1,
        ease: 'power3.out',
        scrollTrigger: { trigger: el, start: 'top 80%', once: true }
      });
    });
  }, []);

  return (
    <section className="portal-section" id="portalSection">
      <div className="portal-vis">
        <div className="portal-art reveal-left">
          <div className="portal-hexagon">
            <div className="portal-glow" />
            <div className="portal-ring" />
            <div className="portal-ring" />
            <div className="portal-ring" />
            <div className="portal-ring" />
            <div className="portal-center">P</div>
          </div>
        </div>
        <div className="portal-info reveal-right" ref={statsRef}>
          <h2>Создан для <em>максимальной</em> <span className="thin">защиты</span></h2>
          <p>
            Шифрование военного уровня. Мгновенное переключение между 15+ локациями.
            Стабильный канал связи с гарантией приватности. Подключайтесь откуда угодно.
            Доверяйте технологиям.
          </p>
          <div className="portal-stats">
            <div className="portal-stat">
              <div className="stat-num">0</div>
              <div className="stat-label">Uptime</div>
            </div>
            <div className="portal-stat">
              <div className="stat-num">0</div>
              <div className="stat-label">Локаций</div>
            </div>
            <div className="portal-stat">
              <div className="stat-num">0</div>
              <div className="stat-label">Логов*</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function Plans() {
  useEffect(() => {
    gsap.utils.toArray<HTMLElement>('.plan-card.reveal').forEach(el => {
      gsap.to(el, {
        opacity: 1,
        y: 0,
        duration: 0.8,
        ease: 'power3.out',
        scrollTrigger: { trigger: el, start: 'top 85%', once: true },
        delay: parseFloat(el.style.getPropertyValue('--delay') || '0')
      });
    });
  }, []);

  return (
    <section className="plans" id="plans">
      <div className="plans-header reveal">
        <h2>ВЫБЕРИТЕ ТАРИФ</h2>
      </div>
      <div className="plans-track">
        {PLANS.map((p, i) => (
          <div key={i} className={`plan-card reveal ${p.tag === 'ХИТ' ? 'hot' : ''}`} style={{ '--delay': `${i * 0.15}s` } as React.CSSProperties}>
            {p.tag && <span className="plan-tag">{p.tag}</span>}
            <span className="plan-emoji">{p.emoji}</span>
            <h3>{p.name}</h3>
            <p className="plan-desc">{p.desc}</p>
            <div className="plan-price">{p.price}</div>
            <div className="plan-note">{p.note}</div>
          </div>
        ))}
      </div>
    </section>
  );
}

function Testimonials() {
  const cards = [...TESTIMONIALS, ...TESTIMONIALS];

  return (
    <section className="testimonials" id="testimonials">
      <h2 className="reveal">ЧТО ГОВОРЯТ <span className="outline">КЛИЕНТЫ</span></h2>
      <div className="test-marquee">
        {cards.map((t, i) => (
          <div key={i} className="test-card">
            <div className="stars">{t.stars}</div>
            <p>{t.text}</p>
            <div className="author">— <span>{t.author}</span>, {t.role}</div>
          </div>
        ))}
      </div>
    </section>
  );
}

function CTA() {
  return (
    <section className="cta-section" id="cta">
      <div className="cta-content">
        <div className="cta-price-label reveal">3 месяца всего за</div>
        <div className="cta-price reveal">
          <span className="currency">⭐</span>499<span className="period">/квартал</span>
        </div>
        <div className="cta-disclaimer reveal">Полный доступ · Все локации · До 5 устройств</div>
        <a href={TG_BOT_URL} target="_blank" rel="noreferrer" className="cta-btn reveal">
          <span className="btn-icon">🚀</span>
          ПОДКЛЮЧИТЬ СЕЙЧАС
        </a>
        <div className="cta-features reveal">
          <span>Мгновенная активация</span>
          <span>Telegram-интеграция</span>
          <span>Поддержка 24/7</span>
          <span>Возврат средств</span>
        </div>
      </div>
    </section>
  );
}

function FAQ() {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  const toggleFaq = (i: number) => {
    setOpenIndex(openIndex === i ? null : i);
  };

  useEffect(() => {
    gsap.utils.toArray<HTMLElement>('.faq-item.reveal').forEach(el => {
      gsap.to(el, {
        opacity: 1,
        y: 0,
        duration: 0.8,
        ease: 'power3.out',
        scrollTrigger: { trigger: el, start: 'top 85%', once: true }
      });
    });
  }, []);

  return (
    <section className="faq" id="faq">
      <h2 className="reveal">FAQ</h2>
      <div>
        {FAQS.map((f, i) => (
          <div key={i} className="faq-item reveal" onClick={() => toggleFaq(i)}>
            <div className="faq-q">
              {f.q}
              <span className={`toggle ${openIndex === i ? 'open' : ''}`}>+</span>
            </div>
            <div className={`faq-a ${openIndex === i ? 'open' : ''}`}>{f.a}</div>
          </div>
        ))}
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="footer">
      <div className="footer-brand">PORTAL<span>.</span></div>
      <div className="footer-links">
        <a href="/offer">Оферта</a>
        <a href="/privacy">Политика конфиденциальности</a>
      </div>
      <div className="footer-legal">
        © {new Date().getFullYear()} PORTAL Network Security. Все права защищены.
        Сервис предоставляет защищённый канал связи для личного использования.
      </div>
    </footer>
  );
}

function Navbar() {
  useEffect(() => {
    let lastY = 0;
    ScrollTrigger.create({
      onUpdate: self => {
        const y = self.scroll();
        if (y > lastY && y > 100) {
          gsap.to('.topbar', { y: -100, duration: 0.4, ease: 'power2.in' });
        } else {
          gsap.to('.topbar', { y: 0, duration: 0.4, ease: 'power2.out' });
        }
        lastY = y;
      }
    });
  }, []);

  return (
    <header className="topbar">
      <div className="brand">PORTAL<span>.</span></div>
      <nav className="topnav">
        <a href="#features">Возможности</a>
        <a href="#plans">Тарифы</a>
        <a href="#faq">FAQ</a>
        <a href={TG_BOT_URL} target="_blank" rel="noreferrer" className="nav-buy">Подключить</a>
      </nav>
    </header>
  );
}

// ======= MAIN PAGE =======
export default function HomePage() {
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    gsap.registerPlugin(ScrollTrigger);
  }, []);

  useEffect(() => {
    if (isLoaded) {
      // Init reveal animations
      gsap.utils.toArray<HTMLElement>('.reveal').forEach(el => {
        gsap.to(el, {
          opacity: 1,
          y: 0,
          duration: 0.8,
          ease: 'power3.out',
          scrollTrigger: { trigger: el, start: 'top 85%', once: true },
          delay: parseFloat(el.style.getPropertyValue('--delay') || '0')
        });
      });
    }
  }, [isLoaded]);

  return (
    <>
      <Cursor />
      <Preloader onComplete={() => setIsLoaded(true)} />
      <Navbar />

      {isLoaded && (
        <main>
          <Hero />
          <Marquee />
          <ScrollScale />
          <Features />
          <PortalVisualization />
          <Plans />
          <Testimonials />
          <CTA />
          <FAQ />
          <Footer />
        </main>
      )}
    </>
  );
}
