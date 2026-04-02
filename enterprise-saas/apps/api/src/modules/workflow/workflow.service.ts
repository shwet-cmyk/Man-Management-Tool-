import { Injectable } from '@nestjs/common';

@Injectable()
export class WorkflowService {
  async publishVersion(tenantId: string, workflowKey: string, definition: Record<string, unknown>) {
    return {
      tenantId,
      workflowKey,
      version: Math.floor(Date.now() / 1000),
      definition,
      mode: 'PRODUCTION',
    };
  }

  async simulate(tenantId: string, workflowKey: string, input: Record<string, unknown>) {
    return {
      tenantId,
      workflowKey,
      sandbox: true,
      result: 'PASS',
      trace: [{ node: 'validate', status: 'ok' }, { node: 'approve-manager', status: 'ok' }],
      input,
    };
  }
}
