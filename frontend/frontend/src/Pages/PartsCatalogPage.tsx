import { PartsCatalogSearch } from '../components/PartsCatalogSearch';
import styles from './PartsCatalogPage.module.css';

export function PartsCatalogPage() {
  return (
    <div className={styles.page}>
      <section className={styles.hero}>
        <div>
          <p className={styles.eyebrow}>Catalogues pièces</p>
          <h1 className={styles.title}>Rechercher des pièces par véhicule, marque ou mot-clé</h1>
          <p className={styles.subtitle}>
            Retrouvez rapidement les références adaptées à votre voiture et au type de pièce recherché.
          </p>
        </div>
      </section>

      <div className={styles.content}>
        <PartsCatalogSearch />
      </div>
    </div>
  );
}
