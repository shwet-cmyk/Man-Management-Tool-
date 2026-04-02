import { BillingService } from '../apps/api/src/modules/billing/billing.service';

describe('BillingService', () => {
  it('calculates usage amount deterministically', async () => {
    const service = new BillingService();
    const event = await service.recordUsage({
      tenantId: 't1',
      metric: 'API_CALL',
      quantity: 1000,
      unitPrice: 0.001,
    });

    expect(event.amount).toBe(1);
  });
});
