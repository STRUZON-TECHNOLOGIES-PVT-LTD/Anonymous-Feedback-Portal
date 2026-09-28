export interface Question {
  id: number;
  order: number;
  text: string;
  type: string;
  options: string[];
}

export interface AnswerIn {
  question_id: number;
  selected_option: string;
}

export interface DeviceInfo {
  user_agent?: string;
  platform?: string;
  screen_resolution?: string;
  timezone?: string;
  language?: string;
  fingerprint_hash?: string;
}

export interface FeedbackSubmitPayload {
  confession_text: string;
  answers: AnswerIn[];
  device: DeviceInfo;
  website: string;
  form_seconds: number;
}

export interface AdminInfo {
  username: string;
}

export interface SubmissionListItem {
  id: string;
  created_at: string;
  confession_preview: string | null;
  ip_address: string | null;
  device_fingerprint: string | null;
}

export interface SubmissionListResponse {
  total: number;
  page: number;
  page_size: number;
  items: SubmissionListItem[];
}

export interface AnswerOut {
  question_id: number;
  question_text: string;
  selected_option: string;
}

export interface SubmissionDetail {
  id: string;
  created_at: string;
  confession_text: string | null;
  ip_address: string | null;
  user_agent: string | null;
  platform: string | null;
  screen_resolution: string | null;
  timezone: string | null;
  language: string | null;
  device_fingerprint: string | null;
  answers: AnswerOut[];
  extracted_names: string[];
}

export interface DailyCount {
  date: string;
  count: number;
}

export interface OptionBreakdown {
  question_id: number;
  text: string;
  option_counts: Record<string, number>;
}

export interface RepeatedFingerprint {
  device_fingerprint: string;
  count: number;
  ip_addresses: string[];
}

export interface RepeatedName {
  name: string;
  mention_count: number;
  submission_ids: string[];
}

export interface Stats {
  total_submissions: number;
  submissions_last_30_days: DailyCount[];
  question_breakdown: OptionBreakdown[];
  top_repeated_fingerprints: RepeatedFingerprint[];
  repeated_names: RepeatedName[];
}
