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
        
        let compiledURL: URL
        if modelURL.pathExtension == "mlpackage" || modelURL.pathExtension == "mlmodel" {
            print("Compiling model...")
            compiledURL = try await MLModel.compileModel(at: modelURL)
        } else {
            compiledURL = modelURL
        }
        
        let model = try await MLModel.load(contentsOf: compiledURL, configuration: config)
        let coldEnd = CFAbsoluteTimeGetCurrent()
        let coldTime = coldEnd - coldStart
        
        print("Cold load time (including compilation if needed): \(String(format: "%.3f", coldTime))s")
        
        print("Model inputs: \(model.modelDescription.inputDescriptionsByName.keys.joined(separator: ", "))")
        
        // Generate test inputs
        let testInputs = generateTestInputs(for: model.modelDescription)
        
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
        case .cpuAndNeuralEngine: return "CPU_AND_NEURAL_ENGINE"
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
    private func generateTestInputs(for description: MLModelDescription) -> MLFeatureProvider {
        var inputDict: [String: MLFeatureValue] = [:]
        
        for (name, inputDesc) in description.inputDescriptionsByName {
            if let multiArrayConstraint = inputDesc.multiArrayConstraint {
                let shape = multiArrayConstraint.shape.map { $0.intValue }
                // Handle flexible shapes if necessary, but for benchmark we just use the default or a fixed size
                // If shape has 0 or -1, we need to pick a size.
                let actualShape = shape.map { $0 <= 0 ? 100 : $0 }
                
                let count = actualShape.reduce(1, *)
                let data = generateRandomFloats(count: count)
                
                let multiArray = try! MLMultiArray(shape: actualShape.map { NSNumber(value: $0) }, dataType: .float32)
                for i in 0..<data.count {
                    multiArray[i] = NSNumber(value: data[i])
                }
                inputDict[name] = MLFeatureValue(multiArray: multiArray)
            }
        }
        
        return try! MLDictionaryFeatureProvider(dictionary: inputDict)
    }
    
    private func generateRandomFloats(count: Int) -> [Float] {
        var floats = [Float](repeating: 0, count: count)
        // Use a simple deterministic LCG with a fixed seed
        var state: UInt32 = 42
        for i in 0..<count {
            state = 1103515245 &* state &+ 12345
            state &= 0x7fffffff
            floats[i] = (Float(state) / Float(0x7fffffff)) * 2.0 - 1.0
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
            print("Usage: DecoderBenchmark <model_path> [--compute-units ALL|CPU_AND_GPU|CPU_ONLY|CPU_AND_NEURAL_ENGINE] [--out output.json]")
            exit(1)
        }
        
        let modelPath = arguments[1]
        let modelURL = URL(fileURLWithPath: modelPath)
        
        // Parse arguments
        var computeUnits: MLComputeUnits = .all
        var outputPath: String? = nil
        
        var i = 2
        while i < arguments.count {
            if arguments[i] == "--compute-units" && i + 1 < arguments.count {
                let unitStr = arguments[i + 1]
                switch unitStr.uppercased() {
                case "ALL": computeUnits = .all
                case "CPU_AND_GPU": computeUnits = .cpuAndGPU
                case "CPU_ONLY": computeUnits = .cpuOnly
                case "CPU_AND_NEURAL_ENGINE": computeUnits = .cpuAndNeuralEngine
                default:
                    print("Unknown compute units: \(unitStr)")
                    exit(1)
                }
                i += 2
            } else if arguments[i] == "--out" && i + 1 < arguments.count {
                outputPath = arguments[i + 1]
                i += 2
            } else {
                i += 1
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
