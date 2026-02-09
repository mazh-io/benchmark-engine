import { APIEndpointDetail } from './endpoint/APIEndpointDetail';
import { LATENCY_ENDPOINT_DOC } from '@/data/apiDocumentation';

export function APIRestSection() {
  return (
    <div className="api-section">
      <div>
        <h2 className="api-section-title">REST API</h2>
        <p className="api-section-desc">
          Fetch real-time latency data for any provider or model.
        </p>
      </div>

      <div className="api-code-block">
        <div className="api-code-label">BASE URL</div>
        <div className="api-code-content">
          <code>https://mazh.io/api/v1</code>
        </div>
      </div>

      <div className="api-code-block">
        <div className="api-code-label">AUTHENTICATION</div>
        <div className="api-code-content">
          <code>Authorization: Bearer mzh_your_api_key</code>
        </div>
      </div>

      <div className="api-info-text">
        Get your API key in{' '}
        <span className="api-info-highlight">Settings → API</span> after subscribing to Pro.
      </div>

      <APIEndpointDetail documentation={LATENCY_ENDPOINT_DOC} />
    </div>
  );
}
