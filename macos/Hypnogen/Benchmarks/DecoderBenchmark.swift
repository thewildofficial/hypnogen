import Foundation
import CoreML
import Accelerate

/// Microbenchmark for CoreML decoder model inference
/// Compares performance across different compute unit configurations
@available(macOS 14.0, *)
struct DecoderBenchmark {
    
    struct BenchmarkResult: Codable {
        let timestamp: String
        let config: Config
        let machineInfo: MachineInfo
        let runs: [RunResult]
        
        struct Config: Codable {
            let computeUnits: String
            let warmRepeats: Int
        }
        
        struct MachineInfo: Codable {
            let platform: String
            let hardware: String
            let cpu: String
            let memoryGB: Double
        }
        
        struct RunResult: Codable {
            let caseId: String
            let cold: TimingResult
            let warm: WarmResult
        }
        
        struct TimingResult: Codable {
            let wallTimeSec: Double
        }
        
        struct WarmResult: Codable {
            let meanWallTimeSec: Double
            let stdWallTimeSec: Double
            let repeats: Int
        }
    }
    
    let modelURL: URL
    let computeUnits: MLComputeUnits
    let warmRepeats: Int
    
    init(modelURL: URL, computeUnits: MLComputeUnits = .all, warmRepeats: Int = 5) {
        self.modelURL = modelURL
        self.computeUnits = computeUnits
        self.warmRepeats = warmRepeats
    }
    
    /// Run benchmark and return results
    func run() async throws -> BenchmarkResult {
        let config = MLModelConfiguration()
        config.computeUnits = computeUnits
        
        print("Loading model from: \(modelURL.path)")
        print("Compute units: \(computeUnitsString)")
        
        // Cold run - includes model compilation/loading
        let coldStart = CFAbsoluteTimeGetCurrent()
        let model = try await MLModel.load(contentsOf: modelURL, configuration: config)
        let coldEnd = CFAbsoluteTimeGetCurrent()
        let coldTime = coldEnd - coldStart
        
        print("Cold load time: \(String(format: "%.3f", coldTime))s")
        
        // Generate test inputs
        let testInputs = generateTestInputs()
        
        // Warm runs
        var warmTimes: [Double] = []
        for i in 0..<warmRepeats {
            let start = CFAbsoluteTimeGetCurrent()
            _ = try await model.prediction(from: testInputs)
            let end = CFAbsoluteTimeGetCurrent()
            let time = end - start
            warmTimes.append(time)
            print("Warm run \(i+1)/\(warmRepeats): \(String(format: "%.3f", time))s")
        }
        
        let meanTime = warmTimes.reduce(0, +) / Double(warmTimes.count)
        let variance = warmTimes.map { pow($0 - meanTime, 2) }.reduce(0, +) / Double(warmTimes.count)
        let stdTime = sqrt(variance)
        
        let machineInfo = getMachineInfo()
        
        return BenchmarkResult(
            timestamp: ISO8601DateFormatter().string(from: Date()),
            config: .init(
                computeUnits: computeUnitsString,
                warmRepeats: warmRepeats
            ),
            machineInfo: machineInfo,
            runs: [
                .init(
                    caseId: "decoder_inference",
                    cold: .init(wallTimeSec: coldTime),
                    warm: .init(
                        meanWallTimeSec: meanTime,
                        stdWallTimeSec: stdTime,
                        repeats: warmRepeats
                    )
                )
            ]
        )
    }
    
    private var computeUnitsString: String {
        switch computeUnits {
        case .all: return "ALL"
        case .cpuAndGPU: return "CPU_AND_GPU"
        case .cpuOnly: return "CPU_ONLY"
        @unknown default: return "UNKNOWN"
        }
    }
    
    private func getMachineInfo() -> BenchmarkResult.MachineInfo {
        let processInfo = ProcessInfo.processInfo
        
        return .init(
            platform: "macOS \(processInfo.operatingSystemVersionString)",
            hardware: getHardwareModel(),
            cpu: getCPUInfo(),
            memoryGB: Double(processInfo.physicalMemory) / (1024 * 1024 * 1024)
        )
    }
    
    private func getHardwareModel() -> String {
        var size = 0
        sysctlbyname("hw.model", nil, &size, nil, 0)
        var model = [CChar](repeating: 0, count: size)
        sysctlbyname("hw.model", &model, &size, nil, 0)
        return String(cString: model)
    }
    
    private func getCPUInfo() -> String {
        var size = 0
        sysctlbyname("machdep.cpu.brand_string", nil, &size, nil, 0)
        var cpu = [CChar](repeating: 0, count: size)
        sysctlbyname("machdep.cpu.brand_string", &cpu, &size, nil, 0)
        return String(cString: cpu)
    }
    
    /// Generate test inputs matching decoder model expectations
    private func generateTestInputs() -> MLFeatureProvider {
        // Decoder expects: asr (1, 512, frames), f0 (1, frames), n (1, frames), ref_s (1, 256)
        let frames = 100  // Typical frame count for ~5 seconds of audio
        
        let asrShape = [1, 512, frames]
        let f0Shape = [1, frames]
        let nShape = [1, frames]
        let refSShape = [1, 256]
        
        let asrData = generateRandomFloats(count: 1 * 512 * frames)
        let f0Data = generateRandomFloats(count: 1 * frames)
        let nData = generateRandomFloats(count: 1 * frames)
        let refSData = generateRandomFloats(count: 1 * 256)
        
        let asrValue = try! MLMultiArray(shape: asrShape.map { NSNumber(value: $0) }, dataType: .float32)
        let f0Value = try! MLMultiArray(shape: f0Shape.map { NSNumber(value: $0) }, dataType: .float32)
        let nValue = try! MLMultiArray(shape: nShape.map { NSNumber(value: $0) }, dataType: .float32)
        let refSValue = try! MLMultiArray(shape: refSShape.map { NSNumber(value: $0) }, dataType: .float32)
        
        // Fill with random data
        for i in 0..<asrData.count { asrValue[i] = NSNumber(value: asrData[i]) }
        for i in 0..<f0Data.count { f0Value[i] = NSNumber(value: f0Data[i]) }
        for i in 0..<nData.count { nValue[i] = NSNumber(value: nData[i]) }
        for i in 0..<refSData.count { refSValue[i] = NSNumber(value: refSData[i]) }
        
        var inputDict: [String: MLFeatureValue] = [
            "asr": MLFeatureValue(multiArray: asrValue),
            "f0": MLFeatureValue(multiArray: f0Value),
            "n": MLFeatureValue(multiArray: nValue),
            "ref_s": MLFeatureValue(multiArray: refSValue)
        ]
        
        return try! MLDictionaryFeatureProvider(dictionary: inputDict)
    }
    
    private func generateRandomFloats(count: Int) -> [Float] {
        var floats = [Float](repeating: 0, count: count)
        for i in 0..<count {
            floats[i] = Float.random(in: -1...1)
        }
        return floats
    }
}

// MARK: - Command Line Interface

@available(macOS 14.0, *)
@main
struct DecoderBenchmarkCLI {
    static func main() async {
        let arguments = CommandLine.arguments
        
        guard arguments.count >= 2 else {
            print("Usage: DecoderBenchmark <model_path> [--compute-units ALL|CPU_AND_GPU|CPU_ONLY] [--out output.json]")
            exit(1)
        }
        
        let modelPath = arguments[1]
        let modelURL = URL(fileURLWithPath: modelPath)
        
        // Parse arguments
        var computeUnits: MLComputeUnits = .all
        var outputPath: String? = nil
        
        for i in 2..<arguments.count {
            if arguments[i] == "--compute-units" && i + 1 < arguments.count {
                let unitStr = arguments[i + 1]
                switch unitStr.uppercased() {
                case "ALL": computeUnits = .all
                case "CPU_AND_GPU": computeUnits = .cpuAndGPU
                case "CPU_ONLY": computeUnits = .cpuOnly
                default:
                    print("Unknown compute units: \(unitStr)")
                    exit(1)
                }
            }
            if arguments[i] == "--out" && i + 1 < arguments.count {
                outputPath = arguments[i + 1]
            }
        }
        
        do {
            let benchmark = DecoderBenchmark(
                modelURL: modelURL,
                computeUnits: computeUnits,
                warmRepeats: 5
            )
            
            let result = try await benchmark.run()
            
            // Encode to JSON
            let encoder = JSONEncoder()
            encoder.outputFormatting = .prettyPrinted
            let jsonData = try encoder.encode(result)
            
            if let outputPath = outputPath {
                let outputURL = URL(fileURLWithPath: outputPath)
                try jsonData.write(to: outputURL)
                print("\nResults written to: \(outputPath)")
            } else {
                if let jsonString = String(data: jsonData, encoding: .utf8) {
                    print("\n=== Results ===")
                    print(jsonString)
                }
            }
            
        } catch {
            print("Error: \(error)")
            exit(1)
        }
    }
}
