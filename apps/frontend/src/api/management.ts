import { apiFetch } from './client';
import { ManagementPrototype } from '../types/management';

export const getManagementPrototype = (): Promise<ManagementPrototype> =>
  apiFetch<ManagementPrototype>('/management/prototype');
