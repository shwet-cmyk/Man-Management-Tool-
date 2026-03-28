import { WorkflowService } from '../apps/api/src/modules/workflow/workflow.service';

describe('WorkflowService', () => {
  it('returns simulation trace in sandbox mode', async () => {
    const service = new WorkflowService();
    const simulation = await service.simulate('tenant-a', 'expense-approval', { amount: 1000 });
    expect(simulation.sandbox).toBe(true);
    expect(simulation.trace.length).toBeGreaterThan(0);
  });
});
