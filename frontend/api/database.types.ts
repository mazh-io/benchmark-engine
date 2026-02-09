/**
 * Supabase Database Types (Read-Only)
 *
 * Row types for each table used by the frontend dashboard.
 * This is a read-only frontend — Insert/Update types are omitted.
 *
 * To auto-generate the full set:
 *   npx supabase gen types typescript --project-id YOUR_PROJECT_ID
 */

export interface Database {
  public: {
    Tables: {
      providers: {
        Row: {
          id: string;
          name: string;
          base_url: string | null;
          logo_url: string | null;
          created_at: string;
        };
      };
      models: {
        Row: {
          id: string;
          name: string;
          provider_id: string;
          context_window: number | null;
          active: boolean;
          last_seen_at: string;
          created_at: string;
        };
      };
      benchmark_results: {
        Row: {
          id: string;
          run_id: string;
          provider_id: string | null;
          model_id: string | null;
          provider: string | null;
          model: string | null;
          input_tokens: number;
          output_tokens: number;
          total_latency_ms: number;
          ttft_ms: number | null;
          tps: number | null;
          status_code: number | null;
          success: boolean;
          error_message: string | null;
          response_text: string | null;
          cost_usd: number;
          tokens_per_dollar: number | null;
          created_at: string;
        };
      };
      runs: {
        Row: {
          id: string;
          run_name: string;
          triggered_by: string;
          started_at: string;
          finished_at: string | null;
        };
      };
      prices: {
        Row: {
          id: string;
          provider_id: string;
          model_id: string;
          input_price_per_m: number;
          output_price_per_m: number;
          timestamp: string;
        };
      };
    };
  };
}
