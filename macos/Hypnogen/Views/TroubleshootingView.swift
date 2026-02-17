// TroubleshootingView.swift
// Hypnogen
//
// Common issues and solutions, presented as expandable cards.

import SwiftUI

struct TroubleshootingView: View {
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: Spacing.md) {
                header
                ForEach(TroubleshootingContent.entries) { entry in
                    TroubleshootingCardView(entry: entry)
                        .accessibilityIdentifier(
                            "\(Constants.Accessibility.Onboarding.troubleshootingEntry)_\(entry.id)"
                        )
                }
            }
            .padding(Spacing.lg)
        }
        .scrollContentBackground(.hidden)
        .accessibilityIdentifier(Constants.Accessibility.Onboarding.troubleshootingContainer)
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: Spacing.xs) {
            Label("Troubleshooting", systemImage: "wrench.and.screwdriver.fill")
                .font(.system(size: 18, weight: .semibold))
                .foregroundStyle(Color.textPrimary)

            Text("Common issues and how to fix them.")
                .font(.system(size: 13))
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
            VStack(alignment: .leading, spacing: Spacing.sm) {
                causeRow
                solutionRow
            }
            .padding(.top, Spacing.sm)
        } label: {
            HStack(spacing: Spacing.sm) {
                Image(systemName: entry.sfSymbol)
                    .font(.system(size: 16, weight: .medium))
                    .foregroundStyle(Color.orange)
                    .frame(width: 24)
                Text(entry.problem)
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundStyle(Color.textPrimary)
            }
        }
        .tint(Color.accentViolet)
        .glassCardStyle(elevation: .raised)
    }

    private var causeRow: some View {
        HStack(alignment: .top, spacing: Spacing.sm) {
            Text("Why:")
                .font(.system(size: 12, weight: .medium))
                .foregroundStyle(Color.textAccent)
                .frame(width: 44, alignment: .leading)
            Text(entry.cause)
                .font(.system(size: 12))
                .foregroundStyle(Color.textSecondary)
        }
    }

    private var solutionRow: some View {
        HStack(alignment: .top, spacing: Spacing.sm) {
            Text("Fix:")
                .font(.system(size: 12, weight: .medium))
                .foregroundStyle(Color.textAccent)
                .frame(width: 44, alignment: .leading)
            Text(entry.solution)
                .font(.system(size: 12))
                .foregroundStyle(Color.textSecondary)
                .lineSpacing(2)
        }
    }
}
