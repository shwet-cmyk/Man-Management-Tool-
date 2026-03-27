import { Injectable } from '@nestjs/common';

type UsageMetric = 'USER' | 'WORKFLOW_EXECUTION' | 'API_CALL' | 'AI_TOKENS';

export interface UsageEventInput {
  tenantId: string;
  metric: UsageMetric;
  quantity: number;
  unitPrice: number;
  sourceRef?: string;
}

@Injectable()
export class BillingService {
  async recordUsage(input: UsageEventInput) {
    const amount = Number((input.quantity * input.unitPrice).toFixed(6));
    return { ...input, amount, recordedAt: new Date().toISOString() };
  }

  async generateInvoice(tenantId: string, periodStart: string, periodEnd: string) {
    // Replace with repository aggregation query + transactional ledger posting.
    return {
      tenantId,
      periodStart,
      periodEnd,
      invoiceNo: `INV-${tenantId.slice(0, 8)}-${periodEnd.replaceAll('-', '')}`,
      lines: [
        { metric: 'USER', quantity: 100, unitPrice: 5, total: 500 },
        { metric: 'API_CALL', quantity: 25000, unitPrice: 0.002, total: 50 },
      ],
      total: 550,
      currency: 'USD',
      ledgerStatus: 'POSTED',
    };
  }
}
