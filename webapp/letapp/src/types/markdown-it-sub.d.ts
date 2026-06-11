declare module 'markdown-it-sub' {
  import MarkdownIt from 'markdown-it';
  
  const sub: (md: MarkdownIt) => void;
  export default sub;
}