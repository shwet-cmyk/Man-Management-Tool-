import { Body, Controller, Get, Param, Post } from '@nestjs/common';
import { BillingService, UsageEventInput } from './billing.service';
import { TenantContext, TenantContextValue } from '../../common/decorators/tenant-context.decorator';

@Controller('tenants/:tenantId/billing')
export class BillingController {
  constructor(private readonly billingService: BillingService) {}

  @Post('usage-events')
  async recordUsage(
    @Param('tenantId') tenantId: string,
    @Body() payload: Omit<UsageEventInput, 'tenantId'>,
    @TenantContext() context: TenantContextValue,
  ) {
    if (context.tenantId !== tenantId) throw new Error('Tenant mismatch');
    return this.billingService.recordUsage({ ...payload, tenantId });
  }

  @Get('invoices/:periodStart/:periodEnd')
  async generateInvoice(
    @Param('tenantId') tenantId: string,
    @Param('periodStart') periodStart: string,
    @Param('periodEnd') periodEnd: string,
  ) {
    return this.billingService.generateInvoice(tenantId, periodStart, periodEnd);
  }
}
