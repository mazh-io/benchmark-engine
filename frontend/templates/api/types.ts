export type APISection = 'docs' | 'playground' | 'keys' | 'widgets';

export interface APICard {
  id: APISection;
  icon: string;
  label: string;
}

export type HTTPMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';

export interface APIParameter {
  name: string;
  type: string;
  default?: string;
  description: string;
  required?: boolean;
}

export interface APIEndpoint {
  method: HTTPMethod;
  path: string;
  description: string;
  parameters?: APIParameter[];
}

export interface CodeExample {
  language: 'curl' | 'python' | 'javascript';
  code: string;
}

export interface APIEndpointDocumentation {
  endpoint: APIEndpoint;
  codeExamples: CodeExample[];
  responseExample: string;
  rateLimits: RateLimit[];
  headers: APIHeader[];
}

export interface RateLimit {
  tier: string;
  limit: string;
}

export interface APIHeader {
  name: string;
  description: string;
}
