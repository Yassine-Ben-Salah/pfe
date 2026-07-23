import { useEffect, useState } from "react";
import styles from "./HeroSection.module.css";
import { TrustStatsSection } from "./TrustStatsSection";
import { useTranslation } from "../i18n";

interface HeroSectionProps {
  onLoginClick?: () => void;
  onLearnMoreClick?: () => void;
}

export function HeroSection({
  onLoginClick,
  onLearnMoreClick,
}: HeroSectionProps) {
  const [repairCost, setRepairCost] = useState(0);
  const [accuracy, setAccuracy] = useState(0);

  useEffect(() => {
    const duration = 2800;
    const startTime = performance.now();
    let animationFrame = 0;

    const animateCounters = (time: number) => {
      const progress = Math.min((time - startTime) / duration, 1);
      const easedProgress = 1 - Math.pow(1 - progress, 3);

      setRepairCost(Math.round(2450 * easedProgress));
      setAccuracy(Number((96.5 * easedProgress).toFixed(1)));

      if (progress < 1) {
        animationFrame = requestAnimationFrame(animateCounters);
      }
    };

    animationFrame = requestAnimationFrame(animateCounters);

    return () => cancelAnimationFrame(animationFrame);
  }, []);

  const { t } = useTranslation();

  return (
    <section className={styles.hero}>
      <div className={styles.container}>
        <div className={styles.grid}>
          {/* Left Side - Content */}
          <div className={styles.content}>
            <h1 className={styles.headline}>
              {t('hero.headline')}
            </h1>

            <p className={styles.subtitle}>
              {t('hero.subtitle')}
            </p>

            <div className={styles.badges}>
              <span className={styles.badge}>
                <span className={styles.dot}></span>
                {t('hero.badge1')}
              </span>
              <span className={styles.badge}>
                <span className={styles.dot}></span>
                {t('hero.badge2')}
              </span>
              <span className={styles.badge}>
                <span className={styles.dot}></span>
                {t('hero.badge3')}
              </span>
            </div>

            <div className={styles.ctaButtons}>
              <button className={styles.primaryButton} onClick={onLoginClick}>
                {t('hero.login')}
                <span className={styles.arrow}>→</span>
              </button>
              <button
                className={styles.secondaryButton}
                onClick={onLearnMoreClick}
              >
                {t('hero.learnMore')}
              </button>
            </div>
          </div>

          {/* Right Side - Illustration */}
          <div className={styles.illustration}>
            <svg
              viewBox="0 0 600 450"
              xmlns="http://www.w3.org/2000/svg"
              className={styles.illustrationSvg}
            >
              <defs>
                <linearGradient
                  id="carGradient"
                  x1="0%"
                  y1="0%"
                  x2="100%"
                  y2="100%"
                >
                  <stop offset="0%" stopColor="#2563EB" />
                  <stop offset="100%" stopColor="#10B981" />
                </linearGradient>

                <linearGradient id="glass" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#ffffff" stopOpacity=".95" />
                  <stop offset="100%" stopColor="#F3F4F6" />
                </linearGradient>

                <filter id="shadow">
                  <feDropShadow
                    dx="0"
                    dy="8"
                    stdDeviation="8"
                    floodOpacity=".18"
                  />
                </filter>
              </defs>
              {/* Background */}
              <circle cx="500" cy="70" r="80" fill="#2563EB" opacity=".08" />
              <circle cx="120" cy="360" r="100" fill="#10B981" opacity=".08" />
              {/* Radar */}
              <circle
                cx="300"
                cy="200"
                r="120"
                stroke="#2563EB"
                strokeDasharray="8 8"
                strokeWidth="2"
                fill="none"
                opacity=".2"
              />
              <circle
                cx="300"
                cy="200"
                r="90"
                stroke="#10B981"
                strokeDasharray="8 8"
                strokeWidth="2"
                fill="none"
                opacity=".2"
              />
              {/* Car */}
              <g filter="url(#shadow)">
                <path
                  d="
                      M140 245L190 185H395L450 245L470 290H120Z"
                  fill="url(#carGradient)"
                />
                <rect
                  x="165"
                  y="205"
                  width="95"
                  height="45"
                  rx="12"
                  fill="#DBEAFE"
                />

                <rect
                  x="280"
                  y="205"
                  width="95"
                  height="45"
                  rx="12"
                  fill="#DBEAFE"
                />

                <circle cx="180" cy="300" r="34" fill="#1F2937" />
                <circle cx="420" cy="300" r="34" fill="#1F2937" />

                <circle cx="180" cy="300" r="18" fill="#6B7280" />
                <circle cx="420" cy="300" r="18" fill="#6B7280" />
              </g>
              {/* AI SCAN LINE (moving effect) */}
              <line
                x1="120"
                y1="185"
                x2="470"
                y2="185"
                stroke="#10B981"
                strokeWidth="3"
                strokeLinecap="round"
                opacity="0.75"
                className={styles.scanLine}
              />
              {/* Damage */}
              <circle cx="330" cy="245" r="22" fill="#EF4444" opacity=".25" />
              <path
                d="M315 230 L340 245 L325 262 L350 278"
                stroke="#EF4444"
                strokeWidth="3"
                fill="none"
              />
              {/* AI Scanner */}
              <rect
                x="290"
                y="200"
                width="90"
                height="90"
                rx="12"
                fill="none"
                stroke="#10B981"
                strokeWidth="3"
                strokeDasharray="8 6"
              />
              <line
                x1="290"
                y1="230"
                x2="380"
                y2="230"
                stroke="#10B981"
                strokeWidth="2"
              />
              <line
                x1="290"
                y1="250"
                x2="380"
                y2="250"
                stroke="#2563EB"
                strokeWidth="2"
              />
              <line
                x1="290"
                y1="270"
                x2="380"
                y2="270"
                stroke="#10B981"
                strokeWidth="2"
              />
              {/* Cost Card */}
              <g filter="url(#shadow)">
                <rect
                  x="25"
                  y="60"
                  width="150"
                  height="90"
                  rx="18"
                  fill="url(#glass)"
                />

                <text
                  x="45"
                  y="90"
                  fontSize="14"
                  fontWeight="600"
                  fill="#6B7280"
                >
                  {t('hero.repairCost')}
                </text>

                <text
                  x="45"
                  y="125"
                  fontSize="20"
                  fontWeight="700"
                  fill="#10B981"
                >
                  {`${repairCost.toLocaleString()} TND`}
                </text>
              </g>
              {/* Confidence */}
              <g filter="url(#shadow)">
                <rect
                  x="425"
                  y="85"
                  width="150"
                  height="90"
                  rx="18"
                  fill="url(#glass)"
                />

                <text
                  x="445"
                  y="115"
                  fontSize="14"
                  fontWeight="600"
                  fill="#6B7280"
                >
                  {t('hero.aiAccuracy')}
                </text>

                <text
                  x="445"
                  y="150"
                  fontSize="28"
                  fontWeight="700"
                  fill="#2563EB"
                >
                  {accuracy.toFixed(1)}%
                </text>
              </g>
              {/* Constat */}
              <g filter="url(#shadow)">
                <rect
                  x="440"
                  y="270"
                  width="110"
                  height="130"
                  rx="16"
                  fill="white"
                />

                <rect
                  x="460"
                  y="295"
                  width="70"
                  height="6"
                  rx="3"
                  fill="#CBD5E1"
                />
                <rect
                  x="460"
                  y="315"
                  width="60"
                  height="6"
                  rx="3"
                  fill="#CBD5E1"
                />
                <rect
                  x="460"
                  y="335"
                  width="75"
                  height="6"
                  rx="3"
                  fill="#CBD5E1"
                />

                <circle cx="495" cy="370" r="18" fill="#10B981" />

                <text
                  x="489"
                  y="376"
                  fontSize="14"
                  fill="white"
                  fontWeight="bold"
                >
                  ✓
                </text>
              </g>{" "}
            </svg>
          </div>
        </div>
      </div>

      <TrustStatsSection />
    </section>
  );
}
