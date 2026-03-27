import { Injectable } from '@nestjs/common';

@Injectable()
export class NotificationsService {
  async enqueueTemplate(
    tenantId: string,
    templateKey: string,
    recipient: string,
    channel: 'EMAIL' | 'WHATSAPP' | 'PUSH',
    payload: Record<string, unknown>,
  ) {
    return {
      tenantId,
      templateKey,
      recipient,
      channel,
      payload,
      status: 'QUEUED',
      retryPolicy: { maxAttempts: 5, backoff: 'exponential' },
    };
  }
}
