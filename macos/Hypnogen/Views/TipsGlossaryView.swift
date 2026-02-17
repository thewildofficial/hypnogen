// TipsGlossaryView.swift
// Hypnogen
//
// Scrollable cards showing helpful tips and a glossary of Hypnogen terminology.

import SwiftUI

struct TipsGlossaryView: View {
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: Spacing.lg) {
                tipsSection
                glossarySeparator
                glossarySection
            }
            .padding(Spacing.lg)
        }
        .scrollContentBackground(.hidden)
        .accessibilityIdentifier(Constants.Accessibility.Onboarding.tipsGlossaryContainer)
    }

    // MARK: - Tips

    private var tipsSection: some View {
        VStack(alignment: .leading, spacing: Spacing.md) {
            Label("Tips", systemImage: "lightbulb.fill")
                .font(.system(size: 18, weight: .semibold))
                .foregroundStyle(Color.textPrimary)

            LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: Spacing.sm) {
                ForEach(TipsContent.tips) { tip in
                    TipCardView(tip: tip)
                        .accessibilityIdentifier(
                            "\(Constants.Accessibility.Onboarding.tipCard)_\(tip.id)"
                        )
                }
            }
        }
    }

    private var glossarySeparator: some View {
        Rectangle()
            .fill(
                LinearGradient(
                    colors: [
                        Color.accentViolet.opacity(0),
                        Color.accentViolet.opacity(0.2),
                        Color.accentViolet.opacity(0),
                    ],
                    startPoint: .leading,
                    endPoint: .trailing
                )
            )
            .frame(height: 1)
    }

    // MARK: - Glossary

    private var glossarySection: some View {
        VStack(alignment: .leading, spacing: Spacing.sm) {
            Label("Glossary", systemImage: "book.fill")
                .font(.system(size: 18, weight: .semibold))
                .foregroundStyle(Color.textPrimary)

            ForEach(GlossaryContent.entries) { entry in
                GlossaryRowView(entry: entry)
                    .accessibilityIdentifier(
                        "\(Constants.Accessibility.Onboarding.glossaryEntry)_\(entry.id)"
                    )
            }
        }
    }
}

// MARK: - Tip Card

struct TipCardView: View {
    let tip: Tip

    var body: some View {
        VStack(alignment: .leading, spacing: Spacing.sm) {
            HStack(spacing: Spacing.sm) {
                Image(systemName: tip.sfSymbol)
                    .font(.system(size: 16, weight: .medium))
                    .foregroundStyle(Color.accentGlow)
                    .frame(width: 24)
                Text(tip.title)
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundStyle(Color.textPrimary)
            }

            Text(tip.body)
                .font(.system(size: 12))
                .foregroundStyle(Color.textSecondary)
                .lineSpacing(2)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .glassCardStyle(elevation: .raised)
    }
}

// MARK: - Glossary Row

struct GlossaryRowView: View {
    let entry: GlossaryEntry

    @State private var isExpanded = false

    var body: some View {
        DisclosureGroup(isExpanded: $isExpanded) {
            Text(entry.definition)
                .font(.system(size: 12))
                .foregroundStyle(Color.textSecondary)
                .lineSpacing(2)
                .padding(.top, Spacing.xs)
        } label: {
            Text(entry.term)
                .font(.system(size: 13, weight: .semibold))
                .foregroundStyle(Color.textPrimary)
        }
        .padding(.vertical, 2)
        .tint(Color.accentViolet)
    }
}
