import type { APIEndpoint } from '../types';

interface Props {
  endpoint: APIEndpoint;
}

export function APIEndpointHeader({ endpoint }: Props) {
  return (
    <div>
      <h3 className="api-subsection-title">Endpoint</h3>

      <div className="api-endpoint-box">
        <span className="api-endpoint-method">{endpoint.method}</span>
        <span className="api-endpoint-path">{endpoint.path}</span>
      </div>

      {endpoint.parameters && endpoint.parameters.length > 0 && (
        <div className="api-table">
          <div className="api-table-header">
            <div>PARAMETER</div>
            <div>TYPE</div>
            <div>DEFAULT</div>
            <div>DESCRIPTION</div>
          </div>

          {endpoint.parameters.map((param) => (
            <div key={param.name} className="api-table-row">
              <div className="api-param-name">{param.name}</div>
              <div className="api-param-type">{param.type}</div>
              <div className="api-table-default">{param.default || '—'}</div>
              <div
                className="api-param-desc"
                dangerouslySetInnerHTML={{
                  __html: param.description.replace(
                    /`([^`]+)`/g,
                    '<code>$1</code>',
                  ),
                }}
              />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
