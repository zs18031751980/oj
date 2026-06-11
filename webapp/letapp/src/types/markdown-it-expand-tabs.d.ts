declare module 'markdown-it-expand-tabs' {
  import MarkdownIt from 'markdown-it';
  
  const expandTabs: (md: MarkdownIt) => void;
  export default expandTabs;
}