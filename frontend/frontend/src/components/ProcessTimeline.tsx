import styles from './ProcessTimeline.module.css';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCircleCheck, faCloudArrowUp, faMicrochip, faRightToBracket } from '@fortawesome/free-solid-svg-icons';
import { useTranslation } from '../i18n';

export function ProcessTimeline() {
  const { t } = useTranslation();
  const steps = [
    {
      number: '01',
      title: t('process.step1.title'),
      description: t('process.step1.desc'),
      icon: faRightToBracket,
    },
    {
      number: '02',
      title: t('process.step2.title'),
      description: t('process.step2.desc'),
      icon: faCloudArrowUp,
    },
    {
      number: '03',
      title: t('process.step3.title'),
      description: t('process.step3.desc'),
      icon: faMicrochip,
    },
    {
      number: '04',
      title: t('process.step4.title'),
      description: t('process.step4.desc'),
      icon: faCircleCheck,
    },
  ];

  return (
    <section className={styles.timeline}>
      <div className={styles.container}>
        <div className={styles.header}>
          <h2>{t('process.title')}</h2>
          <p>{t('process.subtitle')}</p>
        </div>

        <div className={styles.timelineContainer}>
          {steps.map((step, index) => (
            <div key={step.number} className={styles.stepWrapper}>
              <div className={styles.step}>
                <div className={styles.stepNumber}>{step.number}</div>
                <FontAwesomeIcon className={styles.stepIcon} icon={step.icon} aria-hidden="true" />
                <h3>{step.title}</h3>
                <p>{step.description}</p>
              </div>
              
              {index < steps.length - 1 && (
                <div className={styles.line}></div>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
