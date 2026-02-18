import SwiftUI

// MARK: - Typography Tokens

/// Typography system using SF Pro (system font) per macOS HIG.
///
/// Design principles:
/// - Weight contrast creates visual hierarchy (light display ↔ medium body)
/// - Tracking scales inversely with size for optical balance
/// - Line heights tuned per role: tight for display, relaxed for reading
/// - All styles use `Font.system()` to respect user accessibility settings
enum Typography {
    // MARK: Display

    /// Large display text for hero sections — light weight creates elegance at scale (44pt)
    static let heroTitle: Font = .system(size: 44, weight: .light, design: .default)

    /// Page-level headers — medium weight balances authority with refinement (26pt)
    static let pageTitle: Font = .system(size: 26, weight: .medium, design: .default)

    /// Section headers within a page — semibold for clear structure (18pt)
    static let sectionTitle: Font = .system(size: 18, weight: .semibold, design: .default)

    // MARK: Body

    /// Subtitle / lead text bridging headings and body — medium weight distinction (15pt)
    static let subtitle: Font = .system(size: 15, weight: .medium, design: .default)

    /// Standard body copy (14pt, regular)
    static let bodyText: Font = .system(size: 14, weight: .regular, design: .default)

    /// Bold body variant for emphasis (14pt, semibold)
    static let bodyBold: Font = .system(size: 14, weight: .semibold, design: .default)

    /// Small body for secondary content (13pt, regular)
    static let bodySmall: Font = .system(size: 13, weight: .regular, design: .default)

    // MARK: Caption & Labels

    /// Caption text for metadata and descriptions (12pt, regular)
    static let captionText: Font = .system(size: 12, weight: .regular, design: .default)

    /// Small uppercase-style labels — medium weight for crispness at small sizes (11pt)
    static let label: Font = .system(size: 11, weight: .medium, design: .default)

    // MARK: Monospace

    /// Monospaced text for code and script content (14pt, regular, monospaced)
    static let monospaceText: Font = .system(size: 14, weight: .regular, design: .monospaced)

    /// Small monospaced text for inline code (12pt, regular, monospaced)
    static let monospaceSmall: Font = .system(size: 12, weight: .regular, design: .monospaced)
}

// MARK: - Line Height Multipliers

extension Typography {
    /// Tight line height for display headings — keeps large text compact (1.15×)
    static let lineHeightTight: CGFloat = 1.15

    /// Default line height for UI text and short labels (1.4×)
    static let lineHeightNormal: CGFloat = 1.4

    /// Comfortable line height for body paragraphs (1.55×)
    static let lineHeightRelaxed: CGFloat = 1.55

    /// Generous line height for extended reading blocks (1.7×)
    static let lineHeightLoose: CGFloat = 1.7
}

// MARK: - Tracking (Letter Spacing)

extension Typography {
    /// Tight tracking for large display text — optically corrects wide spacing at scale (-1.0pt)
    static let trackingTight: CGFloat = -1.0

    /// Slightly tight tracking for page titles (-0.4pt)
    static let trackingSnug: CGFloat = -0.4

    /// Normal tracking for body text (0pt)
    static let trackingNormal: CGFloat = 0

    /// Wide tracking for small labels and captions — aids legibility at tiny sizes (0.4pt)
    static let trackingWide: CGFloat = 0.4

    /// Extra-wide tracking for uppercase labels and overlines (1.2pt)
    static let trackingExtraWide: CGFloat = 1.2
}

// MARK: - View Extensions

extension View {
    /// Apply hero title styling — light weight, tight tracking, compact line height
    func heroTitle() -> some View {
        self
            .font(Typography.heroTitle)
            .tracking(Typography.trackingTight)
            .lineSpacing(44 * (Typography.lineHeightTight - 1))
    }

    /// Apply page title styling — medium weight, snug tracking
    func pageTitle() -> some View {
        self
            .font(Typography.pageTitle)
            .tracking(Typography.trackingSnug)
            .lineSpacing(26 * (Typography.lineHeightTight - 1))
    }

    /// Apply section title styling — semibold, normal tracking
    func sectionTitle() -> some View {
        self
            .font(Typography.sectionTitle)
            .tracking(Typography.trackingNormal)
            .lineSpacing(18 * (Typography.lineHeightNormal - 1))
    }

    /// Apply subtitle styling — medium weight bridge between headings and body
    func subtitle() -> some View {
        self
            .font(Typography.subtitle)
            .tracking(Typography.trackingNormal)
            .lineSpacing(15 * (Typography.lineHeightNormal - 1))
    }

    /// Apply body text styling — regular weight, relaxed line height for readability
    func bodyText() -> some View {
        self
            .font(Typography.bodyText)
            .tracking(Typography.trackingNormal)
            .lineSpacing(14 * (Typography.lineHeightRelaxed - 1))
    }

    /// Apply bold body styling — semibold for emphasis within body text
    func bodyBold() -> some View {
        self
            .font(Typography.bodyBold)
            .tracking(Typography.trackingNormal)
            .lineSpacing(14 * (Typography.lineHeightRelaxed - 1))
    }

    /// Apply small body styling — secondary content
    func bodySmall() -> some View {
        self
            .font(Typography.bodySmall)
            .tracking(Typography.trackingNormal)
            .lineSpacing(13 * (Typography.lineHeightRelaxed - 1))
    }

    /// Apply caption text styling — wide tracking for small-size legibility
    func captionText() -> some View {
        self
            .font(Typography.captionText)
            .tracking(Typography.trackingWide)
            .lineSpacing(12 * (Typography.lineHeightNormal - 1))
    }

    /// Apply label styling — uppercase-friendly, wide tracking
    func labelText() -> some View {
        self
            .font(Typography.label)
            .tracking(Typography.trackingWide)
    }

    /// Apply monospace text styling — code and script content
    func monospaceText() -> some View {
        self
            .font(Typography.monospaceText)
            .tracking(Typography.trackingNormal)
            .lineSpacing(14 * (Typography.lineHeightRelaxed - 1))
    }

    /// Apply small monospace styling — inline code snippets
    func monospaceSmall() -> some View {
        self
            .font(Typography.monospaceSmall)
            .tracking(Typography.trackingNormal)
            .lineSpacing(12 * (Typography.lineHeightNormal - 1))
    }
}
