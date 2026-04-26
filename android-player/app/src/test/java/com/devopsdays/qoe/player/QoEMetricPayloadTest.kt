package com.devopsdays.qoe.player

import com.devopsdays.qoe.player.models.QoEMetricPayload
import org.junit.Assert.*
import org.junit.Test

class QoEMetricPayloadTest {

    @Test
    fun `payload stores platform correctly`() {
        val payload = QoEMetricPayload(
            platform = "android",
            videoId = "vid-001",
            sessionId = "sess-abc",
            timestamp = "2026-01-01T00:00:00Z",
            deviceInfo = mapOf("model" to "Pixel 8"),
            metrics = mapOf("bitrate" to 4500)
        )
        assertEquals("android", payload.platform)
    }

    @Test
    fun `payload stores videoId correctly`() {
        val payload = QoEMetricPayload(
            platform = "android",
            videoId = "vid-002",
            sessionId = "sess-xyz",
            timestamp = "2026-01-01T00:00:00Z",
            deviceInfo = emptyMap(),
            metrics = emptyMap()
        )
        assertEquals("vid-002", payload.videoId)
    }

    @Test
    fun `payload stores metrics map correctly`() {
        val metrics = mapOf("bufferingRatio" to 0.02, "startupTime" to 1500)
        val payload = QoEMetricPayload(
            platform = "android",
            videoId = "vid-003",
            sessionId = "sess-def",
            timestamp = "2026-01-01T00:00:00Z",
            deviceInfo = emptyMap(),
            metrics = metrics
        )
        assertEquals(0.02, payload.metrics["bufferingRatio"])
        assertEquals(1500, payload.metrics["startupTime"])
    }

    @Test
    fun `device info map is preserved`() {
        val deviceInfo = mapOf("model" to "Pixel 8 Pro", "osVersion" to "14")
        val payload = QoEMetricPayload(
            platform = "android",
            videoId = "vid-004",
            sessionId = "sess-ghi",
            timestamp = "2026-01-01T00:00:00Z",
            deviceInfo = deviceInfo,
            metrics = emptyMap()
        )
        assertEquals("Pixel 8 Pro", payload.deviceInfo["model"])
        assertEquals("14", payload.deviceInfo["osVersion"])
    }

    @Test
    fun `data class equality works`() {
        val p1 = QoEMetricPayload("android", "v1", "s1", "t1", emptyMap(), emptyMap())
        val p2 = QoEMetricPayload("android", "v1", "s1", "t1", emptyMap(), emptyMap())
        assertEquals(p1, p2)
    }
}
