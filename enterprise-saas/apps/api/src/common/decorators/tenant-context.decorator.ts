import { createParamDecorator, ExecutionContext } from '@nestjs/common';

export interface TenantContextValue {
  tenantId: string;
  branchId?: string;
  userId?: string;
  roles: string[];
}

export const TenantContext = createParamDecorator(
  (_: unknown, ctx: ExecutionContext): TenantContextValue => {
    const request = ctx.switchToHttp().getRequest();
    return request.tenantContext as TenantContextValue;
  },
);
