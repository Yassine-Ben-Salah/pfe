import axios from 'axios';
import type { PartsListResponse, ProcessConstatResponse, SearchRequest, SearchResponse } from '../types/api';

let baseURL = localStorage.getItem('api_url') || 'http://localhost:8000';


export interface UserData {
  id: number;
  email: string;
  username: string;
  telephone: string;
  role: string;
  is_active: boolean;
}

export interface ConstatData {
  file_id?: string;
  full_text?: string;
  page_count?: number;
  blurred_pdf_url?: string;

  date_accident?: string;
  heure?: string;
  lieu?: string;
  blesses?: string;

  vehicule_a_marque?: string;
  vehicule_a_type?: string;
  vehicule_a_immatriculation?: string;
  assurance_a?: string;
  degats_vehicule_a?: string;

  vehicule_b_marque?: string;
  vehicule_b_type?: string;
  vehicule_b_immatriculation?: string;
  assurance_b?: string;
  degats_vehicule_b?: string;

  observations?: string;
}


export async function listUsers(): Promise<UserData[]> {
  const res = await axios.get(`${baseURL}/auth/users`, {
    headers: getAuthHeaders(),
  });
  return res.data;
}
export async function registerUser(data: {
  email: string;
  password: string;
  username: string;
  telephone: string;
  role: string;
}): Promise<any> {
  const res = await axios.post(`${baseURL}/auth/register`, data, {
    headers: getAuthHeaders(),
  });
  return res.data;
}


export async function updateUser(userId: number, data: Partial<{
  email: string;
  username: string;
  telephone: string;
  role: string;
  is_active: boolean;
  password: string;
}>): Promise<UserData> {
  const res = await axios.patch(`${baseURL}/auth/users/${userId}`, data, {
    headers: getAuthHeaders(),
  });
  return res.data;
}

export async function deleteUser(userId: number): Promise<void> {
  await axios.delete(`${baseURL}/auth/users/${userId}`, {
    headers: getAuthHeaders(),
  });
}



const getAuthHeaders = () => {
  const token = typeof window !== 'undefined' ? localStorage.getItem('authToken') : null;
  return token ? { Authorization: `Bearer ${token}` } : {};
};

export const getBaseURL = () => baseURL;
export const setBaseURL = (url: string) => {
  baseURL = url.replace(/\/$/, '');
  localStorage.setItem('api_url', baseURL);
};


export async function checkHealth(): Promise<boolean> {
  try {
    const res = await axios.get(`${baseURL}/health`, { timeout: 3000 });
    return res.status === 200;
  } catch {
    return false;
  }
}

export async function searchRapports(req: SearchRequest): Promise<SearchResponse> {
  const res = await axios.post<SearchResponse>(`${baseURL}/search`, req, {
    timeout: 30000,
    headers: getAuthHeaders(),
  });
  return res.data;
}

export async function listParts(params?: {
  q?: string;
  brand?: string;
  car_name?: string;
  limit?: number;
  offset?: number;
}): Promise<PartsListResponse> {
  const res = await axios.get<PartsListResponse>(`${baseURL}/parts`, {
    timeout: 30000,
    headers: getAuthHeaders(),
    params,
  });
  return res.data;
}

export async function processConstat(file: File): Promise<ProcessConstatResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await axios.post<ProcessConstatResponse>(
    `${baseURL}/process-constat`,
    formData,
    {
      timeout: 300000, // important (PDF + LlamaCloud can be slow)
      headers: getAuthHeaders(),
    } 
  );
  console.log(
    "RAW RESPONSE:",
    JSON.stringify(res.data, null, 2)
  );
  return res.data;
}
export async function extractClean(data: any) {
  const res = await axios.post(
    `${baseURL}/extract-clean`,
    data,
    {
      timeout: 180000,
    }
  );

  return res.data;
}
export async function extractFieldsWithGroq(fullText: string): Promise<any> {
  const res = await axios.post(
    `${baseURL}/extract-fields`,
    { text: fullText },
    { timeout: 30000 }
  );
  console.log("Extracted fields:", JSON.stringify(res.data, null, 2));
  return res.data;
}
export async function analyzeConstat(fullText: string): Promise<any> {
  const res = await axios.post(
    `${baseURL}/analyze-constat`,
    { full_text: fullText },
    { timeout: 90000 }
  );
  return res.data;
}

export async function saveConstatReport(constatId: number, report: any): Promise<any> {
  const res = await axios.put(`${baseURL}/constats/${constatId}/report`, report, {
    headers: getAuthHeaders(),
  });
  return res.data;
}

export async function loginUser(email: string, password: string): Promise<{ access_token: string; token_type: string }> {
  const body = new URLSearchParams();
  body.append('username', email);
  body.append('password', password);

  const res = await axios.post(`${baseURL}/auth/login`, body, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    timeout: 10000,
  });
  return res.data;
}

export async function getCurrentUser(): Promise<any> {
  const res = await axios.get(`${baseURL}/auth/me`, {
    headers: getAuthHeaders(),
  });
  return res.data;
}


export async function saveConstat(data: ConstatData): Promise<any> {
  const res = await axios.post(`${baseURL}/constats/`, data, {
    headers: getAuthHeaders(),
  });
  return res.data;
}

export async function listConstats(): Promise<any[]> {
  const res = await axios.get(`${baseURL}/constats/`, {
    headers: getAuthHeaders(),
  });
  return res.data;
}

