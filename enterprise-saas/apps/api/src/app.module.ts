import { MiddlewareConsumer, Module, NestModule } from '@nestjs/common';
import { TenantMiddleware } from './common/middleware/tenant.middleware';
import { BillingModule } from './modules/billing/billing.module';
import { WorkflowModule } from './modules/workflow/workflow.module';
import { NotificationsModule } from './modules/notifications/notifications.module';

@Module({
  imports: [BillingModule, WorkflowModule, NotificationsModule],
})
export class AppModule implements NestModule {
  configure(consumer: MiddlewareConsumer): void {
    consumer.apply(TenantMiddleware).forRoutes('*');
  }
}
