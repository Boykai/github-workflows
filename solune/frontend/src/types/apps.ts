/** Application management types for the Solune platform. */

export type AppStatus = 'creating' | 'active' | 'stopped' | 'error';
export type RepoType = 'same-repo' | 'external-repo' | 'new-repo';

export interface App {
  name: string;
  display_name: string;
  description: string;
  directory_path: string;
  associated_pipeline_id: string | null;
  status: AppStatus;
  repo_type: RepoType;
  external_repo_url: string | null;
  github_repo_url: string | null;
  github_project_url: string | null;
  github_project_id: string | null;
  parent_issue_number: number | null;
  parent_issue_url: string | null;
  port: number | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
  /** Transient warnings from partial-success creation (e.g. Azure secret storage failure). */
  warnings: string[] | null;
}

export interface AppCreate {
  name: string;
  display_name: string;
  description?: string;
  branch?: string;
  pipeline_id?: string;
  project_id?: string;
  repo_type?: RepoType;
  external_repo_url?: string;
  repo_owner?: string;
  repo_visibility?: 'public' | 'private';
  create_project?: boolean;
  ai_enhance?: boolean;
  azure_client_id?: string;
  azure_client_secret?: string;
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

export interface Owner {
  login: string;
  avatar_url: string;
  type: 'User' | 'Organization';
}

export interface CreateProjectRequest {
  title: string;
  owner: string;
  repo_owner?: string;
  repo_name?: string;
}

export interface CreateProjectResponse {
  project_id: string;
  project_number: number;
  project_url: string;
}

export interface AppAssetInventory {
  app_name: string;
  github_repo: string | null;
  github_project_id: string | null;
  parent_issue_number: number | null;
  sub_issues: number[];
  branches: string[];
  has_azure_secrets: boolean;
}

export interface DeleteAppResult {
  app_name: string;
  issues_closed: number;
  branches_deleted: number;
  project_deleted: boolean;
  repo_deleted: boolean;
  db_deleted: boolean;
  errors: string[];
}
