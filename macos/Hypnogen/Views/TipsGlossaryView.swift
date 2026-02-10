// TipsGlossaryView.swift
// Hypnogen
//
// Scrollable cards showing helpful tips and a glossary of Hypnogen terminology.

import SwiftUI

struct TipsGlossaryView: View {
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 24) {
                tipsSection
                Divider()
                glossarySection
            }
            .padding(24)
        }
        .accessibilityIdentifier(Constants.Accessibility.Onboarding.tipsGlossaryContainer)
    }

    // MARK: - Tips

    private var tipsSection: some View {
        VStack(alignment: .leading, spacing: 16) {
            Label("Tips", systemImage: "lightbulb.fill")
                .font(.title2)
                .fontWeight(.semibold)

            LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 12) {
                ForEach(TipsContent.tips) { tip in
                    TipCardView(tip: tip)
                        .accessibilityIdentifier(
                            "\(Constants.Accessibility.Onboarding.tipCard)_\(tip.id)"
                        )
                }
            }
        }
    }

    // MARK: - Glossary

    private var glossarySection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Label("Glossary", systemImage: "book.fill")
                .font(.title2)
                .fontWeight(.semibold)

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
        VStack(alignment: .leading, spacing: 8) {
            HStack(spacing: 8) {
                Image(systemName: tip.sfSymbol)
                    .font(.title3)
                    .foregroundStyle(.accent)
                    .frame(width: 24)
                Text(tip.title)
                    .font(.headline)
            }

            Text(tip.body)
                .font(.callout)
                .foregroundStyle(.secondary)
                .lineSpacing(2)
        }
        .padding(12)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(.quaternary.opacity(0.5))
        .clipShape(RoundedRectangle(cornerRadius: 8))
    }
}

// MARK: - Glossary Row

struct GlossaryRowView: View {
    let entry: GlossaryEntry

    @State private var isExpanded = false

    var body: some View {
        DisclosureGroup(isExpanded: $isExpanded) {
            Text(entry.definition)
                .font(.callout)
                .foregroundStyle(.secondary)
                .lineSpacing(2)
                .padding(.top, 4)
        } label: {
            Text(entry.term)
                .font(.headline)
        }
        .padding(.vertical, 2)
    }
}
