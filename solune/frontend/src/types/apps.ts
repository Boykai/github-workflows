/** Application management types for the Solune platform. */

export type AppStatus = 'creating' | 'active' | 'stopped' | 'error';
export type RepoType = 'same-repo' | 'external-repo';

export interface App {
  name: string;
  display_name: string;
  description: string;
  directory_path: string;
  associated_pipeline_id: string | null;
  status: AppStatus;
  repo_type: RepoType;
  external_repo_url: string | null;
  port: number | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface AppCreate {
  name: string;
  display_name: string;
  description?: string;
  branch: string;
  pipeline_id?: string;
  repo_type?: RepoType;
  external_repo_url?: string;
}

export interface AppUpdate {
  display_name?: string;
  description?: string;
  pipeline_id?: string;
}

export interface AppStatusResponse {
  name: string;
  status: AppStatus;
  port: number | null;
  error_message: string | null;
}
