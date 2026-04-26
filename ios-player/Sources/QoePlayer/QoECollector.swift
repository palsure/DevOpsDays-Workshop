import Foundation
import AVFoundation

public struct QoEMetricPayload: Codable {
    let platform: String
    let videoId: String
    let sessionId: String
    let timestamp: String
    let deviceInfo: DeviceInfo
    let metrics: QoEMetrics
}

public struct DeviceInfo: Codable {
    let deviceType: String
    let os: String
    let screenResolution: String
}

public struct QoEMetrics: Codable {
    let playbackState: String
    let currentTime: Double
    let duration: Double
    let bufferingEvents: [BufferingEvent]
    let totalBufferingTime: Double
    let startupTime: Int64?
    let currentBitrate: Int64?
    let currentResolution: String?
    let bitrateSwitches: Int
    let errors: [PlaybackError]
    let errorCount: Int
    let playbackQuality: String
}

public struct BufferingEvent: Codable {
    let startTime: Double
    let endTime: Double?
    let duration: Double
}

public struct PlaybackError: Codable {
    let code: String
    let message: String
    let timestamp: Double
}

public class QoECollector {
    private let videoId: String
    private let sessionId: String
    private var bufferingEvents: [BufferingEvent] = []
    private var errors: [PlaybackError] = []
    private var startupTime: Int64?
    private var lastBufferingStart: Date?
    private var totalBufferingTime: Double = 0.0
    private var bitrateSwitches: Int = 0
    private var lastBitrate: Int64?
    private var collectingTimer: Timer?
    private let apiBaseURL: String
    
    public init(videoId: String, apiBaseURL: String = "http://localhost:8080/api/v1") {
        self.videoId = videoId
        self.sessionId = "ios-\(Int64(Date().timeIntervalSince1970 * 1000))-\(UUID().uuidString.prefix(8))"
        self.apiBaseURL = apiBaseURL
    }
    
    public func recordStartup(startupTime: Int64) {
        self.startupTime = startupTime
    }
    
    public func recordBufferingStart() {
        if lastBufferingStart == nil {
            lastBufferingStart = Date()
        }
    }
    
    public func recordBufferingEnd() {
        guard let start = lastBufferingStart else { return }
        let end = Date()
        let duration = end.timeIntervalSince(start)
        totalBufferingTime += duration
        
        bufferingEvents.append(BufferingEvent(
            startTime: start.timeIntervalSince1970,
            endTime: end.timeIntervalSince1970,
            duration: duration
        ))
        lastBufferingStart = nil
    }
    
    public func recordError(code: String, message: String) {
        errors.append(PlaybackError(
            code: code,
            message: message,
            timestamp: Date().timeIntervalSince1970
        ))
    }
    
    public func recordBitrateChange(newBitrate: Int64) {
        if let last = lastBitrate, last != newBitrate {
            bitrateSwitches += 1
        }
        lastBitrate = newBitrate
    }
    
    public func startCollecting(player: AVPlayer, interval: TimeInterval = 5.0) {
        collectingTimer = Timer.scheduledTimer(withTimeInterval: interval, repeats: true) { [weak self] _ in
            self?.sendMetrics(player: player)
        }
    }
    
    public func stopCollecting() {
        collectingTimer?.invalidate()
        collectingTimer = nil
    }
    
    private func sendMetrics(player: AVPlayer) {
        let currentTime = player.currentTime().seconds
        let duration = player.currentItem?.duration.seconds ?? 0.0
        let playbackState: String
        if let item = player.currentItem {
            switch item.status {
            case .readyToPlay:
                playbackState = player.rate > 0 ? "playing" : "paused"
            case .failed:
                playbackState = "error"
            default:
                playbackState = "buffering"
            }
        } else {
            playbackState = "idle"
        }
        
        let videoFormat = player.currentItem?.tracks.first(where: { $0.mediaType == .video })
        let currentBitrate = videoFormat?.estimatedDataRate.map { Int64($0) }
        let currentResolution = videoFormat?.naturalSize.map { "\(Int($0.width))x\(Int($0.height))" }
        
        if let bitrate = currentBitrate {
            recordBitrateChange(newBitrate: bitrate)
        }
        
        let payload = QoEMetricPayload(
            platform: "ios",
            videoId: videoId,
            sessionId: sessionId,
            timestamp: ISO8601DateFormatter().string(from: Date()),
            deviceInfo: DeviceInfo(
                deviceType: getDeviceType(),
                os: "iOS \(UIDevice.current.systemVersion)",
                screenResolution: getScreenResolution()
            ),
            metrics: QoEMetrics(
                playbackState: playbackState,
                currentTime: currentTime,
                duration: duration,
                bufferingEvents: bufferingEvents,
                totalBufferingTime: totalBufferingTime,
                startupTime: startupTime,
                currentBitrate: currentBitrate,
                currentResolution: currentResolution,
                bitrateSwitches: bitrateSwitches,
                errors: errors,
                errorCount: errors.count,
                playbackQuality: calculateQuality()
            )
        )
        
        sendToAPI(payload: payload)
    }
    
    private func sendToAPI(payload: QoEMetricPayload) {
        guard let url = URL(string: "\(apiBaseURL)/metrics") else { return }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        do {
            request.httpBody = try JSONEncoder().encode(payload)
        } catch {
            print("Failed to encode payload: \(error)")
            return
        }
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error {
                print("Failed to send metrics: \(error)")
                return
            }
            
            if let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode != 201 {
                print("Failed to send metrics: HTTP \(httpResponse.statusCode)")
            }
        }.resume()
    }
    
    private func getDeviceType() -> String {
        let screenWidth = UIScreen.main.bounds.width
        if screenWidth < 600 {
            return "mobile"
        } else if screenWidth < 1024 {
            return "tablet"
        } else {
            return "tv"
        }
    }
    
    private func getScreenResolution() -> String {
        let bounds = UIScreen.main.bounds
        return "\(Int(bounds.width))x\(Int(bounds.height))"
    }
    
    private func calculateQuality() -> String {
        if totalBufferingTime < 2 && errors.isEmpty {
            return "excellent"
        } else if totalBufferingTime < 5 && errors.count < 2 {
            return "good"
        } else if totalBufferingTime < 10 && errors.count < 5 {
            return "fair"
        } else {
            return "poor"
        }
    }
}

#if canImport(UIKit)
import UIKit
#endif
