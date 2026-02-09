import type { RateLimit, APIHeader } from '../types';

interface Props {
  rateLimits: RateLimit[];
  headers: APIHeader[];
}

export function APIRateLimits({ rateLimits, headers }: Props) {
  return (
    <>
      {rateLimits.length > 0 && (
        <div>
          <h3 className="api-subsection-title">Rate Limits</h3>
          <div className="api-table">
            <div className="api-table-header">
              <div>TIER</div>
              <div>LIMIT</div>
            </div>

            {rateLimits.map((limit) => (
              <div key={limit.tier} className="api-table-row">
                <div className="api-limit-tier">{limit.tier}</div>
                <div className="api-limit-value">{limit.limit}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {headers.length > 0 && (
        <div className="api-headers-wrap">
          <div className="api-table no-margin">
            <div className="api-table-header">
              <div>HEADER</div>
              <div>DESCRIPTION</div>
            </div>

            {headers.map((header) => (
              <div key={header.name} className="api-table-row">
                <div className="api-param-name">{header.name}</div>
                <div className="api-limit-value">{header.description}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </>
  );
}
