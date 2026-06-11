declare module 'markdown-it-sup' {
  import MarkdownIt from 'markdown-it';
  
  const sup: (md: MarkdownIt) => void;
  export default sup;
}