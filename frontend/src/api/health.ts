import axios from "axios";

export type HealthResponse = {
  status: string;
};

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await axios.get<HealthResponse>("/health");
  return response.data;
}

export async function fetchDatabaseHealth(): Promise<HealthResponse> {
  const response = await axios.get<HealthResponse>("/health/db");
  return response.data;
}
