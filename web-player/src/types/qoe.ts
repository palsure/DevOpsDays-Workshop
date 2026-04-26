import type { QoEMetricPayload, Platform, PlaybackState, PlaybackQuality } from '../../../shared/schema/qoe-metrics.types';

export type { QoEMetricPayload, Platform, PlaybackState, PlaybackQuality };

export interface BufferingEvent {
  startTime: number;
  endTime?: number;
  duration: number;
}

export interface PlaybackError {
  code: string;
  message: string;
  timestamp: number;
}
