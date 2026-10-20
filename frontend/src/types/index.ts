export type VaultItemKind =
  | "password"
  | "seed_phrase"
  | "document"
  | "api_key"
  | "note"
  | "crypto_wallet"
  | "custom";

export interface VaultItem {
  id: string;
  kind: string;
  title_hint: string;
  encrypted_data: string;
  nonce: string;
  encryption_version: number;
  asset_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface Asset {
  id: string;
  kind: string;
  name: string;
  identifier: string | null;
  estimated_value_cents: number | null;
  status: string;
  discovery_source: string;
  notes: string | null;
  has_credentials: boolean;
  created_at: string;
  updated_at: string;
}

export interface LegacyMessage {
  id: string;
  recipient_email: string;
  recipient_name: string;
  subject: string;
  trigger: string;
  trigger_date: string | null;
  status: string;
  delivered_at: string | null;
  created_at: string;
  encrypted_content?: string;
  nonce?: string;
}

export interface Executor {
  id: string;
  executor_email: string;
  executor_name: string;
  relationship: string;
  phone: string | null;
  access_level: string;
  status: string;
  accepted_at: string | null;
  created_at: string;
}

export interface KeyBundleResponse {
  encryption_salt: string;
  encrypted_key_bundle: string | null;
  has_vault_key: boolean;
}

export interface EstateSummary {
  executor_id: string;
  grantor_user_id: string;
  grantor_name: string;
  grantor_email: string;
  access_level: string;
  status: string;
  total_assets: number;
  total_vault_items: number;
  total_legacy_messages: number;
  switch_status: string | null;
}

export interface EstateDetail {
  grantor_name: string;
  grantor_email: string;
  access_level: string;
  checklist: Array<{ step: number; title: string; detail: string; done: boolean }>;
  assets: Array<{ id: string; kind: string; name: string; status: string }>;
  vault_items: Array<{ id: string; kind: string; title_hint: string }>;
  legacy_messages: Array<{
    id: string;
    recipient_name: string;
    subject: string;
    status: string;
  }>;
  trusted_contacts: Array<{ name: string; email: string; relationship: string }>;
}
