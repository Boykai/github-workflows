import { z } from 'zod';

export function validateResponse<T>(schema: z.ZodType<T>, data: unknown, endpoint: string): T {
  if (!import.meta.env.DEV) {
    return data as T;
  }

  try {
    return schema.parse(data);
  } catch (error) {
    console.error(`[API Schema Validation] ${endpoint}:`, error);
    throw error;
  }
}