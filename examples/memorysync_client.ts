/**
 * MemorySync Zero-Dependency TypeScript Client
 * Compatible with Node.js 18+, Bun, Deno, and Cloudflare Workers.
 * 
 * Uses standard web `fetch` with strict TypeScript types and scoped multi-tenancy.
 */

export interface MemorySyncConfig {
  apiKey: string;
  baseUrl?: string;
  tenantId?: string;
  projectId?: string;
}

export interface MemoryItem {
  id: string | number;
  memory_id?: string;
  text?: string;
  raw_text?: string;
  summary?: string | null;
  source?: string;
  score?: number;
  metadata?: Record<string, unknown>;
  created_at?: string;
}

export interface AddMemoryParams {
  text: string;
  endUserId: string;
  source?: string;
  metadata?: Record<string, unknown>;
}

export interface SearchMemoriesParams {
  query: string;
  endUserId: string;
  k?: number;
}

export interface RecallContextParams {
  prompt: string;
  endUserId: string;
  k?: number;
}

export interface ListMemoriesParams {
  endUserId: string;
  limit?: number;
}

export interface DeleteMemoriesParams {
  memoryIds: Array<string | number>;
  endUserId: string;
}

export interface RecallResponse {
  context: string;
  memories: MemoryItem[];
}

export class MemorySyncClient {
  private readonly apiKey: string;
  private readonly baseUrl: string;
  private readonly tenantId: string;
  private readonly projectId?: string;

  constructor(config: MemorySyncConfig) {
    if (!config.apiKey) {
      throw new Error("MemorySyncClient: apiKey is required.");
    }
    this.apiKey = config.apiKey;
    this.baseUrl = (config.baseUrl || "https://api.memorysync.io").replace(/\/+$/, "");
    this.tenantId = config.tenantId || "default";
    this.projectId = config.projectId;
  }

  private async request<T>(
    method: "GET" | "POST" | "DELETE",
    path: string,
    body?: Record<string, unknown>,
    endUserId?: string
  ): Promise<T> {
    const url = `${this.baseUrl}${path}`;
    const headers: Record<string, string> = {
      "Authorization": `Bearer ${this.apiKey}`,
      "X-API-Key": this.apiKey,
      "Content-Type": "application/json",
      "Accept": "application/json",
    };

    if (endUserId) {
      headers["X-End-User-ID"] = endUserId;
    }
    if (this.projectId) {
      headers["X-Project-ID"] = this.projectId;
    }

    const options: RequestInit = {
      method,
      headers,
    };

    if (body !== undefined) {
      options.body = JSON.stringify(body);
    }

    const response = await fetch(url, options);

    if (!response.ok) {
      const errorText = await response.text().catch(() => "Unknown error");
      throw new Error(`MemorySync API Error [${response.status} ${response.statusText}]: ${errorText}`);
    }

    return (await response.json()) as T;
  }

  /**
   * Store a new durable fact or preference for a specific end user.
   */
  async add(params: AddMemoryParams): Promise<{ id?: string | number; status?: string }> {
    return this.request<{ id?: string | number; status?: string }>(
      "POST",
      "/memory/add",
      {
        text: params.text,
        source: params.source || "typescript-sdk",
        metadata: params.metadata || {},
      },
      params.endUserId
    );
  }

  /**
   * Search user memories semantically using natural language.
   */
  async search(params: SearchMemoriesParams): Promise<MemoryItem[]> {
    const res = await this.request<{ memories?: MemoryItem[] }>(
      "POST",
      "/memory/query",
      {
        query: params.query,
        k: params.k || 5,
      },
      params.endUserId
    );
    return Array.isArray(res.memories) ? res.memories : [];
  }

  /**
   * Hierarchical recall: returns a pre-assembled, prompt-ready markdown context block.
   */
  async recall(params: RecallContextParams): Promise<RecallResponse> {
    return this.request<RecallResponse>(
      "POST",
      "/v1/memory/recall",
      {
        tenant_id: this.tenantId,
        user_id: params.endUserId,
        prompt: params.prompt,
        k: params.k || 5,
      },
      params.endUserId
    );
  }

  /**
   * List memories for a user, newest first.
   */
  async list(params: ListMemoriesParams): Promise<MemoryItem[]> {
    const limit = params.limit ?? 50;
    const path = `/v1/memory/${encodeURIComponent(this.tenantId)}/${encodeURIComponent(params.endUserId)}/list?limit=${limit}`;
    const res = await this.request<{ memories?: MemoryItem[] }>(
      "GET",
      path,
      undefined,
      params.endUserId
    );
    return Array.isArray(res.memories) ? res.memories : [];
  }

  /**
   * Permanently delete specific memory records.
   */
  async delete(params: DeleteMemoriesParams): Promise<{ deleted: unknown }> {
    const memory_ids = params.memoryIds.map((id) =>
      typeof id === "string" && id.startsWith("m_") ? id.slice(2) : id
    );
    return this.request<{ deleted: unknown }>(
      "DELETE",
      "/memory/forget",
      { memory_ids },
      params.endUserId
    );
  }
}
