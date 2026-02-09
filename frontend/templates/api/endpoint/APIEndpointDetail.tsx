import type { APIEndpointDocumentation } from '../types';
import { APIEndpointHeader } from './APIEndpointHeader';
import { APICodeExamples } from './APICodeExamples';
import { APIResponseExample } from './APIResponseExample';
import { APIRateLimits } from './APIRateLimits';

interface Props {
  documentation: APIEndpointDocumentation;
}

/** Orchestrates all endpoint documentation sub-components */
export function APIEndpointDetail({ documentation }: Props) {
  const { endpoint, codeExamples, responseExample, rateLimits, headers } = documentation;

  return (
    <div>
      <APIEndpointHeader endpoint={endpoint} />
      <APICodeExamples codeExamples={codeExamples} />
      <APIResponseExample responseExample={responseExample} />
      <APIRateLimits rateLimits={rateLimits} headers={headers} />
    </div>
  );
}

