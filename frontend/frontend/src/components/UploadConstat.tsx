import { useRef, useState } from "react";
import { processConstat } from "../api/client";
import styles from "./UploadConstat.module.css";
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCar, faFileImage, faFilePdf, faMagnifyingGlass } from '@fortawesome/free-solid-svg-icons';
import { useTranslation } from '../i18n';


const BASE_URL = () => localStorage.getItem('api_url') || 'http://localhost:8000';

interface Detection {
  class: string;
  confidence: number;
}

interface DetectionResult {
  detections: Detection[];
  imageUrl: string;
  imageW: number;
  imageH: number;
}

export default function UploadConstat({ onResult }: any) {
  const { t } = useTranslation();
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  // Detection state
  const [dmgFile, setDmgFile] = useState<File | null>(null);
  const [dmgDragActive, setDmgDragActive] = useState(false);
  const [dmgLoading, setDmgLoading] = useState(false);
  const [dmgResult, setDmgResult] = useState<DetectionResult | null>(null);

  const inputRef = useRef<HTMLInputElement>(null);
  const dmgInputRef = useRef<HTMLInputElement>(null);
  const [blurredPdf, setBlurredPdf] = useState<string | null>(null);
  // ── Constat PDF ──────────────────────────────────────────────
  const handleFile = (selected: File | null) => {
    if (!selected) return;
    if (selected.type !== "application/pdf") { alert("Only PDF files are allowed."); return; }
    setFile(selected);
  };

  const handleUpload = async () => {
  if (!file) return;

  if (typeof window !== "undefined" && localStorage.getItem("isAuthenticated") !== "true") {
    alert("Please log in first to upload a constat file.");
    return;
  }

  setLoading(true);

  try {
    const parsedData = await processConstat(file);

    setBlurredPdf(parsedData.blurred_pdf_url ?? null);

    onResult(parsedData);

  } catch (err) {
    console.error(err);
    alert("Upload failed.");
  }

  setLoading(false);
};

  // ── Damage Detection ─────────────────────────────────────────
  const handleDmgFile = (selected: File | null) => {
    if (!selected) return;
    if (!selected.type.startsWith("image/")) { alert("Only image files are allowed."); return; }
    setDmgFile(selected);
    setDmgResult(null);
  };

  const handleDmgUpload = async () => {
    if (!dmgFile) return;

    if (typeof window !== "undefined" && localStorage.getItem("isAuthenticated") !== "true") {
      alert("Please log in first to upload an image.");
      return;
    }

    setDmgLoading(true);
    try {
      const formData = new FormData();
      formData.append("file", dmgFile);

      const authToken = typeof window !== "undefined" ? localStorage.getItem("authToken") : null;
      const res = await fetch(`${BASE_URL()}/detect-damage`, {
        method: "POST",
        body: formData,
        headers: authToken ? { Authorization: `Bearer ${authToken}` } : {},
        credentials: "include",
      });

      if (!res.ok) throw new Error("Detection failed");
      const data = await res.json();

      const imageUrl = URL.createObjectURL(dmgFile);
      const img = new Image();
      img.src = imageUrl;
      await new Promise(r => img.onload = r);

      setDmgResult({ detections: data.detections, imageUrl, imageW: img.naturalWidth, imageH: img.naturalHeight });
    } catch (err) {
      console.error(err);
      alert("Detection failed.");
    }
    setDmgLoading(false);
  };

  // confidence → color
  const confColor = (c: number) =>
    c >= 0.75 ? "#22c55e" : c >= 0.5 ? "#f59e0b" : "#ef4444";

  return (
    <div className={styles.wrapper}>
      <div className={styles.grid}>

      {/* ── Constat PDF ── */}
      <div className={styles.card}>
        <div>
          <div className={styles.cardLabel}><FontAwesomeIcon icon={faFilePdf} aria-hidden="true" /> {t('upload.constat.title')}</div>
          <div className={styles.title}>{t('upload.constat.title')}</div>
          <div className={styles.subtitle}>{t('upload.constat.subtitle')}</div>
        </div>

        <div
          className={`${styles.dropzone} ${dragActive ? styles.dragActive : ""}`}
          onClick={() => inputRef.current?.click()}
          onDragOver={e => { e.preventDefault(); setDragActive(true); }}
          onDragLeave={() => setDragActive(false)}
          onDrop={e => { e.preventDefault(); setDragActive(false); handleFile(e.dataTransfer.files?.[0]); }}
        >
          <FontAwesomeIcon className={styles.icon} icon={faFilePdf} aria-hidden="true" />
          <div className={styles.dropTitle}>{t('upload.drop')}</div>
          <div className={styles.dropText}>{t('upload.constat.subtitle')}</div>
          <input ref={inputRef} type="file" accept="application/pdf" className={styles.hiddenInput}
            onChange={e => handleFile(e.target.files?.[0] || null)} />
        </div>

        {file && (
          <div className={styles.fileCard}>
            <FontAwesomeIcon className={styles.fileIcon} icon={faFilePdf} aria-hidden="true" />
            <div className={styles.fileInfo}>
              <div className={styles.fileName}>{file.name}</div>
              <div className={styles.fileMeta}>{(file.size / 1024 / 1024).toFixed(2)} MB</div>
            </div>
          </div>
        )}

        <div className={styles.actions}>
          <button className={styles.uploadBtn} onClick={handleUpload} disabled={!file || loading}>
            {loading ? "Processing..." : t('upload.uploadAnalyze')}
          </button>
          {file && <button className={styles.clearBtn} onClick={() => setFile(null)}>Clear</button>}
        </div>

        {loading && <div className={styles.loading}>BLURRING → PARSING → ANALYZING...</div>}
        {blurredPdf && (
          <div className={styles.preview}>
            <h3>Blurred Constat Preview</h3>

            <iframe
              src={blurredPdf}
              width="100%"
              height="600"
              style={{
                border: "1px solid #ddd",
                borderRadius: 12
              }}
            />
          </div>
)}
      </div>

      {/* ── Damage Detection ── */}
      <div className={styles.card}>
        <div>
          <div className={styles.cardLabel}><FontAwesomeIcon icon={faMagnifyingGlass} aria-hidden="true" /> {t('upload.detect.title')}</div>
          <div className={styles.title}>{t('upload.detect.title')}</div>
          <div className={styles.subtitle}>{t('upload.detect.subtitle')}</div>
        </div>

        <div
          className={`${styles.dropzone} ${dmgDragActive ? styles.dragActive : ""}`}
          onClick={() => dmgInputRef.current?.click()}
          onDragOver={e => { e.preventDefault(); setDmgDragActive(true); }}
          onDragLeave={() => setDmgDragActive(false)}
          onDrop={e => { e.preventDefault(); setDmgDragActive(false); handleDmgFile(e.dataTransfer.files?.[0]); }}
        >
          <FontAwesomeIcon className={styles.icon} icon={faCar} aria-hidden="true" />
          <div className={styles.dropTitle}>{t('upload.drop')}</div>
          <div className={styles.dropText}>JPG, PNG, WEBP supported</div>
          <input ref={dmgInputRef} type="file" accept="image/*" className={styles.hiddenInput}
            onChange={e => handleDmgFile(e.target.files?.[0] || null)} />
        </div>

        {dmgFile && (
          <div className={styles.fileCard}>
            <FontAwesomeIcon className={styles.fileIcon} icon={faFileImage} aria-hidden="true" />
            <div className={styles.fileInfo}>
              <div className={styles.fileName}>{dmgFile.name}</div>
              <div className={styles.fileMeta}>{(dmgFile.size / 1024 / 1024).toFixed(2)} MB</div>
            </div>
          </div>
        )}

        <div className={styles.actions}>
          <button className={styles.uploadBtn} onClick={handleDmgUpload} disabled={!dmgFile || dmgLoading}>
            {dmgLoading ? "Detecting..." : t('upload.detectButton')}
          </button>
          {dmgFile && (
            <button className={styles.clearBtn} onClick={() => { setDmgFile(null); setDmgResult(null); }}>
              Clear
            </button>
          )}
        </div>

        {dmgLoading && <div className={styles.loading}>RUNNING YOLO MODEL...</div>}

        {dmgResult && (
          <div className={styles.dmgResults}>
            <img src={dmgResult.imageUrl} alt="Damage" className={styles.dmgImage} />

            {dmgResult.detections.length === 0 ? (
              <div className={styles.dmgEmpty}>No damage detected.</div>
            ) : (
              <>
                <div className={styles.dmgCount}>
                  {dmgResult.detections.length} detection{dmgResult.detections.length !== 1 ? "s" : ""} found
                </div>
                <div className={styles.dmgPills}>
                  {dmgResult.detections.map((d, i) => (
                    <div key={i} className={styles.dmgPill}
                      style={{ border: `1px solid ${confColor(d.confidence)}40` }}>
                      <span className={styles.dmgDot} style={{ background: confColor(d.confidence) }} />
                      <span className={styles.dmgClass}>{d.class}</span>
                      <span className={styles.dmgConf} style={{ color: confColor(d.confidence) }}>
                        {(d.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        )}
      </div>

      </div>
    </div>
  );
}
