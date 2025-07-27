import type { PageLoad } from './$types';

export const load: PageLoad = ({ url }) => {
  const problemId = url.searchParams.get('id') || '';
  
  return {
    problemId
  };
}; 