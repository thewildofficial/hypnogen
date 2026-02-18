// WorkerStatusView.swift
// Hypnogen
//
// UI for controlling and monitoring the local worker process.

import SwiftUI

struct WorkerStatusView: View {
    @Bindable var viewModel: WorkerViewModel

    @State private var pulsePhase = false
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    var body: some View {
        VStack(alignment: .leading, spacing: Spacing.md) {
            headerRow
            statusDescription
            detailRows
            actionButtons
        }
        .padding(Spacing.md)
        .background(cardBackground)
        .clipShape(RoundedRectangle(cornerRadius: Radius.md, style: .continuous))
        .overlay(cardBorder)
        .shadow(ShadowTokens.card)
    }

    // MARK: - Header

    private var headerRow: some View {
        HStack(alignment: .center, spacing: Spacing.sm) {
            stateIndicator
            Text(viewModel.stateTitle)
                .font(Typography.bodyBold)
                .foregroundStyle(Color.textPrimary)
            Spacer()
            if viewModel.isBusy {
                ProgressView()
                    .controlSize(.small)
                    .tint(Color.accentGlow)
            }
        }
    }

    // MARK: - State Indicator

    private var stateIndicator: some View {
        ZStack {
            Circle()
                .fill(stateColor.opacity(pulsePhase ? 0.2 : 0.08))
                .frame(width: 28, height: 28)
                .pulseAnimation(reduceMotion: reduceMotion, value: pulsePhase)

            Circle()
                .fill(stateColor)
                .frame(width: 10, height: 10)
                .shadow(color: stateColor.opacity(0.6), radius: 4, x: 0, y: 0)

            Circle()
                .strokeBorder(stateColor.opacity(0.3), lineWidth: 1)
                .frame(width: 20, height: 20)
        }
        .onAppear {
            if viewModel.isBusy {
                pulsePhase = true
            }
        }
        .onChange(of: viewModel.isBusy) { _, busy in
            pulsePhase = busy
        }
    }

    // MARK: - Status Description

    private var statusDescription: some View {
        Text(viewModel.statusDescription)
            .font(Typography.bodySmall)
            .foregroundStyle(Color.textSecondary)
            .lineSpacing(2)
    }

    // MARK: - Detail Rows

    @ViewBuilder
    private var detailRows: some View {
        let hasPort = viewModel.port != nil
        let hasPython = viewModel.pythonExecutablePath != nil

        if hasPort || hasPython {
            VStack(alignment: .leading, spacing: Spacing.sm) {
                if let port = viewModel.port {
                    detailRow(label: "Port", value: String(port), monospaced: true)
                }
                if let pythonPath = viewModel.pythonExecutablePath {
                    detailRow(label: "Python", value: pythonPath, monospaced: false, truncate: true)
                }
            }
            .padding(Spacing.sm + 2)
            .background(
                RoundedRectangle(cornerRadius: Radius.sm, style: .continuous)
                    .fill(Color.backgroundDeep.opacity(0.5))
            )
            .overlay(
                RoundedRectangle(cornerRadius: Radius.sm, style: .continuous)
                    .strokeBorder(Color.surfaceSecondary.opacity(0.25), lineWidth: 0.5)
            )
        }
    }

    private func detailRow(
        label: String,
        value: String,
        monospaced: Bool,
        truncate: Bool = false
    ) -> some View {
        HStack(spacing: Spacing.sm) {
            Text(label.uppercased())
                .font(Typography.label)
                .tracking(Typography.trackingWide)
                .foregroundStyle(Color.textSecondary)
                .frame(width: 52, alignment: .leading)

            if monospaced {
                Text(value)
                    .font(Typography.monospaceSmall)
                    .foregroundStyle(Color.textAccent)
                    .textSelection(.enabled)
            } else {
                Text(value)
                    .font(Typography.captionText)
                    .foregroundStyle(Color.textSecondary)
                    .lineLimit(truncate ? 1 : nil)
                    .truncationMode(.middle)
                    .textSelection(.enabled)
            }
        }
    }

    // MARK: - Action Buttons

    private var actionButtons: some View {
        HStack(spacing: Spacing.sm) {
            if viewModel.canStop {
                Button {
                    viewModel.toggleWorker()
                } label: {
                    ButtonLabel(
                        viewModel.primaryActionTitle,
                        icon: "stop.fill",
                        size: .small
                    )
                }
                .buttonStyle(SecondaryButtonStyle(size: .small))
                .disabled(viewModel.isBusy)
            } else {
                Button {
                    viewModel.toggleWorker()
                } label: {
                    ButtonLabel(
                        viewModel.primaryActionTitle,
                        icon: "play.fill",
                        size: .small
                    )
                }
                .buttonStyle(PrimaryButtonStyle(size: .small))
                .disabled(viewModel.isBusy)
            }

            Button {
                viewModel.restartWorker()
            } label: {
                ButtonLabel("Restart", icon: "arrow.clockwise", size: .small)
            }
            .buttonStyle(SecondaryButtonStyle(size: .small))
            .disabled(viewModel.isBusy)
        }
    }

    // MARK: - Card Background

    private var cardBackground: some View {
        ZStack {
            GradientTokens.cardGradient

            RadialGradient(
                colors: [
                    stateColor.opacity(0.06),
                    Color.clear,
                ],
                center: .topLeading,
                startRadius: 0,
                endRadius: 120
            )
        }
    }

    // MARK: - Card Border

    private var cardBorder: some View {
        RoundedRectangle(cornerRadius: Radius.md, style: .continuous)
            .strokeBorder(
                LinearGradient(
                    colors: [
                        stateColor.opacity(0.3),
                        Color.surfaceSecondary.opacity(0.3),
                    ],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                ),
                lineWidth: 1
            )
    }

    // MARK: - State Color

    private var stateColor: Color {
        switch viewModel.state {
        case .stopped:
            return Color.textSecondary
        case .starting, .warmingUp:
            return Color(red: 0.95, green: 0.65, blue: 0.20) // warm amber
        case .ready:
            return Color(red: 0.30, green: 0.85, blue: 0.55) // bright emerald
        case .error:
            return Color(red: 0.94, green: 0.27, blue: 0.27) // destructive red
        }
    }
}
