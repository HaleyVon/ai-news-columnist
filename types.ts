export type ProcessStatus = 'idle' | 'drafting' | 'evaluating' | 'revising' | 'success' | 'error';

export interface ParsedColumn {
  title: string;
  summary: string;
  progressiveStance: string[];
  conservativeStance: string[];
  mainContentTitle: string;
  mainContentBody: string;
  conclusionTitle: string;
  conclusionBody: string;
}

export interface EvaluationResult {
  scores: {
    format: number;
    balance: number;
    readability: number;
    completeness: number;
    objectivity: number;
  };
  pass: boolean;
  feedback: string;
  revisedContent: string;
}

export interface Source {
  title: string;
  uri: string;
}
