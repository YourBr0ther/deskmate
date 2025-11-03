/**
 * TypeScript types for SillyTavern V2 persona cards (Web version)
 */

export interface PersonaData {
  name: string;
  description: string;
  personality: string;
  scenario: string;
  first_mes: string;
  mes_example: string;
  creator_notes: string;
  system_prompt: string;
  post_history_instructions: string;
  alternate_greetings: string[];
  tags: string[];
  creator: string;
  character_version: string;
  avatar: string;
  extensions: Record<string, any>;
  character_book?: {
    entries: any[];
    name: string;
    description: string;
    scan_depth?: number;
    token_budget?: number;
    recursive_scanning?: boolean;
  };
}

export interface PersonaCard {
  spec: string;
  spec_version: string;
  data: PersonaData;
}

export interface PersonaMetadata {
  file_path: string;
  file_size: number;
  loaded_at: string;
  character_name: string;
  creator: string;
  tags: string[];
  has_lorebook: boolean;
}

export interface LoadedPersona {
  persona: PersonaCard;
  metadata: PersonaMetadata;
}

export interface PersonaSummary {
  name: string;
  creator: string;
  tags: string[];
  description_length: number;
  has_lorebook: boolean;
  alternate_greetings_count: number;
  file_size: number;
  loaded_at: string;
}