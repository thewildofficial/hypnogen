// WorkerStatusView.swift
// Hypnogen
//
// UI for controlling and monitoring the local worker process.

import SwiftUI

struct WorkerStatusView: View {
    @Bindable var viewModel: WorkerViewModel

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            HStack(alignment: .center) {
                Label(viewModel.stateTitle, systemImage: stateIconName)
                    .font(.headline)
                    .foregroundStyle(stateColor)

                Spacer()

                if viewModel.isBusy {
                    ProgressView()
                        .controlSize(.small)
                }
            }

            Text(viewModel.statusDescription)
                .font(.callout)
                .foregroundStyle(.secondary)

            Group {
                if let port = viewModel.port {
                    LabeledContent("Port") {
                        Text(String(port))
                            .monospacedDigit()
                            .textSelection(.enabled)
                    }
                }

                if let pythonExecutablePath = viewModel.pythonExecutablePath {
                    LabeledContent("Python") {
                        Text(pythonExecutablePath)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                            .lineLimit(1)
                            .truncationMode(.middle)
                            .textSelection(.enabled)
                    }
                }
            }

            HStack(spacing: 10) {
                if viewModel.canStop {
                    Button(viewModel.primaryActionTitle) {
                        viewModel.toggleWorker()
                    }
                    .buttonStyle(.bordered)
                    .disabled(viewModel.isBusy)
                } else {
                    Button(viewModel.primaryActionTitle) {
                        viewModel.toggleWorker()
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(viewModel.isBusy)
                }

                Button("Restart") {
                    viewModel.restartWorker()
                }
                .buttonStyle(.bordered)
                .disabled(viewModel.isBusy)
            }
        }
        .padding(14)
        .background(
            RoundedRectangle(cornerRadius: 10, style: .continuous)
                .fill(.background)
        )
        .overlay(
            RoundedRectangle(cornerRadius: 10, style: .continuous)
                .stroke(.quaternary)
        )
    }

    private var stateIconName: String {
        switch viewModel.state {
        case .stopped:
            return "stop.circle"
        case .starting, .warmingUp:
            return "clock.arrow.circlepath"
        case .ready:
            return "checkmark.circle.fill"
        case .error:
            return "exclamationmark.triangle.fill"
        }
    }

    private var stateColor: Color {
        switch viewModel.state {
        case .stopped:
            return .secondary
        case .starting, .warmingUp:
            return .orange
        case .ready:
            return .green
        case .error:
            return .red
        }
    }
}
