declare module 'markdown-it-task-lists' {
  import MarkdownIt from 'markdown-it';
  
  interface TaskListOptions {
    enabled?: boolean;
    label?: boolean;
    labelAfter?: boolean;
  }

  const taskLists: (md: MarkdownIt, options?: TaskListOptions) => void;
  export default taskLists;
}