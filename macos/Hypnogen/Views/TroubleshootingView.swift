// TroubleshootingView.swift
// Hypnogen
//
// Common issues and solutions, presented as expandable cards.

import SwiftUI

struct TroubleshootingView: View {
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                header
                ForEach(TroubleshootingContent.entries) { entry in
                    TroubleshootingCardView(entry: entry)
                        .accessibilityIdentifier(
                            "\(Constants.Accessibility.Onboarding.troubleshootingEntry)_\(entry.id)"
                        )
                }
            }
            .padding(24)
        }
        .background(Color.canvas)
        .accessibilityIdentifier(Constants.Accessibility.Onboarding.troubleshootingContainer)
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: 4) {
            Label("Troubleshooting", systemImage: "wrench.and.screwdriver.fill")
                .font(.title2)
                .fontWeight(.semibold)

            Text("Common issues and how to fix them.")
                .font(.subheadline)
                .foregroundStyle(Color.textSecondary)
        }
    }
}

// MARK: - Troubleshooting Card

struct TroubleshootingCardView: View {
    let entry: TroubleshootingEntry

    @State private var isExpanded = false

    var body: some View {
        DisclosureGroup(isExpanded: $isExpanded) {
            VStack(alignment: .leading, spacing: 12) {
                causeRow
                solutionRow
            }
            .padding(.top, 8)
        } label: {
            HStack(spacing: 10) {
                Image(systemName: entry.sfSymbol)
                    .font(.title3)
                    .foregroundStyle(Color.orange)
                    .frame(width: 24)
                Text(entry.problem)
                    .font(.headline)
            }
        }
        .padding(12)
        .background(Color.surface.opacity(0.3))
        .clipShape(RoundedRectangle(cornerRadius: 8))
    }

    private var causeRow: some View {
        HStack(alignment: .top, spacing: 8) {
            Text("Why:")
                .font(.callout)
                .fontWeight(.medium)
                .frame(width: 44, alignment: .leading)
            Text(entry.cause)
                .font(.callout)
                .foregroundStyle(Color.textSecondary)
        }
    }

    private var solutionRow: some View {
        HStack(alignment: .top, spacing: 8) {
            Text("Fix:")
                .font(.callout)
                .fontWeight(.medium)
                .frame(width: 44, alignment: .leading)
            Text(entry.solution)
                .font(.callout)
                .foregroundStyle(Color.textSecondary)
                .lineSpacing(2)
        }
    }
}
