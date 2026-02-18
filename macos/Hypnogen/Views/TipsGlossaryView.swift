// TipsGlossaryView.swift
// Hypnogen
//
// Scrollable cards showing helpful tips and a glossary of Hypnogen terminology.

import SwiftUI

struct TipsGlossaryView: View {
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: Spacing.xl) {
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
            HStack(spacing: Spacing.sm) {
                Image(systemName: "lightbulb.fill")
                    .font(.system(size: 18, weight: .medium))
                    .foregroundStyle(
                        LinearGradient(
                            colors: [Color.accentGlow, Color.accentViolet],
                            startPoint: .top,
                            endPoint: .bottom
                        )
                    )
                    .symbolRenderingMode(.hierarchical)

                Text("Tips")
                    .font(Typography.sectionTitle)
                    .foregroundStyle(Color.textPrimary)
            }

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
                        Color.accentViolet.opacity(0.25),
                        Color.accentIndigo.opacity(0.15),
                        Color.accentViolet.opacity(0),
                    ],
                    startPoint: .leading,
                    endPoint: .trailing
                )
            )
            .frame(height: 1)
            .padding(.horizontal, Spacing.md)
    }

    // MARK: - Glossary

    private var glossarySection: some View {
        VStack(alignment: .leading, spacing: Spacing.md) {
            HStack(spacing: Spacing.sm) {
                Image(systemName: "book.fill")
                    .font(.system(size: 18, weight: .medium))
                    .foregroundStyle(
                        LinearGradient(
                            colors: [Color.accentGlow, Color.accentViolet],
                            startPoint: .top,
                            endPoint: .bottom
                        )
                    )
                    .symbolRenderingMode(.hierarchical)

                Text("Glossary")
                    .font(Typography.sectionTitle)
                    .foregroundStyle(Color.textPrimary)
            }

            VStack(alignment: .leading, spacing: Spacing.xs) {
                ForEach(GlossaryContent.entries) { entry in
                    GlossaryRowView(entry: entry)
                        .accessibilityIdentifier(
                            "\(Constants.Accessibility.Onboarding.glossaryEntry)_\(entry.id)"
                        )
                }
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
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundStyle(Color.accentGlow)
                    .frame(width: 24, height: 24)
                    .background(
                        Circle()
                            .fill(Color.accentViolet.opacity(0.15))
                    )

                Text(tip.title)
                    .font(Typography.bodyBold)
                    .foregroundStyle(Color.textPrimary)
            }

            Text(tip.body)
                .font(Typography.captionText)
                .foregroundStyle(Color.textSecondary)
                .lineSpacing(3)
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
                .font(Typography.captionText)
                .foregroundStyle(Color.textSecondary)
                .lineSpacing(3)
                .padding(.top, Spacing.xs)
        } label: {
            Text(entry.term)
                .font(Typography.bodyBold)
                .foregroundStyle(isExpanded ? Color.textAccent : Color.textPrimary)
        }
        .padding(.vertical, 2)
        .tint(Color.accentViolet)
    }
}
