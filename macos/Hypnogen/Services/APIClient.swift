// APIClient.swift
// Hypnogen
//
// HTTP client for the Hypnogen FastAPI render worker.
// Uses async/await and URLSession for all network calls.

import Foundation

/// Errors from the API client.
enum APIClientError: LocalizedError {
    case invalidURL
    case serverUnreachable
    case unexpectedStatusCode(Int)
    case decodingFailed(Error)
    case encodingFailed(Error)

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid API URL configuration."
        case .serverUnreachable:
            return "Cannot reach the render worker. Is it running?"
        case .unexpectedStatusCode(let code):
            return "Unexpected HTTP status code: \(code)."
        case .decodingFailed(let error):
            return "Failed to decode server response: \(error.localizedDescription)"
        case .encodingFailed(let error):
            return "Failed to encode request: \(error.localizedDescription)"
        }
    }
}

// MARK: - API Response Types (Decodable mirrors of Python Pydantic models)

struct APIRenderJobStatus: Decodable {
    let jobId: String
    let status: String
    let stage: String?
    let progress: Double
    let etaSec: Int?
    let error: String?

    enum CodingKeys: String, CodingKey {
        case jobId = "job_id"
        case status
        case stage
        case progress
        case etaSec = "eta_sec"
        case error
    }
}

struct APIRenderJobArtifacts: Decodable {
    let jobId: String
    let mixWavUrl: String
    let stems: [String: String]
    let metadataUrl: String
    let createdAt: String

    enum CodingKeys: String, CodingKey {
        case jobId = "job_id"
        case mixWavUrl = "mix_wav_url"
        case stems
        case metadataUrl = "metadata_url"
        case createdAt = "created_at"
    }
}

struct APIHealthResponse: Decodable {
    let status: String
}

// MARK: - Request Types

struct APIRenderJobSubmit: Encodable {
    let script: String
    let affirmations: [String]
    let voice: String
    let swarmVoice: String?
    let seed: Int?
    let lengthSec: Int?
    let exportStems: Bool
    let gainDb: [String: Double]?

    enum CodingKeys: String, CodingKey {
        case script, affirmations, voice
        case swarmVoice = "swarm_voice"
        case seed
        case lengthSec = "length_sec"
        case exportStems = "export_stems"
        case gainDb = "gain_db"
    }
}

// MARK: - API Client

/// Client for the Hypnogen render worker HTTP API.
final class APIClient {
    let baseURL: URL
    private let session: URLSession

    init(baseURL: URL = Constants.API.baseURL) {
        self.baseURL = baseURL

        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 30
        config.timeoutIntervalForResource = 300
        self.session = URLSession(configuration: config)
    }

    private var decoder: JSONDecoder { JSONDecoder() }
    private var encoder: JSONEncoder { JSONEncoder() }

    // MARK: - Health

    /// Check if the render worker is reachable.
    func checkHealth() async throws -> Bool {
        let url = baseURL.appendingPathComponent(Constants.API.healthPath)
        let (data, response) = try await session.data(from: url)
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            return false
        }
        let health = try decoder.decode(APIHealthResponse.self, from: data)
        return health.status == "ok"
    }

    // MARK: - Render Jobs

    /// Submit a new render job. Returns the initial job status.
    func submitRenderJob(_ request: APIRenderJobSubmit) async throws -> APIRenderJobStatus {
        let url = baseURL.appendingPathComponent(Constants.API.renderJobsPath)
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "POST"
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")

        do {
            urlRequest.httpBody = try encoder.encode(request)
        } catch {
            throw APIClientError.encodingFailed(error)
        }

        let (data, response) = try await session.data(for: urlRequest)
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIClientError.serverUnreachable
        }

        guard httpResponse.statusCode == 202 else {
            throw APIClientError.unexpectedStatusCode(httpResponse.statusCode)
        }

        do {
            return try decoder.decode(APIRenderJobStatus.self, from: data)
        } catch {
            throw APIClientError.decodingFailed(error)
        }
    }

    /// Poll the status of a render job.
    func getRenderJobStatus(jobId: String) async throws -> APIRenderJobStatus {
        let url = baseURL
            .appendingPathComponent(Constants.API.renderJobsPath)
            .appendingPathComponent(jobId)

        let (data, response) = try await session.data(from: url)
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIClientError.serverUnreachable
        }

        guard httpResponse.statusCode == 200 else {
            throw APIClientError.unexpectedStatusCode(httpResponse.statusCode)
        }

        do {
            return try decoder.decode(APIRenderJobStatus.self, from: data)
        } catch {
            throw APIClientError.decodingFailed(error)
        }
    }

    /// Get artifacts for a completed render job.
    func getRenderJobArtifacts(jobId: String) async throws -> APIRenderJobArtifacts {
        let url = baseURL
            .appendingPathComponent(Constants.API.renderJobsPath)
            .appendingPathComponent(jobId)
            .appendingPathComponent("artifacts")

        let (data, response) = try await session.data(from: url)
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIClientError.serverUnreachable
        }

        guard httpResponse.statusCode == 200 else {
            throw APIClientError.unexpectedStatusCode(httpResponse.statusCode)
        }

        do {
            return try decoder.decode(APIRenderJobArtifacts.self, from: data)
        } catch {
            throw APIClientError.decodingFailed(error)
        }
    }

    /// Cancel a render job.
    func cancelRenderJob(jobId: String) async throws {
        let url = baseURL
            .appendingPathComponent(Constants.API.renderJobsPath)
            .appendingPathComponent(jobId)

        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "DELETE"

        let (_, response) = try await session.data(for: urlRequest)
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIClientError.serverUnreachable
        }

        guard httpResponse.statusCode == 200 else {
            throw APIClientError.unexpectedStatusCode(httpResponse.statusCode)
        }
    }
}
