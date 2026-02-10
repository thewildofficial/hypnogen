// AudioPlayer.swift
// Hypnogen
//
// Audio playback service for calibration samples using AVFoundation.
// Generates sine-tone test audio procedurally (no bundled assets required)
// and applies gain adjustments to simulate different subliminal levels.

import AVFoundation
import Foundation
import Observation

/// Playback state for the calibration audio player.
enum PlaybackState: Equatable {
    case idle
    case playing
    case error(String)
}

/// Generates and plays calibration test audio at specified gain levels.
@Observable
final class AudioPlayer: NSObject {
    // MARK: - Observable State

    private(set) var playbackState: PlaybackState = .idle

    // MARK: - Audio Constants

    private static let sampleRate: Double = 44100
    private static let durationSeconds: Double = 3.0
    private static let baseFrequency: Double = 220.0
    private static let speechSimFrequencies: [Double] = [220, 330, 440]

    // MARK: - Private State

    private var audioPlayer: AVAudioPlayer?

    // MARK: - Public API

    /// Play a calibration sample at the given gain level (in dB).
    ///
    /// Generates a multi-tone signal (simulating speech frequency range)
    /// with the specified gain applied, to let users judge audibility.
    func playCalibrationSample(gainDb: Double) {
        stop()

        do {
            let audioData = generateCalibrationAudio(gainDb: gainDb)
            let player = try AVAudioPlayer(data: audioData)
            player.delegate = self
            player.prepareToPlay()
            player.play()
            audioPlayer = player
            playbackState = .playing
        } catch {
            playbackState = .error(error.localizedDescription)
        }
    }

    /// Stop any currently playing audio.
    func stop() {
        audioPlayer?.stop()
        audioPlayer = nil
        playbackState = .idle
    }

    // MARK: - Audio Generation

    /// Generate a WAV-format Data containing a multi-tone calibration signal at the given gain.
    private func generateCalibrationAudio(gainDb: Double) -> Data {
        let sampleRate = Self.sampleRate
        let totalSamples = Int(sampleRate * Self.durationSeconds)
        let linearGain = pow(10.0, gainDb / 20.0)

        // Generate multi-tone signal (simulates speech frequency content)
        var samples = [Float](repeating: 0, count: totalSamples)
        let frequencyCount = Float(Self.speechSimFrequencies.count)

        for (sampleIndex, _) in samples.enumerated() {
            let time = Double(sampleIndex) / sampleRate
            var value: Float = 0

            for frequency in Self.speechSimFrequencies {
                value += Float(sin(2.0 * .pi * frequency * time))
            }

            // Normalize by frequency count, apply gain, add fade envelope
            value /= frequencyCount
            value *= Float(linearGain)

            // Apply fade in/out to avoid clicks
            let fadeLength = min(totalSamples / 10, Int(sampleRate * 0.05))
            if sampleIndex < fadeLength {
                value *= Float(sampleIndex) / Float(fadeLength)
            } else if sampleIndex > totalSamples - fadeLength {
                value *= Float(totalSamples - sampleIndex) / Float(fadeLength)
            }

            samples[sampleIndex] = value
        }

        return encodeWAV(samples: samples, sampleRate: Int(sampleRate))
    }

    /// Encode Float samples as a 16-bit PCM WAV file in memory.
    private func encodeWAV(samples: [Float], sampleRate: Int) -> Data {
        let channelCount: Int = 1
        let bitsPerSample: Int = 16
        let bytesPerSample = bitsPerSample / 8
        let dataSize = samples.count * bytesPerSample
        let headerSize = 44

        var data = Data(capacity: headerSize + dataSize)

        // RIFF header
        data.append(contentsOf: "RIFF".utf8)
        data.append(littleEndianUInt32(UInt32(headerSize + dataSize - 8)))
        data.append(contentsOf: "WAVE".utf8)

        // fmt sub-chunk
        data.append(contentsOf: "fmt ".utf8)
        data.append(littleEndianUInt32(16)) // Sub-chunk size
        data.append(littleEndianUInt16(1))  // PCM format
        data.append(littleEndianUInt16(UInt16(channelCount)))
        data.append(littleEndianUInt32(UInt32(sampleRate)))
        data.append(littleEndianUInt32(UInt32(sampleRate * channelCount * bytesPerSample)))
        data.append(littleEndianUInt16(UInt16(channelCount * bytesPerSample)))
        data.append(littleEndianUInt16(UInt16(bitsPerSample)))

        // data sub-chunk
        data.append(contentsOf: "data".utf8)
        data.append(littleEndianUInt32(UInt32(dataSize)))

        // Convert Float samples to Int16 PCM
        for sample in samples {
            let clamped = max(-1.0, min(1.0, sample))
            let int16Value = Int16(clamped * Float(Int16.max))
            data.append(littleEndianInt16(int16Value))
        }

        return data
    }

    // MARK: - Byte Helpers

    private func littleEndianUInt32(_ value: UInt32) -> Data {
        withUnsafeBytes(of: value.littleEndian) { Data($0) }
    }

    private func littleEndianUInt16(_ value: UInt16) -> Data {
        withUnsafeBytes(of: value.littleEndian) { Data($0) }
    }

    private func littleEndianInt16(_ value: Int16) -> Data {
        withUnsafeBytes(of: value.littleEndian) { Data($0) }
    }
}

// MARK: - AVAudioPlayerDelegate

extension AudioPlayer: AVAudioPlayerDelegate {
    func audioPlayerDidFinishPlaying(_ player: AVAudioPlayer, successfully flag: Bool) {
        playbackState = .idle
    }

    func audioPlayerDecodeErrorDidOccur(_ player: AVAudioPlayer, error: Error?) {
        playbackState = .error(error?.localizedDescription ?? "Unknown playback error")
    }
}
