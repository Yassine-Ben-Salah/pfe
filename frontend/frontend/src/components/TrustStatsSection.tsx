import { useEffect, useRef, useState } from "react";
import styles from "./TrustStatsSection.module.css";
import { useTranslation } from '../i18n';

type Metric = {
  value: number;
  label: string;
  suffix?: string;
  prefix?: string;
  decimals?: number;
};

export function TrustStatsSection() {
  const { t } = useTranslation();

  const metrics: Metric[] = [
    { value: 500, label: t('trust.partners'), suffix: "+" },
    { value: 50000, label: t('trust.assessments'), suffix: "+" },
    { value: 99.8, label: t('trust.accuracy'), suffix: "%", decimals: 1 },
  ];

interface AnimatedNumberProps extends Metric {
  trigger: boolean;
}

function AnimatedNumber({ value, suffix = "", prefix = "", decimals = 0, trigger }: AnimatedNumberProps) {
  const [displayValue, setDisplayValue] = useState(0);
  const [hasAnimated, setHasAnimated] = useState(false);
  const nodeRef = useRef<HTMLSpanElement | null>(null);

  useEffect(() => {
    if (!trigger || hasAnimated) return;

    const node = nodeRef.current;
    if (!node) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (!entry.isIntersecting || hasAnimated) return;

        setHasAnimated(true);
        const startValue = 0;
        const endValue = value;
        const duration = 1400;
        const startTime = performance.now();

        const tick = (currentTime: number) => {
          const progress = Math.min((currentTime - startTime) / duration, 1);
          const easedProgress = 1 - Math.pow(1 - progress, 3);
          const current = Number(
            (startValue + (endValue - startValue) * easedProgress).toFixed(decimals)
          );

          setDisplayValue(current);

          if (progress < 1) {
            requestAnimationFrame(tick);
          }
        };

        requestAnimationFrame(tick);
      },
      { threshold: 0.4, rootMargin: "0px 0px -10% 0px" }
    );

    observer.observe(node);
    return () => observer.disconnect();
  }, [value, decimals, trigger, hasAnimated]);

  return (
    <span ref={nodeRef} className={styles.number}>
      {prefix}
      {displayValue.toLocaleString("en-US", {
        minimumFractionDigits: decimals > 0 ? decimals : 0,
        maximumFractionDigits: decimals > 0 ? decimals : 0,
      })}
      {suffix}
    </span>
  );
}

  const [isVisible, setIsVisible] = useState(false);
  const sectionRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    const node = sectionRef.current;
    if (!node) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          observer.disconnect();
        }
      },
      { threshold: 0.2 }
    );

    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  return (
    <section ref={sectionRef} className={styles.trustSection}>
      <div className={styles.trustBand}>
        {metrics.map((metric) => (
          <div key={metric.label} className={styles.statCard}>
            <AnimatedNumber trigger={isVisible} {...metric} />
            <span className={styles.label}>{metric.label}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
