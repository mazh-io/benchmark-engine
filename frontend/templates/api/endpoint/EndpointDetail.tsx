import type { APIEndpointDocumentation } from '../types';
import { EndpointHeader } from './EndpointHeader';
import { CodeExamples } from './CodeExamples';
import { ResponseExample } from './ResponseExample';
import { RateLimits } from './RateLimits';

interface Props {
  documentation: APIEndpointDocumentation;
}

export function EndpointDetail({ documentation }: Props) {
  const { endpoint, codeExamples, responseExample, rateLimits, headers } = documentation;

  return (
    <div>
      <EndpointHeader endpoint={endpoint} />
      <CodeExamples codeExamples={codeExamples} />
      <ResponseExample responseExample={responseExample} />
      <RateLimits rateLimits={rateLimits} headers={headers} />
    </div>
  );
}
