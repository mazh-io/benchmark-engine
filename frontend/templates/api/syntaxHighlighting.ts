/**
 * Syntax highlighting for code examples, JSON, and HTML/iframe embeds.
 */

/** Highlight code by language (cURL, Python, JavaScript) */
export function highlightCode(code: string, language: string): string {
  switch (language) {
    case 'curl':
      return code.replace(/"([^"]+)"/g, '<span class="string">"$1"</span>');

    case 'python': {
      let h = code;
      h = h.replace(/\b(import|from|for|in|print)\b/g, '<span class="key">$1</span>');
      h = h.replace(/"([^"]+)"/g, '<span class="string">"$1"</span>');
      h = h.replace(/f"([^"]+)"/g, 'f<span class="string">"$1"</span>');
      return h;
    }

    case 'javascript': {
      let h = code;
      h = h.replace(/\b(const|let|var|await|async|function|return|if|else|for|in|of)\b/g, '<span class="key">$1</span>');
      h = h.replace(/"([^"]+)"/g, '<span class="string">"$1"</span>');
      h = h.replace(/`([^`]+)`/g, '<span class="string">`$1`</span>');
      return h;
    }

    default:
      return code;
  }
}

/** Highlight JSON keys, string values, and numbers */
export function highlightJSON(json: string): string {
  let h = json;
  h = h.replace(/"([^"]+)":/g, '<span class="key">"$1"</span>:');
  h = h.replace(/:\s*"([^"]+)"/g, ': <span class="string">"$1"</span>');
  h = h.replace(/:\s*(\d+)([,}\s])/g, ': <span class="number">$1</span>$2');
  return h;
}

/** Highlight HTML/iframe embed code with green string values */
export function highlightHTML(code: string): string {
  let highlighted = code.replace(/([=])\s*"([^"]+)"/g, '$1<span class="string">"$2"</span>');

  const parts = highlighted.split(/(<span class="string">.*?<\/span>)/g);

  return parts
    .map((part) => {
      if (part.startsWith('<span class="string">')) {
        return part.replace(
          /(<span class="string">")(.*?)("<\/span>)/g,
          (_, open, content, close) => {
            const escaped = content
              .replace(/&/g, '&amp;')
              .replace(/</g, '&lt;')
              .replace(/>/g, '&gt;');
            return open + escaped + close;
          },
        );
      }
      return part
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
    })
    .join('');
}

