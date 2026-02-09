import { highlightJSON } from '../syntaxHighlighting';

interface Props {
  responseExample: string;
}

export function APIResponseExample({ responseExample }: Props) {
  if (!responseExample) return null;

  return (
    <div>
      <h3 className="api-subsection-title">Example Response</h3>

      <div className="api-code-example">
        <div className="api-code-example-header">
          <span>JSON</span>
        </div>

        <div className="api-code-example-content">
          <pre dangerouslySetInnerHTML={{ __html: highlightJSON(responseExample) }} />
        </div>
      </div>
    </div>
  );
}
