import axios from 'axios';

const API_BASE = 'http://localhost:8000';

export interface LoginResponse {
  success: boolean;
  username: string;
  name: string;
  role: string;
  collections: string[];
}

export interface ChatResponse {
  success: boolean;
  response: string;
  message: string;
  route: string;
  guardrail_type: string;
  warning: string;
  stage: string;
  chunks: {
    source_document: string;
    page_number: number;
    section_title: string;
    score: number;
  }[];
}

export const loginUser = async (
  username: string,
  password: string
): Promise<LoginResponse> => {
  const res = await axios.post(`${API_BASE}/login`, { username, password });
  return res.data;
};

export const sendMessage = async (
  query: string,
  username: string,
  role: string,
  session_id: string
): Promise<ChatResponse> => {
  const res = await axios.post(`${API_BASE}/chat`, {
    query,
    username,
    role,
    session_id,
  });
  return res.data;
};
