export async function processUsageEventJob(job: { id: string; data: Record<string, unknown> }) {
  // BullMQ processor placeholder
  return { jobId: job.id, handled: true, at: new Date().toISOString(), data: job.data };
}
