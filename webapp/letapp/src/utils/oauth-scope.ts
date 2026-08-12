export const ensureRoleScope = (scope: string): string => {
  const scopes = scope.trim().split(/\s+/).filter(Boolean);
  if (!scopes.includes('role')) {
    scopes.push('role');
  }
  return scopes.join(' ');
};
