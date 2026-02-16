/* ============================================================================
   API Documentation Data
   
   Centralized API documentation content
   This can be moved to a database table or CMS in the future
============================================================================ */

import type { 
  APIEndpointDocumentation, 
  CodeExample, 
  RateLimit, 
  APIHeader 
} from '@/templates/api/types';

/**
 * Latency Endpoint Documentation
 */
export const LATENCY_ENDPOINT_DOC: APIEndpointDocumentation = {
  endpoint: {
    method: 'GET',
    path: '/v1/latency',
    description: 'Get real-time latency metrics for LLM providers and models',
    parameters: [
      {
        name: 'provider',
        type: 'string',
        description: 'Filter by provider (e.g., groq, openai)',
        required: false,
      },
      {
        name: 'model',
        type: 'string',
        description: 'Filter by model slug',
        required: false,
      },
      {
        name: 'metric',
        type: 'string',
        default: 'all',
        description: 'ttft, tps, or jitter',
        required: false,
      },
      {
        name: 'range',
        type: 'string',
        default: '24h',
        description: '1h, 24h, 7d, 30d, 90d',
        required: false,
      },
      {
        name: 'format',
        type: 'string',
        default: 'json',
        description: 'json or csv',
        required: false,
      },
    ],
  },
  
  codeExamples: [
    {
      language: 'curl',
      code: `curl -X GET "https://mazh.io/api/v1/latency?provider=groq&range=24h" \\
  -H "Authorization: Bearer mzh_your_api_key"`,
    },
    {
      language: 'python',
      code: `import requests

response = requests.get(
    "https://mazh.io/api/v1/latency",
    params={"provider": "groq", "range": "24h"},
    headers={"Authorization": "Bearer mzh_your_api_key"}
)

data = response.json()
print(data)`,
    },
    {
      language: 'javascript',
      code: `const response = await fetch(
  "https://mazh.io/api/v1/latency?provider=groq&range=24h",
  {
    headers: {
      Authorization: "Bearer mzh_your_api_key"
    }
  }
);

const data = await response.json();
console.log(data);`,
    },
  ],
  
  responseExample: `{
  "data": [
    {
      "timestamp": "2025-01-28T14:30:00Z",
      "provider": "groq",
      "model": "llama-3.3-70b",
      "ttft_ms": 189,
      "tps": 454
    }
  ],
  "meta": { "count": 288, "range": "24h" }
}`,
  
  rateLimits: [
    {
      tier: 'Pro',
      limit: '1,000 requests / hour',
    },
  ],
  
  headers: [
    {
      name: 'X-RateLimit-Limit',
      description: 'Your hourly limit',
    },
    {
      name: 'X-RateLimit-Remaining',
      description: 'Requests left this hour',
    },
    {
      name: 'X-RateLimit-Reset',
      description: 'Unix timestamp when limit resets',
    },
  ],
};
