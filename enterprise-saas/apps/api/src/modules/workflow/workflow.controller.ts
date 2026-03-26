import { Body, Controller, Param, Post } from '@nestjs/common';
import { WorkflowService } from './workflow.service';

@Controller('tenants/:tenantId/workflows')
export class WorkflowController {
  constructor(private readonly workflowService: WorkflowService) {}

  @Post(':workflowKey/versions')
  publish(
    @Param('tenantId') tenantId: string,
    @Param('workflowKey') workflowKey: string,
    @Body() definition: Record<string, unknown>,
  ) {
    return this.workflowService.publishVersion(tenantId, workflowKey, definition);
  }

  @Post(':workflowKey/simulate')
  simulate(
    @Param('tenantId') tenantId: string,
    @Param('workflowKey') workflowKey: string,
    @Body() input: Record<string, unknown>,
  ) {
    return this.workflowService.simulate(tenantId, workflowKey, input);
  }
}
