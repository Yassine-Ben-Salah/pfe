export interface PriceItem {
  designation?: string;
  prix_unitaire?: string;
  montant?: string;
}

export interface RapportResult {
  filename?: string;
  score?: number;
  marque?: string;
  type?: string;
  immatriculation?: string;
  assure?: string;
  date_accident?: string;
  numero_dossier?: string;
  damage_text?: string;
  price_items?: PriceItem[];
  total_ht?: string;
  tva?: string;
  total_net?: string;
  total_ttc?: string;
}

export interface SearchRequest {
  marque?: string | null;
  type?: string | null;
  assurance?: string | null;
  damage_query?: string | null;
  top_k: number;
  semantic_weight: number;
  bm25_weight: number;
  rerank: boolean;
  score_threshold?: number | null;
}

export interface SearchResponse {
  total: number;
  results: RapportResult[];
}

export interface PartItem {
  id: number;
  motorisation_id?: number | null;
  brand?: string | null;
  car_name?: string | null;
  piece_name?: string | null;
  piece_brand?: string | null;
  piece_price?: string | number | null;
}

export interface PartsListResponse {
  items: PartItem[];
  limit: number;
  offset: number;
  count: number;
}

export interface PageResult {
  page_number: number;
  markdown: string;
}

export interface ProcessConstatResponse {
  file_id: string;
  full_text: string;
  page_count?: number;
  blurred_pdf_url?: string;
}