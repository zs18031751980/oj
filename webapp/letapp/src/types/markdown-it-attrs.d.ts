declare module 'markdown-it-attrs' {
  import MarkdownIt from 'markdown-it';
  
  interface AttrsOptions {
    allowedAttributes?: string[];
    allowedClasses?: Record<string, string[]>;
    allowedStyles?: Record<string, string[]>;
  }

  const attrs: (md: MarkdownIt, options?: AttrsOptions) => void;
  export default attrs;
}