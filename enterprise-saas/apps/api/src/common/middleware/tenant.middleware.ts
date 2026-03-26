import { Injectable, NestMiddleware, UnauthorizedException } from '@nestjs/common';
import { Request, Response, NextFunction } from 'express';

@Injectable()
export class TenantMiddleware implements NestMiddleware {
  use(req: Request, _res: Response, next: NextFunction): void {
    const tenantId = (req.headers['x-tenant-id'] as string) || undefined;
    const branchId = (req.headers['x-branch-id'] as string) || undefined;

    if (!tenantId) {
      throw new UnauthorizedException('Missing x-tenant-id header');
    }

    (req as Request & { tenantContext?: unknown }).tenantContext = {
      tenantId,
      branchId,
      userId: (req as any).user?.sub,
      roles: (req as any).user?.roles ?? [],
    };

    next();
  }
}
